"""Pruebas específicas para la optimización de zero-copy en AudioRecorder.

Este archivo valida el comportamiento del parámetro copy_data=False introducido
en la PR #81 (Bolt: Zero-copy audio buffer optimization).

Propósito
---------
Verificar que la optimización de zero-copy:
    * Retorna una vista (no copia) del buffer cuando copy_data=False
    * La vista contiene los datos correctos inmediatamente después de stop()
    * Llamar a start() después de stop(copy_data=False) puede corromper datos
      si se mantiene una referencia a la vista (comportamiento documentado)
    * El modo copy_data=True (default) sigue funcionando correctamente

Contexto de la optimización
---------------------------
La optimización elimina ~2MB de copia de memoria por cada transcripción de 30s.
Es segura en el flujo normal porque el sistema bloquea nuevas grabaciones hasta
que la transcripción termine.

Referencias
-----------
    * PR #81: https://github.com/zarvent/voice2machine/pull/81
    * NumPy views: https://numpy.org/doc/stable/reference/arrays.ndarray.html#memory-layout

Ejecución
---------
    >>> pytest tests/unit/test_audio_recorder_zero_copy.py -v
"""

import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from v2m.infrastructure.audio.recorder import AudioRecorder
from v2m.domain.errors import RecordingError


class TestAudioRecorderZeroCopy(unittest.TestCase):
    """Suite de pruebas para la funcionalidad zero-copy del AudioRecorder."""

    def setUp(self) -> None:
        """Inicializa el entorno de prueba."""
        self.recorder = AudioRecorder()

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_stop_with_copy_data_false_returns_view(self, mock_sd: MagicMock) -> None:
        """Verifica que copy_data=False retorna una vista, no una copia.

        Test crítico de la optimización: validamos que el array retornado
        sea efectivamente una vista del buffer interno, no una copia.
        """
        # ARRANGE
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()

        # Inyectamos datos de prueba
        test_data = np.ones(16000, dtype=np.float32)
        self.recorder._buffer[:16000] = test_data
        self.recorder._write_pos = 16000

        # ACT: Obtener vista sin copia
        audio_view = self.recorder.stop(copy_data=False)

        # ASSERT: Verificar que es una vista (shares memory con el buffer)
        # Si modificamos audio_view, el buffer interno también debe cambiar
        original_value = audio_view[0]
        audio_view[0] = 999.0

        # El buffer interno debe reflejar el cambio (son la misma memoria)
        self.assertEqual(self.recorder._buffer[0], 999.0)

        # Restaurar para no afectar otros tests
        audio_view[0] = original_value

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_stop_with_copy_data_true_returns_copy(self, mock_sd: MagicMock) -> None:
        """Verifica que copy_data=True (default) retorna una copia independiente.

        Este es el comportamiento seguro por defecto. La copia protege contra
        corrupción de datos si el buffer es reutilizado.
        """
        # ARRANGE
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()

        test_data = np.ones(16000, dtype=np.float32)
        self.recorder._buffer[:16000] = test_data
        self.recorder._write_pos = 16000

        # ACT: Obtener copia (comportamiento default)
        audio_copy = self.recorder.stop(copy_data=True)

        # ASSERT: Verificar que es una copia independiente
        audio_copy[0] = 999.0

        # El buffer interno NO debe cambiar (son memorias diferentes)
        self.assertNotEqual(self.recorder._buffer[0], 999.0)
        self.assertEqual(self.recorder._buffer[0], 1.0)

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_zero_copy_view_contains_correct_data(self, mock_sd: MagicMock) -> None:
        """Verifica que la vista retornada contiene los datos correctos.

        La vista debe reflejar exactamente los datos grabados, no basura
        o datos de otras partes del buffer.
        """
        # ARRANGE
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()

        # Inyectamos un patrón reconocible: rampa de 0 a 15999
        expected_data = np.arange(16000, dtype=np.float32)
        self.recorder._buffer[:16000] = expected_data
        self.recorder._write_pos = 16000

        # ACT
        audio_view = self.recorder.stop(copy_data=False)

        # ASSERT: Los datos deben coincidir exactamente
        np.testing.assert_array_equal(audio_view, expected_data)
        self.assertEqual(len(audio_view), 16000)

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_zero_copy_unsafe_behavior_documented(self, mock_sd: MagicMock) -> None:
        """Documenta el comportamiento unsafe de copy_data=False si se reutiliza.

        Este test sirve como documentación ejecutable del contrato de la API:
        si mantienes una referencia a la vista y empiezas una nueva grabación,
        los datos pueden corromperse.

        IMPORTANTE: Este es el comportamiento ESPERADO y documentado.
        """
        # ARRANGE: Primera grabación
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()
        first_data = np.ones(8000, dtype=np.float32) * 10.0
        self.recorder._buffer[:8000] = first_data
        self.recorder._write_pos = 8000

        # ACT: Obtener vista y mantener referencia
        first_view = self.recorder.stop(copy_data=False)

        # Verificar que los datos iniciales son correctos
        self.assertTrue(np.all(first_view == 10.0))

        # ARRANGE: Segunda grabación que sobreescribe el buffer
        self.recorder.start()
        second_data = np.ones(8000, dtype=np.float32) * 20.0
        self.recorder._buffer[:8000] = second_data
        self.recorder._write_pos = 8000

        # ACT: Detener segunda grabación
        second_view = self.recorder.stop(copy_data=False)

        # ASSERT: first_view ahora está corrupta (apunta al mismo buffer)
        # Los primeros 8000 elementos ahora son 20.0, no 10.0
        self.assertTrue(np.all(first_view == 20.0))
        self.assertTrue(np.all(second_view == 20.0))

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_copy_data_default_is_true(self, mock_sd: MagicMock) -> None:
        """Verifica que el comportamiento default es copy_data=True (seguro).

        Por retrocompatibilidad y seguridad, el default debe ser copia.
        """
        # ARRANGE
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()
        test_data = np.ones(16000, dtype=np.float32)
        self.recorder._buffer[:16000] = test_data
        self.recorder._write_pos = 16000

        # ACT: Llamar stop() sin argumentos
        audio = self.recorder.stop()

        # ASSERT: Debe comportarse como copy_data=True
        audio[0] = 999.0
        self.assertEqual(self.recorder._buffer[0], 1.0)  # Buffer no modificado

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_zero_copy_with_multichannel_audio(self, mock_sd: MagicMock) -> None:
        """Verifica que zero-copy funciona correctamente con audio multicanal."""
        # ARRANGE: Crear recorder estéreo
        recorder_stereo = AudioRecorder(channels=2)
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        recorder_stereo.start()

        # Datos estéreo: (samples, channels)
        test_data = np.ones((8000, 2), dtype=np.float32)
        test_data[:, 0] = 10.0  # Canal L
        test_data[:, 1] = 20.0  # Canal R
        recorder_stereo._buffer[:8000, :] = test_data
        recorder_stereo._write_pos = 8000

        # ACT
        audio_view = recorder_stereo.stop(copy_data=False)

        # ASSERT: Verificar que es una vista con datos correctos
        self.assertEqual(audio_view.shape, (8000, 2))
        np.testing.assert_array_equal(audio_view[:, 0], 10.0)
        np.testing.assert_array_equal(audio_view[:, 1], 20.0)

        # Verificar que es una vista (no copia)
        audio_view[0, 0] = 999.0
        self.assertEqual(recorder_stereo._buffer[0, 0], 999.0)

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_zero_copy_with_empty_recording(self, mock_sd: MagicMock) -> None:
        """Verifica que zero-copy maneja correctamente grabaciones vacías."""
        # ARRANGE
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()
        # No escribimos nada en el buffer (simulando grabación sin audio)
        self.recorder._write_pos = 0

        # ACT
        audio_view = self.recorder.stop(copy_data=False)

        # ASSERT: Debe retornar array vacío
        self.assertEqual(len(audio_view), 0)
        self.assertEqual(audio_view.dtype, np.float32)

    @patch('v2m.infrastructure.audio.recorder.sd')
    def test_zero_copy_partial_buffer_usage(self, mock_sd: MagicMock) -> None:
        """Verifica que zero-copy retorna solo la porción usada del buffer.

        El buffer está pre-allocado para 10 minutos, pero típicamente usamos
        mucho menos. La vista debe reflejar solo los datos grabados.
        """
        # ARRANGE
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        self.recorder.start()

        # Grabamos solo 2000 samples de un buffer de millones
        test_data = np.arange(2000, dtype=np.float32)
        self.recorder._buffer[:2000] = test_data
        self.recorder._write_pos = 2000

        # ACT
        audio_view = self.recorder.stop(copy_data=False)

        # ASSERT: La vista debe tener exactamente 2000 samples, no más
        self.assertEqual(len(audio_view), 2000)
        np.testing.assert_array_equal(audio_view, test_data)


if __name__ == '__main__':
    unittest.main()
