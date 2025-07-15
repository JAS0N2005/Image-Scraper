# image_scraper/downloader.py

import io
from PIL import Image
import os

def blocking_save(content, path, min_size):
    try:
        img = Image.open(io.BytesIO(content))
    except Exception as e:
        return False, f'pil_error:{e}'
    if img.width < min_size[0] or img.height < min_size[1]:
        return False, 'too_small'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, 'wb') as f:
            f.write(content)
    except Exception as e:
        return False, f'fs_error:{e}'
    return True, ''

async def download_image(session, url, path, min_size, timeout, loop):
    try:
        async with session.get(url, timeout=timeout) as resp:
            resp.raise_for_status()
            content = await resp.read()
            return await loop.run_in_executor(None, blocking_save, content, path, min_size)
    except Exception as e:
        return False, str(e)
