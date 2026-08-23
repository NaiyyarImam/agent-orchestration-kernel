"""Playwright-backed implementation of the BrowserBackend interface."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import asyncio

from kernel.interfaces.browser_backend import BrowserResult

if TYPE_CHECKING:
    from playwright.async_api import Playwright, Browser, BrowserContext, Page, ViewportSize


class PlaywrightBackend:
    """Playwright implementation of the BrowserBackend protocol.

    Encapsulates Playwright completely; only this class depends on Playwright.
    """

    def __init__(
        self,
        *,
        browser_type: str = "chromium",
        headless: bool = True,
        timeout: float = 30.0,
        navigation_timeout: float = 30.0,
        viewport: Optional["ViewportSize"] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self._browser_type = browser_type
        self._headless = headless
        self._timeout = timeout
        self._navigation_timeout = navigation_timeout
        self._viewport = viewport or {"width": 1280, "height": 720}
        self._user_agent = user_agent

        self._playwright: "Playwright | None" = None
        self._browser: "Browser | None" = None
        self._context: "BrowserContext | None" = None
        self._page: "Page | None" = None
        self._initialized = False

    async def initialize(self) -> None:
        """Start Playwright, launch browser, create context and page."""
        if self._initialized:
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed. Run 'pip install playwright' and 'playwright install chromium'.") from exc

        self._playwright = await async_playwright().start()
        browser_launcher = getattr(self._playwright, self._browser_type)
        self._browser = await browser_launcher.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            viewport=self._viewport,
            user_agent=self._user_agent,
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(int(self._timeout * 1000))
        self._page.set_default_navigation_timeout(int(self._navigation_timeout * 1000))
        self._initialized = True

    async def shutdown(self) -> None:
        """Close page, context, browser, and stop Playwright."""
        errors: list[str] = []

        if self._page is not None:
            try:
                await self._page.close()
            except Exception as exc:
                errors.append(f"page close: {exc}")
            finally:
                self._page = None

        if self._context is not None:
            try:
                await self._context.close()
            except Exception as exc:
                errors.append(f"context close: {exc}")
            finally:
                self._context = None

        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception as exc:
                errors.append(f"browser close: {exc}")
            finally:
                self._browser = None

        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception as exc:
                errors.append(f"playwright stop: {exc}")
            finally:
                self._playwright = None

        self._initialized = False

        if errors:
            raise RuntimeError(f"Shutdown errors: {'; '.join(errors)}")

    async def health_check(self) -> bool:
        """Return True if the browser is responsive."""
        if not self._initialized or self._page is None:
            return False
        try:
            await self._page.evaluate("1 + 1")
            return True
        except Exception:
            return False

    async def navigate(self, url: str, *, timeout: Optional[float] = None) -> BrowserResult:
        """Navigate to a URL and return the result."""
        if not self._initialized or self._page is None:
            return BrowserResult(success=False, error="Backend not initialized")

        if not url or not isinstance(url, str):
            return BrowserResult(success=False, error="Invalid URL")

        if not (url.startswith("http://") or url.startswith("https://")):
            return BrowserResult(success=False, error="URL must start with http:// or https://")

        try:
            nav_timeout = int(timeout * 1000) if timeout is not None else int(self._navigation_timeout * 1000)
            response = await self._page.goto(url, wait_until="domcontentloaded", timeout=nav_timeout)
            title = await self._page.title()
            final_url = self._page.url
            status = response.status if response else 0

            if status >= 400:
                return BrowserResult(
                    success=False,
                    url=final_url,
                    title=title,
                    error=f"Navigation failed with status {status}",
                )

            return BrowserResult(
                success=True,
                url=final_url,
                title=title,
                content=None,
            )
        except asyncio.TimeoutError:
            return BrowserResult(success=False, error=f"Navigation timeout after {timeout or self._navigation_timeout}s")
        except Exception as exc:
            return BrowserResult(success=False, error=f"Navigation failed: {exc}")

    async def search(self, query: str, *, limit: int = 10, timeout: Optional[float] = None) -> BrowserResult:
        """Perform a web search using a search engine and extract results."""
        if not self._initialized or self._page is None:
            return BrowserResult(success=False, error="Backend not initialized")

        if not query or not isinstance(query, str):
            return BrowserResult(success=False, error="Invalid query")

        search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        nav_result = await self.navigate(search_url, timeout=timeout)
        if not nav_result.success:
            return nav_result

        try:
            results = await self._page.evaluate(
                f"""() => {{
                    const items = Array.from(document.querySelectorAll('li.b_algo'));
                    return items.slice(0, {limit}).map(item => {{
                        const link = item.querySelector('h2 a');
                        const snippet = item.querySelector('.b_caption p');
                        return {{
                            title: link ? link.innerText : '',
                            url: link ? link.href : '',
                            snippet: snippet ? snippet.innerText : '',
                        }};
                    }});
                }}"""
            )
            return BrowserResult(
                success=True,
                url=nav_result.url,
                title=f"Search results for: {query}",
                content=str(results),
                data={"results": results, "query": query},
            )
        except Exception as exc:
            return BrowserResult(success=False, error=f"Search extraction failed: {exc}")

    async def extract(self, selector: Optional[str] = None) -> BrowserResult:
        """Extract content from the current page."""
        if not self._initialized or self._page is None:
            return BrowserResult(success=False, error="Backend not initialized")

        try:
            if selector is None:
                content = await self._page.evaluate(
                    """() => document.body ? document.body.innerText : ''"""
                )
            else:
                try:
                    content = await self._page.locator(selector).first.inner_text(timeout=5000)
                except Exception:
                    elements = await self._page.locator(selector).all_inner_texts()
                    content = "\n".join(elements)

            url = self._page.url
            title = await self._page.title()

            return BrowserResult(
                success=True,
                url=url,
                title=title,
                content=content,
            )
        except Exception as exc:
            return BrowserResult(success=False, error=f"Extraction failed: {exc}")

    async def screenshot(self, *, full_page: bool = False) -> BrowserResult:
        """Capture a screenshot of the current page."""
        if not self._initialized or self._page is None:
            return BrowserResult(success=False, error="Backend not initialized")

        try:
            screenshot_bytes = await self._page.screenshot(full_page=full_page)
            return BrowserResult(
                success=True,
                url=self._page.url,
                title=await self._page.title(),
                data={"screenshot": screenshot_bytes, "full_page": full_page},
            )
        except Exception as exc:
            return BrowserResult(success=False, error=f"Screenshot failed: {exc}")