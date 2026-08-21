#!/usr/bin/env python3
"""Lightweight persistent system achievement/badge system."""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime

STATE_FILE = os.path.join(os.path.expanduser("~"), ".sysops_achievements.json")


def _run(command):
    try:
        return subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def get_uptime_days():
    try:
        with open("/proc/uptime", encoding="utf-8") as handle:
            return float(handle.readline().split()[0]) / 86400.0
    except (OSError, ValueError, IndexError):
        match = re.search(r"(\d+)\s+day", _run("uptime -p"))
        return float(match.group(1)) if match else 0.0


def get_cpu_core_count():
    return os.cpu_count() or 0


def get_total_ram_gb():
    try:
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024 * 1024)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def get_disk_count():
    output = _run("lsblk -d -n -o NAME 2>/dev/null | wc -l")
    try:
        return int(output)
    except ValueError:
        return 0


def _build_badge_defs(facts):
    return {
        "day_one": ("Day One", "System has been up for at least 1 day.", facts["uptime_days"] >= 1),
        "week_streak": ("Week Streak", "System has been up for at least 7 days.", facts["uptime_days"] >= 7),
        "century_club": ("Century Club", "System has been up for at least 100 days.", facts["uptime_days"] >= 100),
        "quad_squad": ("Quad Squad", "4 or more CPU cores detected.", facts["cpu_cores"] >= 4),
        "core_hoarder": ("Core Hoarder", "16 or more CPU cores detected.", facts["cpu_cores"] >= 16),
        "memory_lane": ("Memory Lane", "32 GB or more RAM detected.", facts["ram_gb"] >= 32),
        "modest_machine": ("Modest Machine", "Less than 4 GB RAM detected — respect.", 0 < facts["ram_gb"] < 4),
        "disk_collector": ("Disk Collector", "3 or more block storage devices detected.", facts["disk_count"] >= 3),
    }


def _load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as handle:
            state = json.load(handle)
            return state if isinstance(state, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
    except OSError:
        pass


def _facts():
    return {
        "uptime_days": get_uptime_days(),
        "cpu_cores": get_cpu_core_count(),
        "ram_gb": get_total_ram_gb(),
        "disk_count": get_disk_count(),
    }


def check_achievements(verbose=True):
    """Unlock newly satisfied badges and return them as ``(id, name, desc)`` tuples."""
    definitions = _build_badge_defs(_facts())
    state = _load_state()
    unlocked = state.setdefault("unlocked", {})
    newly_unlocked = []

    for badge_id, (name, description, condition_met) in definitions.items():
        if condition_met and badge_id not in unlocked:
            unlocked[badge_id] = datetime.now().isoformat(timespec="seconds")
            newly_unlocked.append((badge_id, name, description))

    _save_state(state)
    if verbose and newly_unlocked:
        print("🏆 New achievement" + ("s" if len(newly_unlocked) != 1 else "") + " unlocked!")
        for _, name, description in newly_unlocked:
            print(f"   [{name}] {description}")
    return newly_unlocked


def list_all_badges():
    definitions = _build_badge_defs(_facts())
    unlocked = _load_state().get("unlocked", {})
    print("=== SysOps Achievements ===")
    for badge_id, (name, description, _) in definitions.items():
        status = "✅ UNLOCKED" if badge_id in unlocked else "🔒 locked"
        print(f"{status:14} {name:<16} - {description}")


def main():
    parser = argparse.ArgumentParser(description="Check and list SysOps achievements.")
    parser.add_argument("--list", action="store_true", help="List all badges and their status")
    args = parser.parse_args()
    if args.list:
        list_all_badges()
    elif not check_achievements():
        print("No new achievements this run.")


if __name__ == "__main__":
    main()
