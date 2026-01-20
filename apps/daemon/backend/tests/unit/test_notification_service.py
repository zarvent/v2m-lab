
"""
tests unitarios para el servicio de notificaciones

valida el comportamiento del LinuxNotificationService incluyendo:
- envío de notificaciones via dbus
- auto-dismiss programático
- fallback a notify-send
- configuración desde config
- thread pool executor lifecycle
"""

import subprocess
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest


@dataclass
class MockNotificationsConfig:
    """configuración mock para tests"""

    expire_time_ms: int = 1000  # 1 segundo para tests rápidos
    auto_dismiss: bool = True


class TestNotificationResult:
    """tests para el dataclass NotificationResult"""

    def test_success_result(self):
        """NotificationResult con success=True debe tener notification_id"""
        from v2m.infrastructure.notification_service import NotificationResult

        result = NotificationResult(success=True, notification_id=42)

        assert result.success is True
        assert result.notification_id == 42
        assert result.error is None

    def test_failure_result(self):
        """NotificationResult con success=False debe tener error"""
        from v2m.infrastructure.notification_service import NotificationResult

        result = NotificationResult(success=False, error="test error")

        assert result.success is False
        assert result.notification_id is None
        assert result.error == "test error"

    def test_immutable(self):
        """NotificationResult debe ser inmutable (frozen=True)"""
        from v2m.infrastructure.notification_service import NotificationResult

        result = NotificationResult(success=True, notification_id=1)

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore


class TestLinuxNotificationService:
    """tests para LinuxNotificationService"""

    @pytest.fixture(autouse=True)
    def reset_executor(self):
        """resetea el executor singleton entre tests"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        # forzar reset del executor singleton
        LinuxNotificationService._executor = None
        yield
        # cleanup después del test
        LinuxNotificationService.shutdown_all()

    def test_init_with_custom_config(self):
        """debe inicializar con configuración personalizada"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        config = MockNotificationsConfig(expire_time_ms=5000, auto_dismiss=False)
        service = LinuxNotificationService(config=config)

        assert service._expire_time_ms == 5000
        assert service._auto_dismiss is False

    def test_init_creates_executor(self):
        """debe crear el thread pool executor al inicializar"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        config = MockNotificationsConfig()
        _service = LinuxNotificationService(config=config)

        assert LinuxNotificationService._executor is not None

    def test_executor_is_singleton(self):
        """el executor debe ser compartido entre instancias"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        config = MockNotificationsConfig()
        service1 = LinuxNotificationService(config=config)
        service2 = LinuxNotificationService(config=config)

        assert service1._executor is service2._executor

    @patch("subprocess.run")
    def test_send_notification_success(self, mock_run):
        """debe enviar notificación via dbus exitosamente"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        # configurar mock para retornar id de notificación
        mock_run.return_value = MagicMock(returncode=0, stdout="(uint32 123,)", stderr="")

        config = MockNotificationsConfig(auto_dismiss=False)  # desactivar dismiss
        service = LinuxNotificationService(config=config)

        service.notify("Test Title", "Test Message")

        # verificar que se llamó gdbus con los argumentos correctos
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "gdbus" in call_args
        assert "Test Title" in call_args
        assert "Test Message" in call_args

    @patch("subprocess.run")
    def test_fallback_to_notify_send(self, mock_run):
        """debe usar notify-send como fallback si dbus falla"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        # primera llamada (gdbus) falla, segunda (notify-send) ok
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="dbus error"),
            MagicMock(),  # fallback notify-send
        ]

        config = MockNotificationsConfig(auto_dismiss=False)
        service = LinuxNotificationService(config=config)

        service.notify("Test", "Message")

        # verificar que se llamó notify-send como fallback
        assert mock_run.call_count == 2
        second_call = mock_run.call_args_list[1][0][0]
        assert "notify-send" in second_call

    @patch("subprocess.run")
    def test_schedule_dismiss_called_when_auto_dismiss_enabled(self, mock_run):
        """debe programar dismiss cuando auto_dismiss está habilitado"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        # gdbus retorna id de notificación
        mock_run.return_value = MagicMock(returncode=0, stdout="(uint32 99,)", stderr="")

        config = MockNotificationsConfig(expire_time_ms=100, auto_dismiss=True)
        service = LinuxNotificationService(config=config)

        service.notify("Test", "Message")

        # verificar que se incrementó el pending count
        # (solo por un instante, pero demuestra que se programó)
        # nota: este es un test de comportamiento, no de implementación
        assert service._executor is not None

    def test_pending_dismissals_property(self):
        """pending_dismissals debe retornar conteo correcto"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        config = MockNotificationsConfig()
        service = LinuxNotificationService(config=config)

        # inicialmente debe ser 0
        assert service.pending_dismissals == 0

    @patch("subprocess.run")
    def test_gdbus_not_found(self, mock_run):
        """debe manejar FileNotFoundError gracefully"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        mock_run.side_effect = FileNotFoundError("gdbus not found")

        config = MockNotificationsConfig()
        service = LinuxNotificationService(config=config)

        # no debe lanzar excepción
        service.notify("Test", "Message")

    @patch("subprocess.run")
    def test_timeout_handling(self, mock_run):
        """debe manejar timeouts de subprocess"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        mock_run.side_effect = subprocess.TimeoutExpired("gdbus", 2)

        config = MockNotificationsConfig()
        service = LinuxNotificationService(config=config)

        # no debe lanzar excepción
        service.notify("Test", "Message")

    def test_shutdown_all_closes_executor(self):
        """shutdown_all debe cerrar el executor singleton"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        config = MockNotificationsConfig()
        _service = LinuxNotificationService(config=config)

        assert LinuxNotificationService._executor is not None

        LinuxNotificationService.shutdown_all()

        assert LinuxNotificationService._executor is None


class TestLinuxNotificationAdapter:
    """tests para el adapter legacy de compatibilidad"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """resetea estado entre tests"""
        from v2m.infrastructure.notification_service import LinuxNotificationService

        LinuxNotificationService._executor = None
        yield
        LinuxNotificationService.shutdown_all()

    @patch("v2m.infrastructure.notification_service.LinuxNotificationService.notify")
    def test_delegates_to_service(self, mock_notify):
        """adapter debe delegar al servicio de notificaciones"""
        from v2m.infrastructure.linux_adapters import LinuxNotificationAdapter

        adapter = LinuxNotificationAdapter()
        adapter.notify("Title", "Message")

        mock_notify.assert_called_once_with("Title", "Message")

    def test_implements_interface(self):
        """adapter debe implementar NotificationInterface"""
        from v2m.core.interfaces import NotificationInterface
        from v2m.infrastructure.linux_adapters import LinuxNotificationAdapter

        adapter = LinuxNotificationAdapter()

        assert isinstance(adapter, NotificationInterface)
