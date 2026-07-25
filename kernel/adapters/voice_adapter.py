

"""Voice capability adapter for the JARVIS Kernel."""

from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)


class VoiceAdapter(CapabilityAdapter):
    """Framework-independent voice adapter."""

    def __init__(self) -> None:
        self._initialized = False

    @property
    def name(self) -> str:
        return "voice"

    @property
    def capability_type(self) -> str:
        return "voice"

    @property
    def description(self) -> str:
        return "Provides speech recognition and speech synthesis capabilities."

    async def initialize(self) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent.lower() in {
            "speech_to_text",
            "text_to_speech",
            "start_listening",
            "stop_listening",
            "wake_word",
        }

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("VoiceAdapter has not been initialized.")

        messages = {
            "speech_to_text": "Speech-to-text placeholder.",
            "text_to_speech": "Text-to-speech placeholder.",
            "start_listening": "Start listening placeholder.",
            "stop_listening": "Stop listening placeholder.",
            "wake_word": "Wake word placeholder.",
        }

        return CapabilityResult(
            success=True,
            data={
                "intent": task.intent,
                "payload": task.payload,
                "context": task.context,
                "message": messages.get(
                    task.intent,
                    "Voice placeholder executed successfully.",
                ),
            },
            metadata={
                "adapter": self.name,
                "status": "placeholder",
            },
            execution_time_ms=0.0,
        )

    async def shutdown(self) -> None:
        self._initialized = False