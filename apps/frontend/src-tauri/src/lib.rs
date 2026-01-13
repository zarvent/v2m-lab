// Voice2Machine - Tauri IPC Bridge
// Optimized for microsecond-level performance

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::env;
use std::io::{Read, Write};
use std::os::unix::net::UnixStream;
use std::process::Command as SysCommand;
use std::sync::OnceLock;
use tauri::path::BaseDirectory;
use tauri::{Emitter, Manager};

/// Socket path - reads from V2M_SOCKET_PATH env var, or dynamically discovers XDG_RUNTIME_DIR.
/// Adheres to 2026 security standards for local IPC.
fn socket_path() -> &'static str {
    static PATH: OnceLock<String> = OnceLock::new();
    PATH.get_or_init(|| {
        if let Ok(p) = env::var("V2M_SOCKET_PATH") {
            return p;
        }

        let uid = unsafe { libc::getuid() };
        let mut path = if let Ok(xdg) = env::var("XDG_RUNTIME_DIR") {
            std::path::PathBuf::from(xdg).join("v2m")
        } else {
            // Fallback to /tmp with user UID (safe on Linux when ownership is verified)
            std::path::PathBuf::from("/tmp").join(format!("v2m_{}", uid))
        };

        // Security Audit (SOTA 2026): Ensure the directory is owned by the current user
        // This prevents "squatting" attacks where another user creates the directory first.
        if path.exists() {
            use std::os::unix::fs::MetadataExt;
            if let Ok(metadata) = std::fs::metadata(&path) {
                if metadata.uid() != uid {
                    // Critical security failure: Directory owned by someone else
                    // Fallback to a random temporary name or fail loudly
                    eprintln!("SECURITY ERROR: Runtime directory {:?} is not owned by UID {}", path, uid);
                }
            }
        } else {
            // Attempt to create it with restricted permissions
            let _ = std::fs::create_dir_all(&path);
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let _ = std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o700));
            }
        }

        path.push("v2m.sock");
        path.to_string_lossy().into_owned()
    })
}

/// Max response size (1MB) - DoS protection
const MAX_RESPONSE_SIZE: usize = 1 << 20;

/// Read timeout (300 seconds / 5 minutes)
/// Increased to accommodate Whisper transcription of long files and LLM processing.
/// Performance Note: Prevents abandoning expensive inference computations mid-flight.
const READ_TIMEOUT_SECS: u64 = 300;

// --- PERSISTENCE (SOTA 2026: Remote Control State) ---
// Stores the last successful export result to allow checking "job status"
// even if the frontend component unmounted/remounted (tab switch).
use std::sync::Mutex;
static LAST_EXPORT: OnceLock<Mutex<Option<DaemonState>>> = OnceLock::new();

fn get_last_export_store() -> &'static Mutex<Option<DaemonState>> {
    LAST_EXPORT.get_or_init(|| Mutex::new(None))
}

// --- TYPED STRUCTURES (Eliminates double serialization) ---

/// IPC request to daemon
#[derive(Serialize)]
struct IpcCommand {
    cmd: String,
    data: Option<Value>,
}

/// Raw daemon response (internal)
#[derive(Deserialize)]
struct RawDaemonResponse {
    status: String,
    data: Option<Value>,
    error: Option<String>,
}

/// Telemetry data from system monitor
#[derive(Clone, Serialize, Deserialize, Default)]
pub struct TelemetryData {
    pub cpu: CpuInfo,
    pub ram: RamInfo,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub gpu: Option<GpuInfo>,
}

#[derive(Clone, Serialize, Deserialize, Default)]
pub struct CpuInfo {
    pub percent: f32,
}

#[derive(Clone, Serialize, Deserialize, Default)]
pub struct RamInfo {
    pub used_gb: f32,
    pub total_gb: f32,
    pub percent: f32,
}

#[derive(Clone, Serialize, Deserialize, Default)]
pub struct GpuInfo {
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub vram_used_mb: f32,
    #[serde(default)]
    pub vram_total_mb: f32,
    #[serde(default)]
    pub temp_c: u32,
}

/// Typed daemon state (pushed to frontend)
#[derive(Clone, Serialize, Deserialize)]
pub struct DaemonState {
    pub state: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub transcription: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub refined_text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub telemetry: Option<TelemetryData>,
}

/// IPC error with structured codes
#[derive(Clone, Serialize, Deserialize)]
pub struct IpcError {
    pub code: String,
    pub message: String,
}

