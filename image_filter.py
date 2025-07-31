"""
Downloads and filters images using OCR/logo detection.
Enhanced error handling and logging.
"""

import aiohttp
import io
from PIL import Image
from ocr_logo_detector import detect_logo_or_text
from utils import retry_with_backoff, load_config

class ImageFilter:
    def __init__(self, config):
        self.config = config

    @retry_with_backoff(
        max_retries=load_config()["MAX_RETRIES"],
        backoff=load_config()["RETRY_BACKOFF"]
    )
    async def process_image(self, image_info, config, ml_model=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_info['src'], timeout=20) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        try:
                            img = Image.open(io.BytesIO(content))
                        except Exception as e:
                            return False, None, "OPEN_ERROR"
                        flag_type = detect_logo_or_text(img, config, ml_model=ml_model)
                        if flag_type:
                            if config["DETECTION_MODE"].lower() == "flag":
                                return False, img, flag_type
                            elif config["DETECTION_MODE"].lower() == "erase":
                                return False, None, flag_type
                        return True, img, None
                    else:
                        return False, None, "HTTP_ERROR"
        except Exception as e:
            return False, None, "DOWNLOAD_ERROR"
        return False, None, None