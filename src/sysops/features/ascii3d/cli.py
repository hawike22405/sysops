from __future__ import annotations

import argparse

from .viewer import Viewer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sysops 3d", description="3D ASCII renderer foundation (not enabled yet)")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--depth", type=float, default=3.0, help="Depth scale")
    return parser


def main() -> None:
    raise RuntimeError(
        "The ascii3d renderer is a foundation feature. Complete camera, lighting, "
        "rasterization, and interactive viewer milestones before enabling sysops 3d."
    )