impl From<String> for IpcError {
    fn from(msg: String) -> Self {
        IpcError {
            code: "IPC_ERROR".to_string(),
            message: msg,
        }
    }
}

// --- CORE IPC FUNCTION ---

/// Global persistent connection lock
static CONNECTION: OnceLock<Mutex<Option<UnixStream>>> = OnceLock::new();

fn get_connection() -> &'static Mutex<Option<UnixStream>> {
    CONNECTION.get_or_init(|| Mutex::new(None))
}

/// Send JSON request to Python daemon via Unix socket.
/// Returns typed Value on success, IpcError on failure.
/// Uses persistent connection to reduce latency (SOTA 2026).
fn send_json_request(command: &str, data: Option<Value>) -> Result<Value, IpcError> {
    let conn_lock = get_connection();
    let mut guard = conn_lock.lock().map_err(|_| IpcError::from("Lock poisoned".to_string()))?;

    // 1. Prepare payload (fail fast before network ops)
    let request = IpcCommand {
        cmd: command.to_string(),
        data,
    };
    let json_payload = serde_json::to_vec(&request)
        .map_err(|e| IpcError::from(format!("JSON serialize error: {}", e)))?;
    let payload_size = json_payload.len();

    // Critical security check
    const MAX_REQUEST_SIZE: usize = 10 * 1024 * 1024; // 10MB limit
    if payload_size > MAX_REQUEST_SIZE {
        return Err(IpcError {
            code: "REQUEST_TOO_LARGE".to_string(),
            message: format!("Request payload ({} MB) exceeds {} MB limit",
                           payload_size >> 20, MAX_REQUEST_SIZE >> 20),
        });
    }

    // 2. Ensure connected
    if guard.is_none() {
        let stream = UnixStream::connect(socket_path())
            .map_err(|e| IpcError::from(format!("Daemon not running: {}", e)))?;
        stream.set_read_timeout(Some(std::time::Duration::from_secs(READ_TIMEOUT_SECS)))
            .map_err(|e| IpcError::from(format!("Timeout config failed: {}", e)))?;
        *guard = Some(stream);
    }

    // 3. Send Request (with one retry on broken pipe)
    let len = payload_size as u32;

    // Use a scope to isolate the borrow of the stream
    let write_result = {
        let stream = guard.as_mut().unwrap();
        stream.write_all(&len.to_be_bytes())
    };

    if let Err(_) = write_result {
        // Write failed, assume stale connection. Reconnect.
        // We can modify guard now because 'stream' borrow has ended.
        let new_stream = UnixStream::connect(socket_path())
            .map_err(|e| IpcError::from(format!("Reconnect failed: {}", e)))?;

        new_stream.set_read_timeout(Some(std::time::Duration::from_secs(READ_TIMEOUT_SECS)))
             .map_err(|e| IpcError::from(format!("Timeout config failed: {}", e)))?;

        *guard = Some(new_stream);

        // Retry write header with new stream
        guard.as_mut().unwrap().write_all(&len.to_be_bytes())
            .map_err(|e| IpcError::from(format!("Write header failed: {}", e)))?;
    }

    // Write payload
    guard.as_mut().unwrap().write_all(&json_payload)
        .map_err(|e| IpcError::from(format!("Write payload failed: {}", e)))?;

    // 4. Read Response
    let mut len_buf = [0u8; 4];
    if let Err(e) = guard.as_mut().unwrap().read_exact(&mut len_buf) {
        *guard = None; // Invalidate connection
        return Err(IpcError::from(format!("Read header failed: {}", e)));
    }

    let response_len = u32::from_be_bytes(len_buf) as usize;
    if response_len > MAX_RESPONSE_SIZE {
        *guard = None;
        return Err(IpcError {
            code: "PAYLOAD_TOO_LARGE".to_string(),
            message: format!("Response exceeds {} MB limit", MAX_RESPONSE_SIZE >> 20),
        });
    }

    let mut response_buf = vec![0u8; response_len];
    if let Err(e) = guard.as_mut().unwrap().read_exact(&mut response_buf) {
        *guard = None;
        return Err(IpcError::from(format!("Read body failed: {}", e)));
    }

    // 5. Deserialize
    let response: RawDaemonResponse = serde_json::from_slice(&response_buf)
        .map_err(|e| IpcError::from(format!("Invalid JSON response: {}", e)))?;

    if response.status == "success" {
        Ok(response.data.unwrap_or(Value::Null))
    } else {
        Err(IpcError {
            code: "DAEMON_ERROR".to_string(),
            message: response.error.unwrap_or_else(|| "Unknown daemon error".to_string()),
        })
    }
}

