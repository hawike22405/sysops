from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

import numpy as np


class DepthMode(Enum):
    NORMAL = auto()
    INVERTED = auto()


class DepthGenerator(ABC):
    @abstractmethod
    def generate(self, grayscale: np.ndarray) -> np.ndarray:
        raise NotImplementedError


@dataclass
class BrightnessDepthGenerator(DepthGenerator):
    mode: DepthMode = DepthMode.NORMAL

    def generate(self, grayscale: np.ndarray) -> np.ndarray:
        depth = grayscale if self.mode is DepthMode.NORMAL else 1.0 - grayscale
        depth = np.clip(depth, 0.0, 1.0)
        
        # One pass of 3x3 box blur for a smoother, Gaussian-like effect
        for _ in range(1):
            depth = (
                depth +
                np.roll(depth, 1, axis=0) + np.roll(depth, -1, axis=0) +
                np.roll(depth, 1, axis=1) + np.roll(depth, -1, axis=1) +
                np.roll(np.roll(depth, 1, axis=0), 1, axis=1) +
                np.roll(np.roll(depth, -1, axis=0), 1, axis=1) +
                np.roll(np.roll(depth, 1, axis=0), -1, axis=1) +
                np.roll(np.roll(depth, -1, axis=0), -1, axis=1)
            ) / 9.0
        
        return np.clip(depth, 0.0, 1.0)


@dataclass
class AIDepthGenerator(DepthGenerator):
    model_path: str | None = None

    def generate(self, grayscale: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Wire up a monocular depth model behind this interface.")


def apply_depth_scale(depth: np.ndarray, depth_scale: float) -> np.ndarray:
    return depth * depth_scale