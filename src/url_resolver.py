import asyncio
import random
from typing import Callable, Optional

from playwright.async_api import Browser, async_playwright


class URLResolutionError(Exception):
    pass


class RateLimiter:
    def __init__(self, min_delay: float, max_delay: float):
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def wait(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)


class ExponentialBackoff:
    def __init__(self, max_retries: int, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    wait_time = (2**attempt) * self.base_delay + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)
        raise URLResolutionError(
            f"All {self.max_retries} retries failed: {last_exc}"
        ) from last_exc


class URLResolver:
    def __init__(
        self,
        headless: bool = True,
        max_concurrent: int = 5,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        max_retries: int = 3,
        timeout: int = 30000,
    ):
        self.headless = headless
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._rate_limiter = RateLimiter(min_delay, max_delay)
        self._backoff = ExponentialBackoff(max_retries)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def __aenter__(self) -> "URLResolver":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _do_resolve(self, redirect_url: str) -> tuple[str, Optional[str]]:
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            page = await context.new_page()
            await self._rate_limiter.wait()
            await page.goto(
                redirect_url, wait_until="networkidle", timeout=self.timeout
            )
            final_url = page.url
            html_content = await page.content()
            return final_url, html_content
        finally:
            await context.close()

    async def resolve_url(self, redirect_url: str) -> tuple[str, Optional[str]]:
        async with self._semaphore:
            return await self._backoff.execute_with_retry(
                self._do_resolve, redirect_url
            )

    async def resolve_batch(
        self,
        urls: list[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> list[tuple[str, Optional[str]]]:
        completed = 0
        total = len(urls)
        results = [None] * total
        lock = asyncio.Lock()

        async def resolve_one(i: int, url: str):
            nonlocal completed
            try:
                result = await self.resolve_url(url)
            except URLResolutionError as e:
                result = (url, None)
                print(f"[url_resolver] Failed to resolve {url}: {e}")
            results[i] = result
            async with lock:
                completed += 1
                if progress_callback:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(total, completed, url)
                    else:
                        progress_callback(total, completed, url)

        await asyncio.gather(*[resolve_one(i, url) for i, url in enumerate(urls)])
        return results
