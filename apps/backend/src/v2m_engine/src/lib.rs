//! V2M Engine - High-Performance Rust Extensions for Voice2Machine
//!
//! # Architecture (SOTA 2026)
//! - Audio: Lock-Free SPSC Ring Buffer (ringbuf 0.4)
//! - Resampling: Band-limited Sinc Interpolation (rubato 0.16)
//! - VAD: WebRTC Voice Activity Detection
//! - Monitoring: Native Syscalls (sysinfo 0.33)

use log::{error, info, warn};
use numpy::{PyArray1, PyArrayMethods};
use pyo3::prelude::*;
use ringbuf::{
    traits::{Consumer, Producer, Split},
    HeapRb,
};
use rubato::{
    Resampler, SincFixedIn, SincInterpolationParameters, SincInterpolationType, WindowFunction,
};
use sysinfo::System;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};

// ============================================================================
// AUDIO RECORDER - Lock-Free Ring Buffer + High Quality Resampling
// ============================================================================

type RingProducer = ringbuf::HeapProd<f32>;
type RingConsumer = ringbuf::HeapCons<f32>;

/// AudioRecorder implementation in Rust using Lock-Free Ring Buffer.
///
/// Uses CPAL for cross-platform audio capture and Rubato for high-quality
/// sinc interpolation resampling to target sample rate (typically 16kHz for Whisper).
#[pyclass(unsendable)]
struct AudioRecorder {
    stream: Option<cpal::Stream>,
    consumer: Option<RingConsumer>,

    requested_sample_rate: u32,
    device_sample_rate: u32,
    channels: u16,
    is_recording: bool,
}

#[pymethods]
impl AudioRecorder {
    #[new]
    #[pyo3(signature = (sample_rate=16000, channels=1))]
    fn new(sample_rate: u32, channels: u16) -> Self {
        let _ = pyo3_log::try_init();

        AudioRecorder {
            stream: None,
            consumer: None,
            requested_sample_rate: sample_rate,
            device_sample_rate: 0,
            channels,
            is_recording: false,
        }
    }

