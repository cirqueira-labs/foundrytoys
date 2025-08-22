from typing import Optional, Tuple


class InferenceService:
    def __init__(self) -> None:
        self._configured = False
        self._model: Optional[str] = None

    def configure(self, model: Optional[str] = None) -> None:
        self._model = model
        self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    def send_message(self, message: str) -> Tuple[bool, str]:
        if not self._configured:
            return False, "Serviço de inferência não configurado."
        if not message.strip():
            return False, "Mensagem vazia."
        return True, f"[stub:{self._model or 'default'}] {message}"
