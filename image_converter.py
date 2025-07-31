"""
Converts images (SVG, WebP, .tmp, and others) to PNG using Pillow and cairosvg.
Leaves standard raster images unchanged for efficiency.
Enhanced error handling and logging.
"""

from PIL import Image
import os
import cairosvg

class ImageConverter:
    def __init__(self, config):
        self.config = config

    def ensure_png(self, img, original_src=None):
        try:
            if isinstance(img, Image.Image):
                return img
            elif isinstance(img, str):
                ext = os.path.splitext(img)[-1].lower()
                standard_formats = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
                if ext in standard_formats:
                    return img
                elif ext == ".webp":
                    im = Image.open(img).convert("RGBA")
                    out_path = img.rsplit('.', 1)[0] + ".png"
                    im.save(out_path, "PNG")
                    return out_path
                elif ext == ".svg" or ext == ".tmp":
                    out_path = img.rsplit('.', 1)[0] + ".png"
                    try:
                        cairosvg.svg2png(url=img, write_to=out_path)
                        return out_path
                    except Exception:
                        pass
                try:
                    im = Image.open(img)
                    out_path = img.rsplit('.', 1)[0] + ".png"
                    im.save(out_path, "PNG")
                    return out_path
                except Exception as e:
                    print(f"[ImageConverter] Could not convert {img} to PNG: {e}")
                    return img
            else:
                return img
        except Exception as e:
            print(f"[ImageConverter] Unexpected error: {e}")
            return img