    fn start(&mut self) -> PyResult<()> {
        if self.is_recording {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "Recording already in progress",
            ));
        }

        let host = cpal::default_host();
        let device = match host.default_input_device() {
            Some(d) => d,
            None => {
                return Err(pyo3::exceptions::PyOSError::new_err(
                    "No input device available",
                ))
            }
        };

        // Get supported configs
        let supported_configs = match device.supported_input_configs() {
            Ok(c) => c,
            Err(e) => {
                return Err(pyo3::exceptions::PyOSError::new_err(format!(
                    "Failed to query device configs: {}",
                    e
                )))
            }
        };

        // Select best config: prioritize channel match, resample if rate doesn't match
        let best_config_range = supported_configs
            .into_iter()
            .filter(|c| c.channels() == self.channels)
            .max_by_key(|c| c.max_sample_rate());

        let config: cpal::StreamConfig = match best_config_range {
            Some(c) => {
                let req_rate = cpal::SampleRate(self.requested_sample_rate);
                let target_rate =
                    if c.min_sample_rate() <= req_rate && c.max_sample_rate() >= req_rate {
                        req_rate
                    } else {
                        c.max_sample_rate()
                    };

                self.device_sample_rate = target_rate.0;
                c.with_sample_rate(target_rate).into()
            }
            None => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "No supported config found for {} channels",
                    self.channels
                )));
            }
        };

        info!(
            "Starting recording: Requested={}Hz, Device={}Hz",
            self.requested_sample_rate, self.device_sample_rate
        );

        // Allocate buffer (approx 10 mins at device rate)
        let buffer_size = (self.device_sample_rate * 60 * 10) as usize;
        let rb = HeapRb::<f32>::new(buffer_size);
        let (mut producer, consumer) = rb.split();

        self.consumer = Some(consumer);

        let err_fn = move |err| {
            error!("Audio stream error: {}", err);
        };

        let stream = device
            .build_input_stream(
                &config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    // ringbuf 0.4 API: push_slice returns count, we ignore it (drop samples if full)
                    let _ = producer.push_slice(data);
                },
                err_fn,
                None,
            )
            .map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Failed to build input stream: {}",
                    e
                ))
            })?;

        stream.play().map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to start stream: {}", e))
        })?;

        self.stream = Some(stream);
        self.is_recording = true;

        Ok(())
    }

    fn stop<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f32>>> {
        if !self.is_recording {
            return Err(pyo3::exceptions::PyRuntimeError::new_err("Not recording"));
        }

        self.stream = None;
        self.is_recording = false;

        let mut raw_data = Vec::new();
        if let Some(mut consumer) = self.consumer.take() {
            // ringbuf 0.4: use pop_iter()
            while let Some(sample) = consumer.try_pop() {
                raw_data.push(sample);
            }
        }

        // Resample if necessary
        let final_data = if self.device_sample_rate != self.requested_sample_rate
            && !raw_data.is_empty()
        {
            info!(
                "Resampling from {}Hz to {}Hz",
                self.device_sample_rate, self.requested_sample_rate
            );

            let params = SincInterpolationParameters {
                sinc_len: 256,
                f_cutoff: 0.95,
                interpolation: SincInterpolationType::Linear,
                oversampling_factor: 256,
                window: WindowFunction::BlackmanHarris2,
            };

            let f_ratio = self.requested_sample_rate as f64 / self.device_sample_rate as f64;
            let mut resampler = SincFixedIn::<f32>::new(
                f_ratio,
                256.0,
                params,
                raw_data.len(),
                1, // channels
            )
            .map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Resampler init failed: {}", e))
            })?;

            let waves = vec![raw_data];
            let resampled_waves = resampler.process(&waves, None).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Resampling failed: {}", e))
            })?;

            resampled_waves[0].clone()
        } else {
            raw_data
        };

        // PyO3 0.23: use PyArray1::from_vec_bound
        Ok(PyArray1::from_vec(py, final_data))
    }
}

// ============================================================================
// VOICE ACTIVITY DETECTOR - WebRTC VAD (SOTA 2026)
// ============================================================================

/// Voice Activity Detector using WebRTC algorithm.
///
/// WebRTC VAD is battle-tested (used in Chrome, Firefox) and provides
/// low-latency speech detection without GPU/ONNX overhead.
///
/// Aggressiveness levels:
/// - 0: Least aggressive (more false positives, fewer missed detections)
/// - 1: Low aggressiveness
/// - 2: Medium aggressiveness
/// - 3: Most aggressive (fewer false positives, may miss quiet speech)
#[pyclass(unsendable)]
struct VoiceActivityDetector {
    vad: webrtc_vad::Vad,
    sample_rate: webrtc_vad::SampleRate,
}

