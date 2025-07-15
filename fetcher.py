# image_scraper/fetcher.py

async def fetch(session, url, retries, timeout):
    last_err = None
    for _ in range(retries):
        try:
            resp = await session.get(url, timeout=timeout)
            resp.raise_for_status()
            return await resp.text(), None
        except Exception as e:
            last_err = str(e)
    return None, last_err
