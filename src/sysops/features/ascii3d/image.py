from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


@dataclass
class PreprocessConfig:
    width: int = 120
    height: int | None = None
    crop: bool = True
    remove_background: bool = False
    normalize_contrast: bool = True


def preprocess(path: str | Path, config: PreprocessConfig = PreprocessConfig()) -> np.ndarray:
    image = Image.open(Path(path)).convert("RGBA")
    if config.crop:
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            image = image.crop(bbox)
    if config.width > 0:
        target_height = config.height or max(1, round(image.height * config.width / max(image.width, 1)))
        image = image.resize((config.width, target_height), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(image)
    if config.normalize_contrast:
        gray = ImageOps.autocontrast(gray)
    return np.asarray(gray, dtype=np.float64) / 255.0