#[pymethods]
impl VoiceActivityDetector {
    #[new]
    #[pyo3(signature = (aggressiveness=2, sample_rate=16000))]
    fn new(aggressiveness: i32, sample_rate: u32) -> PyResult<Self> {
        let _ = pyo3_log::try_init();

        let sr = match sample_rate {
            8000 => webrtc_vad::SampleRate::Rate8kHz,
            16000 => webrtc_vad::SampleRate::Rate16kHz,
            32000 => webrtc_vad::SampleRate::Rate32kHz,
            48000 => webrtc_vad::SampleRate::Rate48kHz,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "Sample rate must be 8000, 16000, 32000, or 48000",
                ))
            }
        };

        let mut vad = webrtc_vad::Vad::new();
        vad.set_mode(match aggressiveness {
            0 => webrtc_vad::VadMode::Quality,
            1 => webrtc_vad::VadMode::LowBitrate,
            2 => webrtc_vad::VadMode::Aggressive,
            3 => webrtc_vad::VadMode::VeryAggressive,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "Aggressiveness must be 0-3",
                ))
            }
        });

        info!("VAD initialized: aggressiveness={}, rate={}Hz", aggressiveness, sample_rate);

        Ok(VoiceActivityDetector { vad, sample_rate: sr })
    }

    /// Check if a single frame contains speech.
    ///
    /// Frame must be exactly 10ms, 20ms, or 30ms of audio at the configured sample rate.
    /// For 16kHz: 160, 320, or 480 samples.
    ///
    /// Args:
    ///     frame: Audio frame as i16 samples (PCM 16-bit)
    ///
    /// Returns:
    ///     True if speech detected, False otherwise
    fn is_speech(&mut self, frame: &Bound<'_, PyArray1<i16>>) -> PyResult<bool> {
        let slice = unsafe { frame.as_slice()? };

        match self.vad.is_voice_segment(slice) {
            Ok(result) => Ok(result),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "VAD error: {:?}. Frame must be 10/20/30ms (160/320/480 samples at 16kHz)",
                e
            ))),
        }
    }

    /// Process entire audio buffer and detect speech segments.
    ///
    /// Scans through audio in 30ms frames and returns (start, end) indices
    /// of continuous speech regions.
    ///
    /// Args:
    ///     audio: Float32 audio samples normalized to [-1.0, 1.0]
    ///     frame_ms: Frame duration in milliseconds (10, 20, or 30)
    ///     min_speech_frames: Minimum consecutive speech frames to count as speech segment
    ///     min_silence_frames: Minimum consecutive silence frames to end segment
    ///
    /// Returns:
    ///     List of (start_sample, end_sample) tuples for speech regions
    #[pyo3(signature = (audio, frame_ms=30, min_speech_frames=3, min_silence_frames=10))]
    fn detect_segments(
        &mut self,
        audio: &Bound<'_, PyArray1<f32>>,
        frame_ms: u32,
        min_speech_frames: usize,
        min_silence_frames: usize,
    ) -> PyResult<Vec<(usize, usize)>> {
        let samples_per_sec = match self.sample_rate {
            webrtc_vad::SampleRate::Rate8kHz => 8000,
            webrtc_vad::SampleRate::Rate16kHz => 16000,
            webrtc_vad::SampleRate::Rate32kHz => 32000,
            webrtc_vad::SampleRate::Rate48kHz => 48000,
        };

        let frame_samples = (samples_per_sec * frame_ms / 1000) as usize;

        // Validate frame size
        if frame_ms != 10 && frame_ms != 20 && frame_ms != 30 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "frame_ms must be 10, 20, or 30",
            ));
        }

        let audio_slice = unsafe { audio.as_slice()? };

        // Convert f32 to i16
        let audio_i16: Vec<i16> = audio_slice
            .iter()
            .map(|&s| (s.clamp(-1.0, 1.0) * 32767.0) as i16)
            .collect();

        let total_frames = audio_i16.len() / frame_samples;
        let mut segments: Vec<(usize, usize)> = Vec::new();

        let mut in_speech = false;
        let mut speech_start = 0;
        let mut speech_frame_count = 0;
        let mut silence_frame_count = 0;

        for frame_idx in 0..total_frames {
            let start = frame_idx * frame_samples;
            let end = start + frame_samples;
            let frame = &audio_i16[start..end];

            let is_voice = self.vad.is_voice_segment(frame).unwrap_or(false);

            if is_voice {
                silence_frame_count = 0;
                speech_frame_count += 1;

                if !in_speech && speech_frame_count >= min_speech_frames {
                    // Speech segment started
                    in_speech = true;
                    speech_start = (frame_idx - min_speech_frames + 1) * frame_samples;
                }
            } else {
                if in_speech {
                    silence_frame_count += 1;

                    if silence_frame_count >= min_silence_frames {
                        // Speech segment ended
                        let speech_end = (frame_idx - min_silence_frames) * frame_samples;
                        if speech_end > speech_start {
                            segments.push((speech_start, speech_end));
                        }
                        in_speech = false;
                        speech_frame_count = 0;
                    }
                } else {
                    speech_frame_count = 0;
                }
            }
        }

        // Handle case where audio ends during speech
        if in_speech {
            segments.push((speech_start, audio_i16.len()));
        }

        info!("VAD detected {} speech segments", segments.len());
        Ok(segments)
    }

    /// Filter audio to keep only speech segments.
    ///
    /// Returns a new array containing only the speech portions of the input.
    #[pyo3(signature = (audio, frame_ms=30))]
    fn filter_speech<'py>(
        &mut self,
        py: Python<'py>,
        audio: &Bound<'py, PyArray1<f32>>,
        frame_ms: u32,
    ) -> PyResult<Bound<'py, PyArray1<f32>>> {
        let segments = self.detect_segments(audio, frame_ms, 3, 10)?;
        let audio_slice = unsafe { audio.as_slice()? };

        let mut filtered: Vec<f32> = Vec::new();
        for (start, end) in segments {
            let end = end.min(audio_slice.len());
            filtered.extend_from_slice(&audio_slice[start..end]);
        }

        if filtered.is_empty() {
            warn!("VAD: No speech detected in audio");
        } else {
            info!("VAD: Kept {:.1}% of audio ({} -> {} samples)",
                  100.0 * filtered.len() as f32 / audio_slice.len() as f32,
                  audio_slice.len(), filtered.len());
        }

        Ok(PyArray1::from_vec(py, filtered))
    }
}

