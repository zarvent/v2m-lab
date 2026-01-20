"""Pruebas unitarias para regresiones y bugs corregidos en AudioRecorder.

Este archivo contiene pruebas diseñadas para reproducir y evitar la reaparición
de bugs específicos encontrados en `AudioRecorder`.

Pruebas incluidas:
    - Resource leak en `start()`: Verifica que el stream se cierre si falla `start()`.
    - Buffer corruption en `stop()`: Verifica que `stop()` retorne una copia segura del buffer.

Ejecución:
    >>> pytest tests/unit/test_audio_recorder_regressions.py
"""

import unittest
from unittest.mock import MagicMock, patch

from v2m.domain.errors import RecordingError
from v2m.infrastructure.audio.recorder import AudioRecorder


class TestAudioRecorderRegressions(unittest.TestCase):
    def setUp(self):
        # Force Python fallback path for these tests (tests are designed for Python impl)
        self.patcher = patch("v2m.infrastructure.audio.recorder.HAS_RUST_ENGINE", False)
        self.patcher.start()
        self.recorder = AudioRecorder()

    def tearDown(self):
        self.patcher.stop()

    @patch("v2m.infrastructure.audio.recorder.sd")
    def test_start_failure_cleans_up_resources(self, mock_sd):
        """
        Verifica que si stream.start() falla, se limpien los recursos correctamente.

        Bug corregido:
            Anteriormente, si `self._stream.start()` lanzaba una excepción,
            `self._stream` quedaba asignado pero en un estado inconsistente,
            y `_recording` quedaba en False. Esto podía causar fugas de recursos
            o errores en intentos posteriores de `start()`.

        Comportamiento esperado:
            - Se debe lanzar RecordingError.
            - `self._recording` debe ser False.
            - `self._stream` debe ser None (limpiado).
            - Se debe haber llamado a `stream.close()`.
        """
        # Arrange
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        # Simular fallo en start()
        mock_stream.start.side_effect = Exception("Simulated start failure")

        # Act & Assert
        with self.assertRaises(RecordingError):
            self.recorder.start()

        self.assertFalse(self.recorder._recording)
        self.assertIsNone(self.recorder._stream, "El stream debería ser None tras un fallo en start()")
        mock_stream.close.assert_called_once()

    def test_stop_returns_copy_to_prevent_corruption(self):
        """
        Verifica que `stop()` retorne una COPIA del buffer, no una vista.

        Bug corregido:
            Anteriormente, `stop()` retornaba una vista (`slice`) del buffer interno pre-allocado.
            Si se llamaba a `start()` nuevamente (reiniciando la grabación) mientras el caller
            aún procesaba el audio anterior, los datos en la vista se corrompían (sobrescribían)
            por la nueva grabación.

        Comportamiento esperado:
            - El array retornado por `stop()` no debe cambiar si se modifica el buffer interno.
        """
        # Arrange
        recorder = AudioRecorder(sample_rate=16000, max_duration_sec=1)

        # Simular estado de grabación manual para evitar depender de sounddevice real
        recorder._recording = True
        recorder._stream = MagicMock()  # Mock stream to avoid errors in stop()

        # Simular datos grabados: [1.0, 1.0, ...]
        with recorder._lock:
            recorder._buffer[:100] = 1.0
            recorder._write_pos = 100

        # Act
        # Detener grabación (debería retornar copia)
        audio_data = recorder.stop()

        # Assert inicial
        self.assertEqual(audio_data[0], 1.0, "El audio inicial debe ser 1.0")

        # Simular nueva grabación sobrescribiendo el buffer
        with recorder._lock:
            recorder._buffer[:100] = 2.0  # Sobrescribir con 2.0

        # Assert final: el audio_data original NO debe haber cambiado
        self.assertEqual(
            audio_data[0],
            1.0,
            "El audio retornado fue corrompido por cambios en el buffer interno. `stop()` debe retornar una copia.",
        )


if __name__ == "__main__":
    unittest.main()
