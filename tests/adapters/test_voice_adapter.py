

import pytest

from kernel.adapters.voice_adapter import VoiceAdapter
from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask


@pytest.mark.asyncio
async def test_adapter_metadata():
    adapter = VoiceAdapter()
    assert adapter.name == "voice"
    assert adapter.capability_type == "voice"
    assert "speech" in adapter.description.lower()


@pytest.mark.asyncio
async def test_initialize_and_health_check():
    adapter = VoiceAdapter()
    assert await adapter.health_check() is False
    await adapter.initialize()
    assert await adapter.health_check() is True


@pytest.mark.parametrize(
    "intent",
    [
        "speech_to_text",
        "text_to_speech",
        "start_listening",
        "stop_listening",
        "wake_word",
    ],
)
def test_supported_intents(intent: str):
    assert VoiceAdapter().supports(intent) is True


def test_unsupported_intent():
    assert VoiceAdapter().supports("unsupported") is False


@pytest.mark.asyncio
async def test_execute_requires_initialize():
    adapter = VoiceAdapter()
    task = CapabilityTask(task_id="voice-0", intent="speech_to_text", payload={})
    with pytest.raises(RuntimeError):
        await adapter.execute(task)


@pytest.mark.asyncio
async def test_speech_to_text_execution():
    adapter = VoiceAdapter()
    await adapter.initialize()
    task = CapabilityTask(task_id="voice-1", intent="speech_to_text", payload={"audio": "sample.wav"})
    result = await adapter.execute(task)
    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "voice"
    assert result.data["intent"] == "speech_to_text"
    assert result.data["message"] == "Speech-to-text placeholder."


@pytest.mark.asyncio
async def test_text_to_speech_execution():
    adapter = VoiceAdapter()
    await adapter.initialize()
    task = CapabilityTask(task_id="voice-2", intent="text_to_speech", payload={"text": "Hello"})
    result = await adapter.execute(task)
    assert result.success is True
    assert result.data["message"] == "Text-to-speech placeholder."


@pytest.mark.asyncio
async def test_start_listening_execution():
    adapter = VoiceAdapter()
    await adapter.initialize()
    task = CapabilityTask(task_id="voice-3", intent="start_listening", payload={})
    result = await adapter.execute(task)
    assert result.success is True
    assert result.data["message"] == "Start listening placeholder."


@pytest.mark.asyncio
async def test_stop_listening_execution():
    adapter = VoiceAdapter()
    await adapter.initialize()
    task = CapabilityTask(task_id="voice-4", intent="stop_listening", payload={})
    result = await adapter.execute(task)
    assert result.success is True
    assert result.data["message"] == "Stop listening placeholder."


@pytest.mark.asyncio
async def test_wake_word_execution():
    adapter = VoiceAdapter()
    await adapter.initialize()
    task = CapabilityTask(task_id="voice-5", intent="wake_word", payload={})
    result = await adapter.execute(task)
    assert result.success is True
    assert result.data["message"] == "Wake word placeholder."


@pytest.mark.asyncio
async def test_shutdown():
    adapter = VoiceAdapter()
    await adapter.initialize()
    await adapter.shutdown()
    assert await adapter.health_check() is False