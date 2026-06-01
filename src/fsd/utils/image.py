"""Image loading and CelebA-Spoof bounding-box face cropping.

Each CelebA-Spoof image has a sibling ``<name>_BB.txt`` containing a single line:

    x y w h score

The coordinates are expressed against a 224-pixel reference frame, so they are
rescaled to the real image size before cropping. This logic mirrors the official
``client.py`` ``read_image`` routine so model inputs match the published benchmark.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

BBOX_REFERENCE = 224.0


def bbox_path_for(image_path: str | Path) -> Path:
    p = Path(image_path)
    return p.with_name(p.stem + "_BB.txt")


def load_bbox(image_path: str | Path) -> tuple[int, int, int, int, float] | None:
    """Read ``<name>_BB.txt`` -> (x, y, w, h, score) in 224-reference space.

    Returns None when the file is missing or malformed.
    """
    bb = bbox_path_for(image_path)
    if not bb.exists():
        return None
    try:
        line = bb.read_text(encoding="utf-8", errors="ignore").strip()
        x, y, w, h, score = line.split(" ")[:5]
        return int(float(x)), int(float(y)), int(float(w)), int(float(h)), float(score)
    except (ValueError, IndexError):
        return None


def crop_face_bbox(img_bgr: np.ndarray, bbox: tuple[int, int, int, int, float] | None) -> np.ndarray:
    """Crop the face region from a BGR image using a 224-reference bbox.

    Falls back to the full frame when bbox is None. Returns a BGR crop.
    """
    if bbox is None:
        return img_bgr
    real_h, real_w = img_bgr.shape[:2]
    x, y, w, h, _ = bbox

    sx = real_w / BBOX_REFERENCE
    sy = real_h / BBOX_REFERENCE
    x = int(x * sx)
    y = int(y * sy)
    w = int(w * sx)
    h = int(h * sy)

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(real_w, x + w)
    y2 = min(real_h, y + h)
    if x2 <= x1 or y2 <= y1:
        return img_bgr
    return img_bgr[y1:y2, x1:x2, :]


def read_image_rgb(image_path: str | Path, *, crop: bool = True) -> np.ndarray:
    """Read an image and return an RGB uint8 array, optionally BB-cropped to the face.

    Raises FileNotFoundError when the image cannot be read.
    """
    image_path = Path(image_path)
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    if crop:
        img = crop_face_bbox(img, load_bbox(image_path))
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