// ============================================================================
// SYSTEM MONITOR - CPU/RAM/GPU Metrics
// ============================================================================

/// SystemMonitor implementation in Rust using sysinfo.
///
/// Provides low-overhead system metrics collection via native syscalls,
/// avoiding Python's GIL during metric gathering.
#[pyclass]
struct SystemMonitor {
    sys: System,
    #[cfg(feature = "nvidia")]
    nvml: Option<nvml_wrapper::Nvml>,
}

#[pymethods]
impl SystemMonitor {
    #[new]
    fn new() -> Self {
        let _ = pyo3_log::try_init();

        #[cfg(feature = "nvidia")]
        let nvml = match nvml_wrapper::Nvml::init() {
            Ok(n) => {
                info!("NVML initialized for GPU monitoring");
                Some(n)
            }
            Err(e) => {
                warn!("NVML init failed (GPU temp unavailable): {:?}", e);
                None
            }
        };

        SystemMonitor {
            sys: System::new_all(),
            #[cfg(feature = "nvidia")]
            nvml,
        }
    }

    fn update(&mut self) {
        self.sys.refresh_cpu_all();
        self.sys.refresh_memory();
    }

    fn get_ram_usage(&self) -> (u64, u64, f32) {
        let total = self.sys.total_memory();
        let used = self.sys.used_memory();
        let percent = if total > 0 {
            (used as f64 / total as f64) * 100.0
        } else {
            0.0
        };
        (total, used, percent as f32)
    }

    fn get_cpu_usage(&self) -> f32 {
        self.sys.global_cpu_usage()
    }

    /// Get GPU temperature in Celsius (requires nvidia feature).
    /// Returns 0 if NVML is not available or fails.
    fn get_gpu_temp(&self) -> u32 {
        #[cfg(feature = "nvidia")]
        if let Some(ref nvml) = self.nvml {
            if let Ok(device) = nvml.device_by_index(0) {
                if let Ok(temp) = device.temperature(nvml_wrapper::enum_wrappers::device::TemperatureSensor::Gpu) {
                    return temp;
                }
            }
        }
        0
    }
}

// ============================================================================
// MODULE REGISTRATION
// ============================================================================

#[pymodule]
fn v2m_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AudioRecorder>()?;
    m.add_class::<VoiceActivityDetector>()?;
    m.add_class::<SystemMonitor>()?;
    Ok(())
}
