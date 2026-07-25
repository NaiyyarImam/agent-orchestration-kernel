import pytest
from kernel.adapters.browser_adapter import BrowserAdapter
from kernel.interfaces.capability_adapter import CapabilityTask, CapabilityResult


def test_adapter_metadata():
    adapter = BrowserAdapter()
    assert adapter.name == "browser"
    assert adapter.capability_type == "browser"
    assert "browser" in adapter.description.lower()


@pytest.mark.asyncio
async def test_initialize_and_health_check():
    adapter = BrowserAdapter()
    assert await adapter.health_check() is False
    await adapter.initialize()
    assert await adapter.health_check() is True


def test_supported_intents():
    adapter = BrowserAdapter()
    for intent in [
        "browser",
        "browse",
        "web_search",
        "open_url",
        "extract_page",
        "scrape",
        "navigate",
    ]:
        assert adapter.supports(intent) is True


def test_unsupported_intent():
    adapter = BrowserAdapter()
    for intent in ["coding", "research", "voice"]:
        assert adapter.supports(intent) is False


@pytest.mark.asyncio
async def test_execute_requires_initialize():
    adapter = BrowserAdapter()
    task = CapabilityTask(
        task_id="browser-test-0",
        intent="web_search",
        payload={},
    )
    with pytest.raises(RuntimeError):
        await adapter.execute(task)


@pytest.mark.asyncio
async def test_web_search_execution():
    adapter = BrowserAdapter()
    await adapter.initialize()
    task = CapabilityTask(
        task_id="browser-test-1",
        intent="web_search",
        payload={"query": "JARVIS"},
    )
    result = await adapter.execute(task)
    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata.get("adapter") == "browser"
    assert result.data.get("intent") == "web_search"
    assert result.data.get("payload") == {"query": "JARVIS"}
    assert result.data.get("message") == "Web search placeholder."


@pytest.mark.asyncio
async def test_open_url_execution():
    adapter = BrowserAdapter()
    await adapter.initialize()
    task = CapabilityTask(
        task_id="browser-test-2",
        intent="open_url",
        payload={"url": "https://example.com"},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.metadata.get("adapter") == "browser"
    assert result.data.get("intent") == "open_url"
    assert result.data.get("payload") == {"url": "https://example.com"}
    assert result.data.get("message") == "Open URL placeholder."


@pytest.mark.asyncio
async def test_scrape_execution():
    adapter = BrowserAdapter()
    await adapter.initialize()
    task = CapabilityTask(
        task_id="browser-test-3",
        intent="scrape",
        payload={"url": "https://example.com"},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.metadata.get("adapter") == "browser"
    assert result.data.get("intent") == "scrape"
    assert result.data.get("payload") == {"url": "https://example.com"}
    assert result.data.get("message") == "Web scraping placeholder."


@pytest.mark.asyncio
async def test_shutdown():
    adapter = BrowserAdapter()
    await adapter.initialize()
    await adapter.shutdown()
    assert await adapter.health_check() is False