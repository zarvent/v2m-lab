"""Workflow de Procesamiento LLM."""

import asyncio
import re
from typing import TYPE_CHECKING, Any

from v2m.shared.config import config
from v2m.shared.logging import logger

if TYPE_CHECKING:
    from v2m.api.schemas import LLMResponse
    from v2m.features.desktop.linux_adapters import LinuxClipboardAdapter
    from v2m.features.desktop.notification_service import LinuxNotificationService


class LLMWorkflow:
    def __init__(self) -> None:
        self._llm_service: Any | None = None
        self._clipboard: LinuxClipboardAdapter | None = None
        self._notifications: LinuxNotificationService | None = None

    @property
    def clipboard(self):
        if self._clipboard is None:
            from v2m.features.desktop.linux_adapters import LinuxClipboardAdapter

            self._clipboard = LinuxClipboardAdapter()
        return self._clipboard

    @property
    def notifications(self):
        if self._notifications is None:
            from v2m.features.desktop.notification_service import LinuxNotificationService

            self._notifications = LinuxNotificationService()
        return self._notifications

    @property
    def llm_service(self) -> Any:
        if self._llm_service is None:
            backend = config.llm.backend
            if backend == "gemini":
                from v2m.features.llm.gemini_service import GeminiLLMService

                self._llm_service = GeminiLLMService()
            elif backend == "ollama":
                from v2m.features.llm.ollama_service import OllamaLLMService

                self._llm_service = OllamaLLMService()
            else:
                from v2m.features.llm.local_service import LocalLLMService

                self._llm_service = LocalLLMService()
            logger.info(f"LLM backend inicializado: {backend}")
        return self._llm_service

    async def process_text(self, text: str) -> "LLMResponse":
        from v2m.api.schemas import LLMResponse

        backend_name = config.llm.backend
        try:
            if asyncio.iscoroutinefunction(self.llm_service.process_text):
                refined = await self.llm_service.process_text(text)
            else:
                refined = await asyncio.to_thread(self.llm_service.process_text, text)
            self.clipboard.copy(refined)
            self.notifications.notify(f"✅ {backend_name} - copiado", f"{refined[:80]}...")
            return LLMResponse(text=refined, backend=backend_name)
        except Exception as e:
            logger.error(f"Error procesando texto con {backend_name}: {e}")
            self.clipboard.copy(text)
            self.notifications.notify(f"⚠️ {backend_name} falló", "usando texto original...")
            return LLMResponse(text=text, backend=f"{backend_name} (fallback)")

    async def translate_text(self, text: str, target_lang: str) -> "LLMResponse":
        from v2m.api.schemas import LLMResponse

        backend_name = config.llm.backend
        if not re.match(r"^[a-zA-Z\s\-]{2,20}$", target_lang):
            logger.warning(f"Idioma inválido: {target_lang}")
            self.notifications.notify("❌ Error", "Idioma de destino inválido")
            return LLMResponse(text=text, backend="error")
        try:
            if asyncio.iscoroutinefunction(self.llm_service.translate_text):
                translated = await self.llm_service.translate_text(text, target_lang)
            else:
                translated = await asyncio.to_thread(self.llm_service.translate_text, text, target_lang)
            self.clipboard.copy(translated)
            self.notifications.notify(f"✅ Traducción ({target_lang})", f"{translated[:80]}...")
            return LLMResponse(text=translated, backend=backend_name)
        except Exception as e:
            logger.error(f"Error traduciendo con {backend_name}: {e}")
            self.notifications.notify("❌ Error traducción", "Fallo al traducir")
            return LLMResponse(text=text, backend=f"{backend_name} (error)")
