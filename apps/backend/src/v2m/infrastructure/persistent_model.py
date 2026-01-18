import asyncio
import gc
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import psutil
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


def _safe_log(level: int, msg: str) -> None:
    """Log safely, suppressing errors when interpreter is shutting down."""
    try:
        # Check if interpreter is shutting down (sys.stderr may be None or closed)
        if sys.stderr is None:
            return
        logger.log(level, msg)
    except (ValueError, OSError):
        # I/O operation on closed file - interpreter is shutting down
        pass


class PersistentWhisperWorker:
    """
    Gestiona una instancia persistente del modelo Whisper en un hilo dedicado.
    Implementa política de 'keep-warm' por defecto, liberando recursos solo bajo presión de memoria.
    """

    def __init__(
        self,
        model_size: str,
        device: str = "cuda",
        compute_type: str = "float16",
        device_index: int = 0,
        num_workers: int = 1,
        keep_warm: bool = True,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.device_index = device_index
        self.num_workers_whisper = num_workers
        self.keep_warm = keep_warm

        self._model: WhisperModel | None = None
        self._lock = asyncio.Lock()
        # Single worker strict for GPU isolation
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="whisper_worker")

    async def initialize(self):
        """Pre-loads the model if keep_warm is True."""
        if self.keep_warm:
            async with self._lock:
                await self._load_model()

    def initialize_sync(self):
        """Carga síncrona para warmup en hilos (Container)."""
        if self.keep_warm and self._model is None:
            _safe_log(logging.INFO, "Precargando modelo (Sync)...")
            self._model = self._create_model()
            _safe_log(logging.INFO, "Modelo precargado.")

    async def run_inference(self, func, *args, **kwargs):
        """
        Ejecuta una función de inferencia (que usa el modelo) en el executor dedicado.
        La función `func` debe aceptar `model` como primer argumento.
        """
        async with self._lock:
            if self._model is None:
                await self._load_model()
            elif not self.keep_warm:
                # Si no es keep_warm, verificamos si deberíamos descargar antes (pero aquí estamos por ejecutar)
                pass

            # Check memory pressure before execution if policy requires (logging only)
            if self._is_memory_critical():
                logger.warning("Memoria crítica detectada (>90%), procediendo con inferencia.")

            loop = asyncio.get_running_loop()
            try:
                # Ejecutar la función pasando el modelo
                return await loop.run_in_executor(self._executor, lambda: func(self._model, *args, **kwargs))
            except Exception as e:
                logger.error(f"Error de inferencia: {e}")
                raise

    async def transcribe(self, audio: Any, **kwargs):
        """Wrapper directo para transcribe."""

        def _transcribe_sync(model, audio_data, **opts):
            # faster-whisper transcribe returns a generator.
            # We must convert to list inside the executor to perform the inference there.
            segments, info = model.transcribe(audio_data, **opts)
            return list(segments), info

        return await self.run_inference(_transcribe_sync, audio, **kwargs)

    async def _load_model(self):
        if self._model is not None:
            return

        logger.info(f"Cargando modelo Whisper {self.model_size} en {self.device}...")
        loop = asyncio.get_running_loop()
        try:
            self._model = await loop.run_in_executor(self._executor, self._create_model)
            logger.info("Modelo Whisper cargado correctamente.")
        except Exception as e:
            logger.error(f"Fallo al cargar modelo: {e}")
            raise

    def _create_model(self):
        return WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            device_index=self.device_index,
            num_workers=self.num_workers_whisper,
        )

    def _is_memory_critical(self) -> bool:
        try:
            mem = psutil.virtual_memory()
            return mem.percent > 90.0
        except Exception:
            return False

    async def unload(self):
        """Descarga explícita del modelo."""
        async with self._lock:
            if self._model:
                logger.warning("Descargando modelo Whisper de la memoria...")
                self._model = None
                # Force GC
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self._executor, self._gc_collect)
                logger.info("Modelo descargado.")

    def _gc_collect(self):
        gc.collect()
        # Si hubiera torch disponible, torch.cuda.empty_cache()