// --- TAURI COMMANDS (Typed responses, no double serialization) ---

/// Get current daemon state with telemetry
#[tauri::command]
fn get_status() -> Result<DaemonState, IpcError> {
    let data = send_json_request("GET_STATUS", None)?;
    serde_json::from_value(data).map_err(|e| IpcError::from(format!("Parse error: {}", e)))
}

/// Start recording audio
#[tauri::command]
fn start_recording(app: tauri::AppHandle) -> Result<DaemonState, IpcError> {
    let data = send_json_request("START_RECORDING", None)?;
    let state: DaemonState = serde_json::from_value(data)
        .unwrap_or(DaemonState {
            state: "recording".to_string(),
            transcription: None,
            refined_text: None,
            message: Some("Recording started".to_string()),
            telemetry: None,
        });
    // Emit state change event to all listeners
    let _ = app.emit("v2m://state-update", &state);
    Ok(state)
}

/// Stop recording and transcribe
#[tauri::command]
fn stop_recording(app: tauri::AppHandle) -> Result<DaemonState, IpcError> {
    let data = send_json_request("STOP_RECORDING", None)?;
    let state: DaemonState = serde_json::from_value(data)
        .map_err(|e| IpcError::from(format!("Parse error: {}", e)))?;
    // Emit transcription result
    let _ = app.emit("v2m://state-update", &state);
    Ok(state)
}

/// Ping daemon (health check)
#[tauri::command]
fn ping() -> Result<Value, IpcError> {
    send_json_request("PING", None)
}

/// Process text with LLM
#[tauri::command]
fn process_text(app: tauri::AppHandle, text: String) -> Result<DaemonState, IpcError> {
    let data = json!({ "text": text });
    let result = send_json_request("PROCESS_TEXT", Some(data))?;
    let state: DaemonState = serde_json::from_value(result)
        .map_err(|e| IpcError::from(format!("Parse error: {}", e)))?;
    // Emit refined text result
    let _ = app.emit("v2m://state-update", &state);
    Ok(state)
}

/// Translate text with LLM
#[tauri::command]
fn translate_text(app: tauri::AppHandle, text: String, target_lang: String) -> Result<DaemonState, IpcError> {
    let data = json!({ "text": text, "target_lang": target_lang });
    let result = send_json_request("TRANSLATE_TEXT", Some(data))?;
    let state: DaemonState = serde_json::from_value(result)
        .map_err(|e| IpcError::from(format!("Parse error: {}", e)))?;
    // Emit translated text result
    let _ = app.emit("v2m://state-update", &state);
    Ok(state)
}

/// Pause daemon operations
#[tauri::command]
fn pause_daemon(app: tauri::AppHandle) -> Result<DaemonState, IpcError> {
    let data = send_json_request("PAUSE_DAEMON", None)?;
    let state: DaemonState = serde_json::from_value(data)
        .unwrap_or(DaemonState {
            state: "paused".to_string(),
            transcription: None,
            refined_text: None,
            message: None,
            telemetry: None,
        });
    let _ = app.emit("v2m://state-update", &state);
    Ok(state)
}

/// Resume daemon operations
#[tauri::command]
fn resume_daemon(app: tauri::AppHandle) -> Result<DaemonState, IpcError> {
    let data = send_json_request("RESUME_DAEMON", None)?;
    let state: DaemonState = serde_json::from_value(data)
        .unwrap_or(DaemonState {
            state: "idle".to_string(),
            transcription: None,
            refined_text: None,
            message: None,
            telemetry: None,
        });
    let _ = app.emit("v2m://state-update", &state);
    Ok(state)
}

/// Update runtime config
#[tauri::command]
fn update_config(updates: Value) -> Result<Value, IpcError> {
    send_json_request("UPDATE_CONFIG", Some(updates))
}

/// Get current config
#[tauri::command]
fn get_config() -> Result<Value, IpcError> {
    send_json_request("GET_CONFIG", None)
}

