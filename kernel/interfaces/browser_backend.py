"""Browser backend interface for the JARVIS Kernel.

Defines the port that every browser automation backend must implement.
The Kernel depends only on this interface; concrete backends are constructed
by the composition root and injected into the BrowserAdapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class BrowserResult:
    """Result returned by a browser backend operation."""
    success: bool
    url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


@runtime_checkable
class BrowserBackend(Protocol):
    """Port implemented by every browser automation backend.

    Only the operations actually required by BrowserAdapter are defined.
    Backends are constructed by the composition root (Bootstrap) and injected
    into BrowserAdapter; the adapter never instantiates a backend itself.
    """

    async def initialize(self) -> None:
        """Prepare backend resources (launch browser, create context)."""

    async def shutdown(self) -> None:
        """Release backend resources (close browser, stop playwright)."""

    async def health_check(self) -> bool:
        """Return backend health status."""

    async def navigate(self, url: str, *, timeout: Optional[float] = None) -> BrowserResult:
        """Navigate to a URL."""

    async def search(self, query: str, *, limit: int = 10, timeout: Optional[float] = None) -> BrowserResult:
        """Perform a web search and return structured results."""

    async def extract(self, selector: Optional[str] = None) -> BrowserResult:
        """Extract content from the current page. If selector is None, extract visible text."""

    async def screenshot(self, *, full_page: bool = False) -> BrowserResult:
        """Capture a screenshot of the current page."""