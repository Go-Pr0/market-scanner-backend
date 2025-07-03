import asyncio
import re
from playwright.async_api import async_playwright

async def extract_total3_marketcap_stealth():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled"
        ])

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )

        page = await context.new_page()

        # Block resources that aren't needed
        async def block_unwanted(route):
            if route.request.resource_type in ["image", "stylesheet", "font"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_unwanted)

        # Navigate slowly to mimic human behavior
        await page.goto("https://www.tradingview.com/symbols/TOTAL3/technicals/", timeout=30000, wait_until="load")
        await asyncio.sleep(3)  # slight wait to simulate user pause

        # Wait for a stable element that always appears when data is ready
        await page.wait_for_selector("text=Summary", timeout=15000)

        # Mask some JS-level automation flags (navigator.webdriver etc.)
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """)

        # Extract all visible text from the body
        text_content = await page.locator("body").inner_text()

        # Regex to find market cap value like 824.55 B or 1.2 B
        match = re.search(r"(\d{1,3}(?:[.,]\d{1,3})?)\s*[\u202f ]?B", text_content)
        if match:
            market_cap = match.group(0).replace("\u202f", "").strip()
            print(f"✅ TOTAL3 Market Cap: {market_cap}")
        else:
            print("❌ Market cap not found.")

        await browser.close()

# Run the stealth scraper
asyncio.run(extract_total3_marketcap_stealth())
