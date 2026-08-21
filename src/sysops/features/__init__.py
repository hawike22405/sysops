"""Optional interactive and diagnostic features for sysops."""

from .achievements import check_achievements, list_all_badges
from .benchmark import run_benchmark
from .interactive_menu import run_interactive_menu

__all__ = [
    "check_achievements",
    "list_all_badges",
    "run_benchmark",
    "run_interactive_menu",
]
