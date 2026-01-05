//! V2M Engine - Extensiones de Rust de Alto Rendimiento para Voice2Machine
//!
//! # Arquitectura (State of the Art 2026)
//! - Audio: Búfer Circular Lock-Free SPSC (ringbuf 0.4).
//! - Re-muestreo: Interpolación Sinc de banda limitada (rubato 0.16).
//! - VAD: Detección de Actividad de Voz WebRTC.
//! - Monitoreo: Llamadas al sistema nativas (sysinfo 0.33).

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
// GRABADOR DE AUDIO (AUDIO RECORDER) - Lock-Free Ring Buffer + Re-muestreo
// ============================================================================

type RingProducer = ringbuf::HeapProd<f32>;
type RingConsumer = ringbuf::HeapCons<f32>;

/// Implementación de AudioRecorder en Rust usando Búfer Circular Lock-Free.
///
/// Utiliza CPAL para captura de audio multiplataforma y Rubato para re-muestreo
/// de alta calidad mediante interpolación sinc a la frecuencia objetivo (típicamente 16kHz para Whisper).
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
                "Grabación ya en curso",
            ));
        }

        let host = cpal::default_host();
        let device = match host.default_input_device() {
            Some(d) => d,
            None => {
                return Err(pyo3::exceptions::PyOSError::new_err(
                    "No hay dispositivo de entrada disponible",
                ))
            }
        };

        // Obtener configuraciones soportadas
        let supported_configs = match device.supported_input_configs() {
            Ok(c) => c,
            Err(e) => {
                return Err(pyo3::exceptions::PyOSError::new_err(format!(
                    "Fallo al consultar configuraciones del dispositivo: {}",
                    e
                )))
            }
        };

        // Seleccionar mejor configuración: priorizar coincidencia de canales, re-muestrear si la tasa no coincide
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
                    "No se encontró configuración soportada para {} canales",
                    self.channels
                )));
            }
        };

        info!(
            "Iniciando grabación: Solicitado={}Hz, Dispositivo={}Hz",
            self.requested_sample_rate, self.device_sample_rate
        );

        // Asignar búfer (aprox. 10 minutos a la tasa del dispositivo)
        let buffer_size = (self.device_sample_rate * 60 * 10) as usize;
        let rb = HeapRb::<f32>::new(buffer_size);
        let (mut producer, consumer) = rb.split();

        self.consumer = Some(consumer);

        let err_fn = move |err| {
            error!("Error en flujo de audio: {}", err);
        };

        let stream = device
            .build_input_stream(
                &config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    // API ringbuf 0.4: push_slice devuelve conteo, lo ignoramos (descarta muestras si está lleno)
                    let _ = producer.push_slice(data);
                },
                err_fn,
                None,
            )
            .map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Fallo al construir flujo de entrada: {}",
                    e
                ))
            })?;

        stream.play().map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("Fallo al iniciar flujo: {}", e))
        })?;

        self.stream = Some(stream);
        self.is_recording = true;

        Ok(())
    }

    fn stop<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f32>>> {
        if !self.is_recording {
            return Err(pyo3::exceptions::PyRuntimeError::new_err("No se está grabando"));
        }

        self.stream = None;
        self.is_recording = false;

        let mut raw_data = Vec::new();
        if let Some(mut consumer) = self.consumer.take() {
            // ringbuf 0.4: usar pop_iter() o try_pop()
            while let Some(sample) = consumer.try_pop() {
                raw_data.push(sample);
            }
        }

        // Re-muestrear si es necesario
        let final_data = if self.device_sample_rate != self.requested_sample_rate
            && !raw_data.is_empty()
        {
            info!(
                "Re-muestrando de {}Hz a {}Hz",
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
                1, // canales
            )
            .map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Fallo init re-muestreador: {}", e))
            })?;

            let waves = vec![raw_data];
            let resampled_waves = resampler.process(&waves, None).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Fallo al re-muestrear: {}", e))
            })?;

            resampled_waves[0].clone()
        } else {
            raw_data
        };

        // PyO3 0.23: usar PyArray1::from_vec_bound
        Ok(PyArray1::from_vec(py, final_data))
    }
}

// ============================================================================
// DETECTOR DE ACTIVIDAD DE VOZ (VAD) - WebRTC VAD (SOTA 2026)
// ============================================================================

