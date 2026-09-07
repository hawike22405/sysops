"""Optional interactive and diagnostic features for sysops."""

from .achievements import check_achievements, list_all_badges
from .benchmark import run_benchmark
from .htop_view import run_htop_view
from .interactive_menu import run_interactive_menu
from .os_logo import animate_os_logo, detect_os, logo_frames, render_os_frame

__all__ = [
    "animate_os_logo",
    "detect_os",
    "logo_frames",
    "render_os_frame",
    "check_achievements",
    "list_all_badges",
    "run_benchmark",
    "run_htop_view",
    "run_interactive_menu",
]
