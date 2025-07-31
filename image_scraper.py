import asyncio
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from utils import log_failure

class ImageScraper:
    def __init__(self, config):
        self.config = config

    async def scrape_images(self, website, row, config):
        row_num = int(row['Row'])
        activity_id = row['ActivityId']
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=config["HEADLESS"])
                page = await browser.new_page(ignore_https_errors=True)
                try:
                    await page.goto(website, timeout=120000, wait_until="domcontentloaded")
                    await page.wait_for_selector("img", timeout=30000)
                    # Scroll to load images
                    await page.evaluate("""async () => {
                        for (let i = 0; i < 10; i++) {
                            window.scrollBy(0, document.body.scrollHeight);
                            await new Promise(r => setTimeout(r, 1000));
                        }
                    }""")
                    # Collect all image src attributes
                    srcs = await page.eval_on_selector_all("img[src]", "elements => elements.map(e => e.src)")
                    for src in srcs:
                        yield {"src": src}
                finally:
                    await page.close()
                    await browser.close()
        except PlaywrightTimeoutError as e:
            log_failure(config, row_num, activity_id, f"SCRAPER_TIMEOUT:{e}")
        except Exception as e:
            log_failure(config, row_num, activity_id, f"SCRAPER_ERROR:{type(e).__name__}")

