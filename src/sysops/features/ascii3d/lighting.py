from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .geometry import Vec3, normalize

DEFAULT_ASCII_RAMP = " .:-=+*#%@"


@dataclass
class Light:
    direction: Vec3 = field(
        default_factory=lambda: np.array([0.4, 0.6, 1.0], dtype=np.float64)
    )
    ambient: float = 0.15

    def normalized_direction(self) -> Vec3:
        return normalize(self.direction)


def face_brightness(normal: Vec3, light: Light) -> float:
    n = normalize(normal)
    l = normalize(light.direction)
    diffuse = max(0.0, float(np.dot(n, l)))
    return max(0.0, min(1.0, float(light.ambient) + (1.0 - float(light.ambient)) * diffuse))


def brightness_to_char(brightness: float, ramp: str = DEFAULT_ASCII_RAMP) -> str:
    if not ramp:
        return " "
    value = max(0.0, min(1.0, float(brightness)))
    index = min(len(ramp) - 1, int(value * (len(ramp) - 1)))
    return ramp[index]