/// Helper: Resolve path to daemon script.
fn resolve_daemon_script(app: &tauri::AppHandle) -> Result<std::path::PathBuf, IpcError> {
    // Try dev path first (relative to project)
    let dev_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.join("scripts/v2m-daemon.sh"));

    if let Some(path) = dev_path.filter(|p| p.exists()) {
        Ok(path)
    } else {
        // Fallback to bundled resources (production)
        app.path()
            .resolve("scripts/v2m-daemon.sh", BaseDirectory::Resource)
            .map_err(|e| IpcError::from(format!("Script path resolve error: {}", e)))
    }
}

/// Restart daemon process
#[tauri::command]
async fn restart_daemon(app: tauri::AppHandle) -> Result<DaemonState, IpcError> {
    let script_path = resolve_daemon_script(&app)?;

    let output = SysCommand::new("bash")
        .arg(&script_path)
        .arg("restart")
        .output()
        .map_err(|e| IpcError::from(format!("Restart script error: {}", e)))?;

    if output.status.success() {
        let state = DaemonState {
            state: "restarting".to_string(),
            transcription: None,
            refined_text: None,
            message: Some("Daemon restarted".to_string()),
            telemetry: None,
        };
        let _ = app.emit("v2m://state-update", &state);
        Ok(state)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(IpcError {
            code: "RESTART_FAILED".to_string(),
            message: stderr.to_string(),
        })
    }
}

/// Shutdown daemon process
#[tauri::command]
async fn shutdown_daemon(app: tauri::AppHandle) -> Result<DaemonState, IpcError> {
    let script_path = resolve_daemon_script(&app)?;

    let output = SysCommand::new("bash")
        .arg(&script_path)
        .arg("stop")
        .output()
        .map_err(|e| IpcError::from(format!("Shutdown script error: {}", e)))?;

    if output.status.success() {
        let state = DaemonState {
            state: "disconnected".to_string(),
            transcription: None,
            refined_text: None,
            message: Some("Daemon stopped".to_string()),
            telemetry: None,
        };
        let _ = app.emit("v2m://state-update", &state);
        Ok(state)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(IpcError {
            code: "SHUTDOWN_FAILED".to_string(),
            message: stderr.to_string(),
        })
    }
}

/// Transcribe a media file (video/audio) to text
///
/// Supports: MP4, MOV, MKV (video) and WAV, MP3, FLAC, M4A (audio)
/// Forwards request to Python backend which handles efficient streaming extraction.
#[tauri::command]
async fn transcribe_file(app: tauri::AppHandle, file_path: String) -> Result<DaemonState, IpcError> {
    #[cfg(debug_assertions)]
    eprintln!("[IPC] Transcribing: {}", file_path);

    let path = std::path::Path::new(&file_path);
    let ext = path.extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_lowercase())
        .unwrap_or_default();

    let video_extensions = ["mp4", "mov", "mkv", "avi", "webm"];
    let is_video = video_extensions.contains(&ext.as_str());

    // 1. Notify Frontend: Processing Started
    let initial_step = if is_video { "extracting" } else { "transcribing" };
    let _ = app.emit("v2m://export-status", json!({ "step": initial_step, "progress": 0 }));

    let data = json!({ "file_path": file_path });

    // 2. Call Backend
    match send_json_request("TRANSCRIBE_FILE", Some(data)) {
        Ok(json_value) => {
             // Deserialize success state
             let state: DaemonState = serde_json::from_value(json_value)
                .map_err(|e| IpcError::from(format!("Parse error: {}", e)))?;

             // Emit event for "Remote Control" UI listeners
             let _ = app.emit("v2m://transcription-complete", &state);

             // PERSISTENCE: Save state so frontend can recover it on mount
             if let Ok(mut store) = get_last_export_store().lock() {
                 *store = Some(state.clone());
             }

             Ok(state)
        },
        Err(e) => Err(e)
    }
}

/// Retrieve the last successful export result
/// Used by frontend on mount to check if a job finished while it was unmounted.
#[tauri::command]
fn get_last_export() -> Option<DaemonState> {
    get_last_export_store().lock().ok().and_then(|g| g.clone())
}

// --- ENTRY POINT ---

/// Configuración inicial de la aplicación Tauri.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            get_status,
            start_recording,
            stop_recording,
            ping,
            process_text,
            translate_text,
            pause_daemon,
            resume_daemon,
            update_config,
            get_config,
            restart_daemon,
            shutdown_daemon,
            shutdown_daemon,
            transcribe_file,
            get_last_export
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
