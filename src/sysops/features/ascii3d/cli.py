import argparse
from pathlib import Path

from .viewer import Viewer, ViewerConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="3D ASCII Image Viewer")
    parser.add_argument("image", help="Path to an image file")
    parser.add_argument("--width", type=int, default=100, help="Terminal width")
    parser.add_argument("--height", type=int, default=35, help="Terminal height")
    parser.add_argument("--scale", type=float, default=3.0, help="Depth scale factor")
    parser.add_argument("--color", action="store_true", help="Use ANSI color")
    args = parser.parse_args()

    run_viewer(args.image, args.width, args.height, args.scale, args.color)

def run_viewer(image_path: str, width: int = 100, height: int = 35, scale: float = 3.0, use_color: bool = False) -> None:
    config = ViewerConfig(
        terminal_width=width,
        terminal_height=height,
        depth_scale=scale,
        use_color=use_color
    )
    viewer = Viewer(config=config)
    
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise SystemExit(f"Error: No such image file: {path}")

    try:
        viewer.load_image(path)
        viewer.run()
    except Exception as exc:
        raise SystemExit(f"Error: {exc}")