/// Detector de Actividad de Voz usando algoritmo WebRTC.
///
/// WebRTC VAD es robusto (usado en Chrome, Firefox) y provee
/// detección de voz de baja latencia sin overhead de GPU/ONNX.
///
/// Niveles de agresividad:
/// - 0: Menos agresivo (más falsos positivos, menos detecciones perdidas)
/// - 1: Agresividad baja
/// - 2: Agresividad media
/// - 3: Más agresivo (menos falsos positivos, puede perder voz baja)
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
                    "Tasa de muestreo debe ser 8000, 16000, 32000, o 48000",
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
                    "Agresividad debe ser 0-3",
                ))
            }
        });

        info!("VAD inicializado: agresividad={}, tasa={}Hz", aggressiveness, sample_rate);

        Ok(VoiceActivityDetector { vad, sample_rate: sr })
    }

    /// Verifica si un solo frame contiene voz.
    ///
    /// El frame debe ser exactamente 10ms, 20ms, o 30ms de audio a la tasa configurada.
    /// Para 16kHz: 160, 320, o 480 muestras.
    ///
    /// Args:
    ///     frame: Frame de audio como muestras i16 (PCM 16-bit)
    ///
    /// Returns:
    ///     True si se detecta voz, False en caso contrario
    fn is_speech(&mut self, frame: &Bound<'_, PyArray1<i16>>) -> PyResult<bool> {
        let slice = unsafe { frame.as_slice()? };

        match self.vad.is_voice_segment(slice) {
            Ok(result) => Ok(result),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Error VAD: {:?}. Frame debe ser 10/20/30ms (160/320/480 muestras a 16kHz)",
                e
            ))),
        }
    }

    /// Procesa el búfer de audio completo y detecta segmentos de voz.
    ///
    /// Escanea el audio en frames de 30ms y devuelve tuplas (inicio, fin)
    /// de regiones de voz continua.
    ///
    /// Args:
    ///     audio: Muestras de audio Float32 normalizadas a [-1.0, 1.0]
    ///     frame_ms: Duración del frame en milisegundos (10, 20, o 30)
    ///     min_speech_frames: Mínimo de frames de voz consecutivos para contar como segmento
    ///     min_silence_frames: Mínimo de frames de silencio consecutivos para terminar segmento
    ///
    /// Returns:
    ///     Lista de tuplas (muestra_inicio, muestra_fin) para regiones de voz
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

        // Validar tamaño de frame
        if frame_ms != 10 && frame_ms != 20 && frame_ms != 30 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "frame_ms debe ser 10, 20, o 30",
            ));
        }

        let audio_slice = unsafe { audio.as_slice()? };

        // Convertir f32 a i16
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
                    // Inicio de segmento de voz
                    in_speech = true;
                    speech_start = (frame_idx - min_speech_frames + 1) * frame_samples;
                }
            } else {
                if in_speech {
                    silence_frame_count += 1;

                    if silence_frame_count >= min_silence_frames {
                        // Fin de segmento de voz
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

        // Manejar caso donde el audio termina durante voz
        if in_speech {
            segments.push((speech_start, audio_i16.len()));
        }

        info!("VAD detectó {} segmentos de voz", segments.len());
        Ok(segments)
    }

    /// Filtrar audio para mantener solo segmentos de voz.
    ///
    /// Retorna un nuevo array conteniendo solo las porciones de voz de la entrada.
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
            warn!("VAD: No se detectó voz en el audio");
        } else {
            info!("VAD: Se mantuvo {:.1}% del audio ({} -> {} muestras)",
                  100.0 * filtered.len() as f32 / audio_slice.len() as f32,
                  audio_slice.len(), filtered.len());
        }

        Ok(PyArray1::from_vec(py, filtered))
    }
}

// ============================================================================
// MONITOR DE SISTEMA - Métricas CPU/RAM/GPU
// ============================================================================

/// Implementación de SystemMonitor en Rust usando sysinfo.
///
/// Provee recolección de métricas de sistema con bajo overhead vía syscalls nativas,
/// evitando el bloqueo por GIL de Python durante la recolección.
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
                info!("NVML inicializado para monitoreo de GPU");
                Some(n)
            }
            Err(e) => {
                warn!("Fallo init NVML (temp GPU no disponible): {:?}", e);
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

    /// Obtener temperatura de GPU en Celsius (requiere feature nvidia).
    /// Retorna 0 si NVML no está disponible o falla.
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
// REGISTRO DE MÓDULO
// ============================================================================

#[pymodule]
fn v2m_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<AudioRecorder>()?;
    m.add_class::<VoiceActivityDetector>()?;
    m.add_class::<SystemMonitor>()?;
    Ok(())
}
