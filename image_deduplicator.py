"""
Deduplicates images by hash, preferring largest pixel area for duplicates.
Works with both PIL Image objects and file paths robustly.
"""

import hashlib
from PIL import Image
import os

class ImageDeduplicator:
    def __init__(self, config):
        self.config = config
        self.hashes = {}

    def is_unique(self, img):
        try:
            if isinstance(img, Image.Image):
                img_bytes = img.tobytes()
                area = img.width * img.height
            elif isinstance(img, str) and os.path.isfile(img):
                with open(img, "rb") as f:
                    img_bytes = f.read()
                try:
                    with Image.open(img) as im:
                        area = im.width * im.height
                except Exception:
                    area = 0
            else:
                return False
            img_hash = hashlib.md5(img_bytes).hexdigest()
            if img_hash in self.hashes:
                if area > self.hashes[img_hash][0]:
                    self.hashes[img_hash] = (area, img)
                    return True
                return False
            self.hashes[img_hash] = (area, img)
            return True
        except Exception as e:
            print(f"[Deduplicator] Error deduplicating image: {e}")
            return False