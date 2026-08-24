from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


@dataclass
class PreprocessConfig:
    width: int = 50
    height: int | None = None
    crop: bool = True
    remove_background: bool = False
    normalize_contrast: bool = True


def _load_and_resize(path: str | Path, config: PreprocessConfig) -> Image.Image:
    image = Image.open(Path(path)).convert("RGBA")
    if config.crop:
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            image = image.crop(bbox)
    if config.width > 0:
        target_height = config.height or max(1, round(image.height * config.width / max(image.width, 1)))
        image = image.resize((config.width, target_height), Image.Resampling.LANCZOS)
    return image


def preprocess(path: str | Path, config: PreprocessConfig = PreprocessConfig()) -> np.ndarray:
    image = _load_and_resize(path, config)
    gray = ImageOps.grayscale(image)
    if config.normalize_contrast:
        gray = ImageOps.autocontrast(gray)
    return np.asarray(gray, dtype=np.float64) / 255.0


def preprocess_color(path: str | Path, config: PreprocessConfig = PreprocessConfig()) -> tuple[np.ndarray, np.ndarray]:
    """Return (grayscale_float64_0to1, rgb_uint8) arrays for the same resized image."""
    image = _load_and_resize(path, config)
    rgb = image.convert("RGB")
    gray = ImageOps.grayscale(image)
    if config.normalize_contrast:
        gray = ImageOps.autocontrast(gray)
    return np.asarray(gray, dtype=np.float64) / 255.0, np.asarray(rgb, dtype=np.uint8)
