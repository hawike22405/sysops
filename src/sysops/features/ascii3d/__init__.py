"""CPU-based 3D ASCII/Unicode renderer foundation for SysOps."""

from .camera import Camera
from .depth import AIDepthGenerator, BrightnessDepthGenerator, DepthMode
from .geometry import Mesh
from .lighting import Light
from .mesh import generate_mesh_from_depth
from .viewer import Viewer, ViewerConfig

__all__ = [
    "AIDepthGenerator",
    "BrightnessDepthGenerator",
    "Camera",
    "DepthMode",
    "Light",
    "Mesh",
    "Viewer",
    "ViewerConfig",
    "generate_mesh_from_depth",
]
