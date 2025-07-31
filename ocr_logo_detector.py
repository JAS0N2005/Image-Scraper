"""
Logo and Text Detection Module

Supports classical (OpenCV, skimage) and ML-based (TFLite/ONNX) detection of logos and text in images.
"""

from PIL import Image
import pytesseract
import numpy as np
from skimage.color import rgb2gray
from skimage.filters import sobel
import cv2

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def load_ml_model(config):
    if config["LOGO_DETECTION_BACKEND"] == "ml" and config.get("LOGO_MODEL_PATH"):
        import tensorflow as tf
        interpreter = tf.lite.Interpreter(model_path=config["LOGO_MODEL_PATH"])
        interpreter.allocate_tensors()
        return interpreter
    return None

def predict_logo_ml(img: Image.Image, interpreter):
    import numpy as np
    img = img.resize((224, 224)).convert("RGB")
    arr = np.array(img, dtype=np.float32)[None, ...] / 255.0
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]['index'], arr)
    interpreter.invoke()
    out = interpreter.get_tensor(output_details[0]['index'])
    if out[0][0] > 0.5:
        return True
    return False

def detect_logo_or_text(img: Image.Image, config, ml_model=None):
    text = pytesseract.image_to_string(img)
    if len(text.strip()) > 10:
        return "TEXT"
    if config["LOGO_DETECTION_BACKEND"] == "ml" and ml_model is not None:
        if predict_logo_ml(img, ml_model):
            return "LOGO"
    arr = np.array(img.convert("RGB"))
    colors = len(np.unique(arr.reshape(-1, arr.shape[2]), axis=0))
    if config["LOGO_DETECTION_BACKEND"] == "opencv":
        cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) < 10 and colors < 8:
            return "LOGO"
    try:
        gray = rgb2gray(arr)
        edges = sobel(gray)
        edge_density = np.mean(edges > 0.15)
        if edge_density > 0.15 and colors < 32:
            return "LOGO"
    except Exception:
        pass
    return None