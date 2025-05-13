from typing import Optional, Tuple
import cv2, pytesseract, numpy as np
from image_match import find_template_bboxes
TESS_CFG = "--psm 7 -c tessedit_char_whitelist=0123456789"
def ocr_roi(img: np.ndarray,
            bbox: Optional[Tuple[int, int, int, int]] = None,
            tess_cfg: str = TESS_CFG) -> str:
    if bbox is None:
        roi = img
    else:
        x1, y1, x2, y2 = bbox
        roi = img[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    th   = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    raw = pytesseract.image_to_string(th, config=tess_cfg)
    return "".join(filter(str.isprintable, raw)).strip()

if __name__ == '__main__':
    path = "./screen.png"
    screen = cv2.imread(path)
    if screen is None:
        raise FileNotFoundError(f"cannot open: {path}")
    banner_path = "./banners/100_banner.png"
    banner = cv2.imread(banner_path)
    if banner is None:
        raise FileNotFoundError(f"cannot open: {banner_path}")
    
    bboxes = find_template_bboxes(screen, banner)
    x1, y1, w, h = bboxes[0]
    x1 += 1000
    x2 = x1 + 600
    y2 = y1 + h
    bbox = [x1, y1, x2, y2]
    print(ocr_roi(banner))
    print(ocr_roi(screen, bbox))