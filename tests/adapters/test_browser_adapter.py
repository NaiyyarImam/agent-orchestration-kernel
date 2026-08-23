import pytest
from kernel.adapters.browser_adapter import BrowserAdapter
from kernel.interfaces.browser_backend import BrowserBackend, BrowserResult
from kernel.interfaces.capability_adapter import CapabilityTask, CapabilityResult


class FakeBrowserBackend:
    """Fake browser backend for testing."""

    def __init__(self) -> None:
        self._initialized = False
        self.calls: list[dict[str, Any]] = []

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    async def health_check(self) -> bool:
        return self._initialized

    async def navigate(self, url: str, *, timeout: Optional[float] = None) -> BrowserResult:
        self.calls.append({"method": "navigate", "url": url, "timeout": timeout})
        return BrowserResult(success=True, url=url, title="Test Page", content="Test content")

    async def search(self, query: str, *, limit: int = 10, timeout: Optional[float] = None) -> BrowserResult:
        self.calls.append({"method": "search", "query": query, "limit": limit, "timeout": timeout})
        return BrowserResult(
            success=True,
            url="https://www.bing.com/search?q=test",
            title=f"Search results for: {query}",
            content="Test results",
            data={"results": [{"title": "Test", "url": "https://example.com", "snippet": "Test snippet"}]},
        )

    async def extract(self, selector: Optional[str] = None) -> BrowserResult:
        self.calls.append({"method": "extract", "selector": selector})
        return BrowserResult(success=True, url="https://example.com", title="Test Page", content="Extracted content")

    async def screenshot(self, *, full_page: bool = False) -> BrowserResult:
        self.calls.append({"method": "screenshot", "full_page": full_page})
        return BrowserResult(success=True, data={"screenshot": b"fake", "full_page": full_page})


from typing import Any, Optional


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
    backend = FakeBrowserBackend()
    adapter = BrowserAdapter(backend=backend)
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
    assert result.data.get("url") == "https://www.bing.com/search?q=test"
    assert result.data.get("title") == "Search results for: JARVIS"


@pytest.mark.asyncio
async def test_open_url_execution():
    backend = FakeBrowserBackend()
    adapter = BrowserAdapter(backend=backend)
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
    assert result.data.get("url") == "https://example.com"
    assert result.data.get("title") == "Test Page"


@pytest.mark.asyncio
async def test_scrape_execution():
    backend = FakeBrowserBackend()
    adapter = BrowserAdapter(backend=backend)
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
    assert result.data.get("content") == "Extracted content"


@pytest.mark.asyncio
async def test_extract_page_execution():
    backend = FakeBrowserBackend()
    adapter = BrowserAdapter(backend=backend)
    await adapter.initialize()
    task = CapabilityTask(
        task_id="browser-test-4",
        intent="extract_page",
        payload={},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.data.get("intent") == "extract_page"


@pytest.mark.asyncio
async def test_navigate_execution():
    backend = FakeBrowserBackend()
    adapter = BrowserAdapter(backend=backend)
    await adapter.initialize()
    task = CapabilityTask(
        task_id="browser-test-5",
        intent="navigate",
        payload={"url": "https://example.com"},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.data.get("intent") == "navigate"


@pytest.mark.asyncio
async def test_backend_failure():
    """Test that backend failures are properly reported."""
    class FailingBackend:
        async def initialize(self) -> None: pass
        async def shutdown(self) -> None: pass
        async def health_check(self) -> bool: return True
        async def navigate(self, url: str, *, timeout: Optional[float] = None) -> BrowserResult:
            return BrowserResult(success=False, error="Navigation failed")
        async def search(self, query: str, *, limit: int = 10, timeout: Optional[float] = None) -> BrowserResult:
            return BrowserResult(success=False, error="Search failed")
        async def extract(self, selector: Optional[str] = None) -> BrowserResult:
            return BrowserResult(success=False, error="Extract failed")
        async def screenshot(self, *, full_page: bool = False) -> BrowserResult:
            return BrowserResult(success=False, error="Screenshot failed")

    backend = FailingBackend()
    adapter = BrowserAdapter(backend=backend)
    await adapter.initialize()

    task = CapabilityTask(task_id="test", intent="web_search", payload={"query": "test"})
    result = await adapter.execute(task)
    assert result.success is False
    assert "Search failed" in result.error


@pytest.mark.asyncio
async def test_missing_backend():
    """Test that missing backend returns error."""
    adapter = BrowserAdapter(backend=None)
    await adapter.initialize()

    task = CapabilityTask(task_id="test", intent="web_search", payload={"query": "test"})
    result = await adapter.execute(task)
    assert result.success is False
    assert "not configured" in result.error


@pytest.mark.asyncio
async def test_shutdown():
    backend = FakeBrowserBackend()
    adapter = BrowserAdapter(backend=backend)
    await adapter.initialize()
    await adapter.shutdown()
    assert await adapter.health_check() is False