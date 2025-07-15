# image_scraper/dynamic_fetcher.py
import threading
import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from urllib.parse import urljoin

# ←←← add this at the top
_selenium_lock = threading.Lock()

def fetch_all_images_with_selenium(page_url: str, needed: int = None) -> list[str]:
    """
    Advanced Selenium fallback:
      - up to `needed` URLs
      - scroll & click load-more
      - scrape <img> tags + srcset
      - click thumbnails & any [onclick]
      - scan CSS background-images
    """
    # acquire lock so we never spawn two browsers at once
    with _selenium_lock:
        opts = Options()
        opts.headless = True
        opts.add_argument('--ignore-certificate-errors')
        opts.add_argument('--allow-insecure-localhost')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-software-rasterizer')
        opts.add_argument('--no-sandbox')
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])

        try:
            driver = webdriver.Chrome(options=opts)
        except Exception as e:
            logging.warning(f"[Selenium] could not start Chrome: {e}")
            return []

        try:
            driver.get(page_url)
            time.sleep(1)

            # 1) Scroll & click “load more”
            for _ in range(5):
                prev = len(driver.find_elements(By.TAG_NAME, 'img'))
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                for sel in ('button.load-more', 'a.more', 'div.load-more'):
                    for el in driver.find_elements(By.CSS_SELECTOR, sel):
                        try:
                            el.click()
                            time.sleep(0.5)
                        except:
                            pass
                if needed and len(driver.find_elements(By.TAG_NAME, 'img')) >= needed:
                    break
                if len(driver.find_elements(By.TAG_NAME, 'img')) == prev:
                    break

            seen = set()
            urls = []
            bg_re = re.compile(r'url\(["\']?(.*?)["\']?\)')

            def add(u):
                if not u or u.lower().endswith('.svg'):
                    return False
                full = urljoin(page_url, u)
                if full in seen:
                    return False
                seen.add(full)
                urls.append(full)
                return True

            # 2) scrape <img> tags + srcset
            for img in driver.find_elements(By.TAG_NAME, 'img'):
                if add(img.get_attribute('src') or '') and needed and len(urls) >= needed:
                    return urls
                srcset = img.get_attribute('srcset') or ''
                for cand in (u.strip().split(' ')[0] for u in srcset.split(',')):
                    if add(cand) and needed and len(urls) >= needed:
                        return urls

            # 3) click thumbnails & onclicks
            thumbs     = driver.find_elements(By.CSS_SELECTOR, 'img.thumbnail, a.gallery-thumb')
            clickables = driver.find_elements(By.CSS_SELECTOR, '[onclick]')
            for el in thumbs + clickables:
                if needed and len(urls) >= needed:
                    break
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", el)
                    el.click()
                    time.sleep(1)
                    for img in driver.find_elements(By.TAG_NAME, 'img'):
                        if add(img.get_attribute('src') or '') and needed and len(urls) >= needed:
                            break
                        srcset = img.get_attribute('srcset') or ''
                        for cand in (u.strip().split(' ')[0] for u in srcset.split(',')):
                            if add(cand) and needed and len(urls) >= needed:
                                break
                except:
                    pass
                finally:
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass

            # 4) scan CSS background-images
            for el in driver.find_elements(By.CSS_SELECTOR, '*'):
                if needed and len(urls) >= needed:
                    break
                try:
                    bg = driver.execute_script(
                        "return window.getComputedStyle(arguments[0])"
                        ".getPropertyValue('background-image')",
                        el
                    ) or ''
                except:
                    continue
                for m in bg_re.findall(bg):
                    if add(m) and needed and len(urls) >= needed:
                        break

            return urls

        except Exception as e:
            logging.warning(f"[Selenium] fetch failed for {page_url}: {e}")
            return []

        finally:
            driver.quit()
