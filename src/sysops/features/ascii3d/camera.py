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
        forward = normalize(self.target - self.position)
        if np.linalg.norm(forward) < 1e-12:
            forward = np.array([0.0, 0.0, -1.0], dtype=np.float64)

        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        if abs(float(np.dot(forward, world_up))) > 0.999:
            world_up = np.array([1.0, 0.0, 0.0], dtype=np.float64)

        right = normalize(np.cross(forward, world_up))
        up = normalize(np.cross(right, forward))

        view = identity()
        view[0, :3] = right
        view[1, :3] = up
        view[2, :3] = -forward
        view[0, 3] = -float(np.dot(right, self.position))
        view[1, 3] = -float(np.dot(up, self.position))
        view[2, 3] = float(np.dot(forward, self.position))
        return view

    def projection_matrix(self, aspect: float) -> Mat4:
        if aspect <= 0:
            raise ValueError("aspect must be greater than 0")
        if self.near <= 0 or self.far <= self.near:
            raise ValueError("near must be > 0 and far must be > near")

        if self.orthographic:
            scale = max(1.0, np.tan(np.deg2rad(self.fov_degrees) * 0.5) * self.position.size)
            half_h = scale
            half_w = half_h * aspect
            projection = np.zeros((4, 4), dtype=np.float64)
            projection[0, 0] = 1.0 / half_w
            projection[1, 1] = 1.0 / half_h
            projection[2, 2] = -2.0 / (self.far - self.near)
            projection[2, 3] = -(self.far + self.near) / (self.far - self.near)
            projection[3, 3] = 1.0
            return projection

        f = 1.0 / np.tan(np.deg2rad(self.fov_degrees) * 0.5)
        projection = np.zeros((4, 4), dtype=np.float64)
        projection[0, 0] = f / aspect
        projection[1, 1] = f
        projection[2, 2] = (self.far + self.near) / (self.near - self.far)
        projection[2, 3] = (2.0 * self.far * self.near) / (self.near - self.far)
        projection[3, 2] = -1.0
        return projection

    def orbit(self, yaw: float, pitch: float) -> None:
        offset = self.position - self.target
        radius = float(np.linalg.norm(offset))
        if radius < 1e-9:
            radius = 5.0
        theta = np.arctan2(offset[0], offset[2]) + yaw
        phi = np.arcsin(np.clip(offset[1] / radius, -1.0, 1.0)) + pitch
        limit = np.deg2rad(89.0)
        phi = float(np.clip(phi, -limit, limit))
        cos_phi = np.cos(phi)
        self.position = self.target + np.array(
            [radius * np.sin(theta) * cos_phi, radius * np.sin(phi), radius * np.cos(theta) * cos_phi],
            dtype=np.float64,
        )

    def dolly(self, amount: float) -> None:
        direction = normalize(self.target - self.position)
        new_position = self.position + direction * amount
        distance = float(np.linalg.norm(self.target - new_position))
        if distance < 0.5:
            new_position = self.target - direction * 0.5
        self.position = new_position
