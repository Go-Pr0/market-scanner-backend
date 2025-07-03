from playwright.async_api import async_playwright
import asyncio
import re
import logging
from typing import Optional

# Setup logging specific to this module
logger = logging.getLogger("total3_scraper")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def fetch_total3_market_cap(timeout: int = 30_000) -> Optional[float]:
    """Fetch the TOTAL3 market-cap in billions (numeric value).

    This function launches a headless Chromium browser via Playwright, navigates to
    TradingView's TOTAL3 technicals page, and extracts the market-cap figure that is
    normally displayed with a trailing "B" (for billions).  Only the numeric part is
    returned as a float.

    Args:
        timeout (int): Page-load timeout in milliseconds. Defaults to 30 s.

    Returns:
        Optional[float]: Market-cap in billions, or ``None`` if extraction failed.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )

            # Intercept and abort unneeded resources.
            async def block_unwanted(route):
                if route.request.resource_type in {"image", "stylesheet", "font"}:
                    await route.abort()
                else:
                    await route.continue_()

            await context.route("**/*", block_unwanted)
            page = await context.new_page()

            await page.goto(
                "https://www.tradingview.com/symbols/TOTAL3/technicals/",
                timeout=timeout,
                wait_until="load",
            )

            # Brief human-like pause.
            await asyncio.sleep(3)

            # Wait for a stable selector that indicates data is rendered.
            await page.wait_for_selector("text=Summary", timeout=15_000)

            # Hardening against detection.
            await page.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                """
            )

            # Extract full visible text and look for the market-cap pattern.
            text_content = await page.locator("body").inner_text()
            match = re.search(r"(\d{1,3}(?:[.,]\d{1,3})?)\s*[\u202f ]?B", text_content)
            if not match:
                logger.warning("TOTAL3 market-cap value not found in page text.")
                return None

            raw_val = match.group(1)
            # Normalise number: replace comma with empty string, use dot as decimal point.
            normalised = raw_val.replace("\u202f", "").replace(",", "")
            try:
                return float(normalised)
            except ValueError:
                logger.error(f"Failed to parse market-cap value '{raw_val}' as float.")
                return None

    except Exception as e:
        logger.error(f"Error while fetching TOTAL3 market-cap: {e}")
        return None 