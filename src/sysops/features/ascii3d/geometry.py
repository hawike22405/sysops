from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

Vec3 = np.ndarray
Vec2 = np.ndarray
Mat4 = np.ndarray


def vec3(x: float, y: float, z: float) -> Vec3:
    return np.array([x, y, z], dtype=np.float64)


def normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm < 1e-12:
        return v
    return v / norm


def identity() -> Mat4:
    return np.eye(4, dtype=np.float64)


def translation(x: float, y: float, z: float) -> Mat4:
    m = identity()
    m[0, 3], m[1, 3], m[2, 3] = x, y, z
    return m


def scale(x: float, y: float, z: float) -> Mat4:
    m = identity()
    m[0, 0], m[1, 1], m[2, 2] = x, y, z
    return m


def rotation_x(radians: float) -> Mat4:
    c, s = np.cos(radians), np.sin(radians)
    m = identity()
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def rotation_y(radians: float) -> Mat4:
    c, s = np.cos(radians), np.sin(radians)
    m = identity()
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def rotation_z(radians: float) -> Mat4:
    c, s = np.cos(radians), np.sin(radians)
    m = identity()
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def transform_point(m: Mat4, p: Vec3) -> Vec3:
    result = m @ np.array([p[0], p[1], p[2], 1.0])
    w = result[3] if abs(result[3]) > 1e-12 else 1.0
    return result[:3] / w


def transform_direction(m: Mat4, d: Vec3) -> Vec3:
    return (m @ np.array([d[0], d[1], d[2], 0.0]))[:3]


@dataclass
class Triangle:
    i0: int
    i1: int
    i2: int
    normal: Optional[Vec3] = None


@dataclass
class Mesh:
    vertices: np.ndarray
    faces: np.ndarray
    normals: Optional[np.ndarray] = None
    uvs: Optional[np.ndarray] = None
    colors: Optional[np.ndarray] = None

    def vertex_count(self) -> int:
        return self.vertices.shape[0]

    def face_count(self) -> int:
        return self.faces.shape[0]

    def compute_face_normal(self, face_index: int) -> Vec3:
        i0, i1, i2 = self.faces[face_index]
        a, b, c = self.vertices[i0], self.vertices[i1], self.vertices[i2]
        return normalize(np.cross(b - a, c - a))

    def compute_vertex_normals(self) -> np.ndarray:
        raise NotImplementedError("Implement per-vertex normal accumulation.")
