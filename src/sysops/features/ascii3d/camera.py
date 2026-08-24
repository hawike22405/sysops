from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .geometry import Mat4, Vec3, identity, normalize


@dataclass
class Camera:
    position: Vec3 = field(default_factory=lambda: np.array([0.0, 0.0, 5.0], dtype=np.float64))
    target: Vec3 = field(default_factory=lambda: np.array([0.0, 0.0, 0.0], dtype=np.float64))
    fov_degrees: float = 60.0
    near: float = 0.1
    far: float = 100.0
    orthographic: bool = False

    def view_matrix(self) -> Mat4:
        raise NotImplementedError("Implement view matrix construction.")

    def projection_matrix(self, aspect: float) -> Mat4:
        raise NotImplementedError("Implement perspective/orthographic projection.")

    def orbit(self, yaw: float, pitch: float) -> None:
        raise NotImplementedError("Implement orbit controls.")

    def dolly(self, amount: float) -> None:
        raise NotImplementedError("Implement camera dolly/zoom.")
