"""Terminal Dino run game for `sysops --play` / `sysops play`.

A Chrome-offline-style runner where the dino jumps or ducks to avoid oncoming
cacti and pterodactyls. Built on stdlib `curses` with full animations, day/night
cycles, scoreboard stats, and time-based physics.
"""

import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import curses
except ImportError:  # pragma: no cover
    curses = None

# --- Art Definitions ---

DINO_RUN1 = [
    " █▀█",
    "███ ",
    "█ █ ",
]
DINO_RUN2 = [
    " █▀█",
    "███ ",
    " █  ",
]
DINO_BLINK = [
    " █─█",
    "███ ",
    "█ █ ",
]
DINO_JUMP = [
    " █▀█",
    "███ ",
    "██  ",
]

DINO_DUCK1 = [
    "█████",
    "█ █  ",
]
DINO_DUCK2 = [
    "█████",
    " █ █ ",
]

DINO_W = 4
DINO_H = 3
DINO_DUCK_W = 5
DINO_DUCK_H = 2

CACTI = {
    "small": [" █ ", "███"],
    "medium": [" █ ", "███", " █ "],
    "tall": [" █ ", " █ ", "███", " █ "],
    "double": ["█ █", "███", "█ █"],
    "cluster": ["█ █ █", "█████", "  █  "],
}

PTERODACTYL_FRAME1 = [
    "  ▲▲ ",
    "◄████",
]
PTERODACTYL_FRAME2 = [
    "◄████",
    "  ▼▼ ",
]

# --- Physics & Gameplay Settings ---
GRAVITY = 0.45
GRAVITY_HOLD = 0.25
JUMP_VELOCITY = -2.6
BASE_SPEED = 2.5
MAX_SPEED = 9.0
MIN_GAP = 12
SPAWN_BASE = 55
FRAME_MS = 50
COYOTE_TIME = 0.12  # seconds
MIN_JUMP_TIME = 0.10  # seconds


def _get_config_dir() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        path = Path(config_home) / "sysops"
    else:
        path = Path.home() / ".config" / "sysops"
    return path


def _load_high_score() -> int:
    try:
        path = _get_config_dir() / "dino_highscore.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return int(data.get("high_score", 0))
    except Exception:
        pass
    return 0


def _save_high_score(score: int) -> None:
    try:
        config_dir = _get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        path = config_dir / "dino_highscore.json"
        path.write_text(json.dumps({"high_score": score}), encoding="utf-8")
    except Exception:
        pass


def _new_game(width: int, height: int) -> Dict:
    ground = max(6, height - 3)

    clouds = []
    for _ in range(3):
        clouds.append({
            "x": float(random.randint(5, max(10, width - 10))),
            "y": random.randint(2, max(2, ground - 6)),
            "art": [" ░░ ", "░░░░"],
        })

    stars = []
    for _ in range(8):
        stars.append({
            "x": random.randint(2, max(2, width - 3)),
            "y": random.randint(1, max(1, ground - 7)),
            "char": random.choice(["*", ".", "·", "✦"]),
        })

    return {
        "width": width,
        "height": height,
        "ground": ground,
        "dino_x": 4.0,
        "dino_y": float(ground),
        "vy": 0.0,
        "grounded": True,
        "is_ducking": False,
        "duck_counter": 0,
        "jump_counter": 0,
        "jump_held": False,
        "coyote_timer": 0.0,
        "min_jump_timer": 0.0,
        "obstacles": [],
        "clouds": clouds,
        "stars": stars,
        "ground_offset": 0.0,
        "speed": BASE_SPEED,
        "score": 0,
        "distance": 0.0,
        "spawn_timer": 0.0,
        "frame": 0,
        "status": "START",  # "START", "COUNTDOWN", "PLAYING", "PAUSED", "GAMEOVER"
        "countdown": 3,
        "countdown_timer": 3.0,
        "is_night": False,
    }


def _spawn_obstacle(state: Dict) -> Dict:
    # Spawn pterodactyls only if score >= 150 and random chance
    if state["score"] >= 150 and random.random() < 0.4:
        altitude = random.choice(["low", "mid", "high"])
        if altitude == "low":
            y_bot = state["ground"] - 1
        elif altitude == "mid":
            y_bot = state["ground"] - 2
        else:  # high
            y_bot = state["ground"] - 3
        y_top = y_bot - 1
        return {
            "type": "pterodactyl",
            "art": PTERODACTYL_FRAME1,
            "x": float(state["width"] - 1),
            "w": 5,
            "h": 2,
            "y_top": y_top,
            "y_bot": y_bot,
            "altitude": altitude,
        }
    else:
        art = random.choice(list(CACTI.values()))
        h = len(art)
        w = max(len(r) for r in art)
        return {
            "type": "cactus",
            "art": art,
            "x": float(state["width"] - 1),
            "w": w,
            "h": h,
            "y_top": state["ground"] - h + 1,
            "y_bot": state["ground"],
            "altitude": "ground",
        }


def _tick(state: Dict, dt: float = 0.05) -> None:
    st = state
    if st["status"] == "PAUSED":
        return

    if st["status"] == "COUNTDOWN":
        st["countdown_timer"] -= dt
        if st["countdown_timer"] <= 0:
            st["status"] = "PLAYING"
        else:
            st["countdown"] = int(st["countdown_timer"]) + 1
        return

    if st["status"] != "PLAYING":
        return

    st["frame"] += 1
    st["score"] += 1
    st["distance"] += st["speed"] * dt * 5.0
    st["speed"] = min(MAX_SPEED, BASE_SPEED + st["score"] / 400.0)
    st["is_night"] = (st["score"] // 500) % 2 == 1

    dt_factor = dt / 0.05  # Scale physics normalized to 50ms (20 ticks/sec)

    st["ground_offset"] = (st["ground_offset"] + st["speed"] * 0.25 * dt_factor) % 40.0

    if st["duck_counter"] > 0:
        st["is_ducking"] = True
        st["duck_counter"] -= 1
    else:
        st["is_ducking"] = False

    if st["jump_counter"] > 0:
        st["jump_held"] = True
        st["jump_counter"] -= 1
    else:
        st["jump_held"] = False

    if st["grounded"]:
        st["coyote_timer"] = COYOTE_TIME
    else:
        st["coyote_timer"] = max(0.0, st["coyote_timer"] - dt)

    if st["min_jump_timer"] > 0:
        st["min_jump_timer"] = max(0.0, st["min_jump_timer"] - dt)

    if not st["grounded"]:
        if st["jump_held"] and st["vy"] < 0:
            st["vy"] += GRAVITY_HOLD * dt_factor
        else:
            st["vy"] += GRAVITY * dt_factor
        st["dino_y"] += st["vy"] * dt_factor

        # Top ceiling clamp to keep Dino inside terminal bounds
        min_dino_y = float(2 + DINO_H - 1)
        if st["dino_y"] < min_dino_y:
            st["dino_y"] = min_dino_y
            st["vy"] = max(0.0, st["vy"])

        if st["dino_y"] >= st["ground"]:
            st["dino_y"] = float(st["ground"])
            st["vy"] = 0.0
            st["grounded"] = True
            st["min_jump_timer"] = MIN_JUMP_TIME

    for ob in st["obstacles"]:
        ob["x"] -= st["speed"] * dt_factor
    st["obstacles"] = [o for o in st["obstacles"] if o["x"] + o["w"] > 0]

    for cloud in st["clouds"]:
        cloud["x"] -= (st["speed"] * 0.2) * dt_factor
        if cloud["x"] < -6:
            cloud["x"] = float(st["width"] + random.randint(2, 10))
            cloud["y"] = random.randint(2, max(2, st["ground"] - 6))

    interval = max(12, int(SPAWN_BASE / (st["speed"] / BASE_SPEED)))
    st["spawn_timer"] -= 1.0 * dt_factor
    if st["spawn_timer"] <= 0:
        if not st["obstacles"] or (
            st["obstacles"][-1]["x"] + st["obstacles"][-1]["w"]
            < st["width"] - MIN_GAP
        ):
            st["obstacles"].append(_spawn_obstacle(st))
        st["spawn_timer"] = float(interval)


def _rects_overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1) -> bool:
    return ax0 <= bx1 and bx0 <= ax1 and ay0 <= by1 and by0 <= ay1


def _collides(state: Dict) -> bool:
    is_duck = state.get("is_ducking", False)
    dino_w = DINO_DUCK_W if is_duck else DINO_W
    dino_h = DINO_DUCK_H if is_duck else DINO_H

    dx0 = int(state["dino_x"])
    dx1 = dx0 + dino_w - 1
    dy0 = int(state["dino_y"]) - dino_h + 1
    dy1 = int(state["dino_y"])

    for ob in state["obstacles"]:
        ox0 = int(ob["x"])
        ox1 = ox0 + ob["w"] - 1
        oy0 = int(ob["y_top"])
        oy1 = int(ob["y_bot"])

        if _rects_overlap(dx0, dy0, dx1, dy1, ox0, oy0, ox1, oy1):
            return True
    return False


def _put(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    try:
        maxy, maxx = stdscr.getmaxyx()
        iy, ix = int(y), int(x)
        if 0 <= iy < maxy and 0 <= ix < maxx:
            available = maxx - ix
            if len(text) > available:
                text = text[:available]
            stdscr.addstr(iy, ix, text, attr)
    except curses.error:
        pass


def _draw(
    stdscr,
    state: Dict,
    over: bool = False,
    high_score: int = 0,
    use_color: bool = False,
) -> None:
    st = state
    h = st["height"]
    w = st["width"]
    ground = st["ground"]

    g = curses.color_pair(2) if use_color else 0
    c = curses.color_pair(1) if use_color else 0
    s = curses.color_pair(3) if use_color else 0
    cyan = curses.color_pair(4) if use_color else 0

    stdscr.erase()

    # Terminal size guard
    if w < 35 or h < 12:
        msg1 = "Terminal size too small!"
        msg2 = f"Min 35x12 (got {w}x{h})"
        msg3 = "Press Q to quit"
        _put(stdscr, h // 2 - 1, max(0, (w - len(msg1)) // 2), msg1, s)
        _put(stdscr, h // 2, max(0, (w - len(msg2)) // 2), msg2, s)
        _put(stdscr, h // 2 + 1, max(0, (w - len(msg3)) // 2), msg3, s)
        stdscr.refresh()
        return

    # Background: Night mode vs Day mode
    if st["is_night"]:
        for star in st["stars"]:
            _put(stdscr, star["y"], star["x"], star["char"], cyan)
        _put(stdscr, 2, max(2, w - 8), "☾ Moon", cyan)
    else:
        _put(stdscr, 2, max(2, w - 8), "☼ Sun", s)

    # Clouds
    for cloud in st["clouds"]:
        for r, row in enumerate(cloud["art"]):
            _put(stdscr, cloud["y"] + r, cloud["x"], row, cyan)

    # Smooth ground scrolling line
    ground_pattern = "───•───────▫────┴───────•───────▫────┴───"
    pattern_len = len(ground_pattern)
    offset = st["ground_offset"]
    for x in range(w):
        ch = ground_pattern[int(x + offset) % pattern_len]
        _put(stdscr, ground + 1, x, ch, g)

    # Dino drawing
    if st.get("is_ducking", False):
        art = DINO_DUCK1 if (st["frame"] // 4) % 2 == 0 else DINO_DUCK2
        h_art = DINO_DUCK_H
    elif not st["grounded"]:
        art = DINO_JUMP
        h_art = DINO_H
    else:
        if (st["frame"] // 30) % 5 == 0 and (st["frame"] % 30) < 3:
            art = DINO_BLINK
        else:
            art = DINO_RUN1 if (st["frame"] // 4) % 2 == 0 else DINO_RUN2
        h_art = DINO_H

    dino_top_y = st["dino_y"] - h_art + 1
    for r, row in enumerate(art):
        _put(stdscr, dino_top_y + r, st["dino_x"], row, g)

    # Obstacles drawing
    for ob in st["obstacles"]:
        if ob["type"] == "pterodactyl":
            art_ob = PTERODACTYL_FRAME1 if (st["frame"] // 4) % 2 == 0 else PTERODACTYL_FRAME2
        else:
            art_ob = ob["art"]
        for r, art_row in enumerate(art_ob):
            _put(stdscr, ob["y_top"] + r, ob["x"], art_row, c)

    # Header / Scoreboard
    title = "S Y S O P S  D I N O"
    _put(stdscr, 1, 2, title, s)
    dist_text = f"{int(st['distance'])}m"
    score_text = f"HI {high_score:05d}  {st['score']:05d}  {dist_text}  {st['speed']:.1f}x"
    _put(stdscr, 1, max(2, w - len(score_text) - 2), score_text, s)

    status = st["status"]
    if over or status == "GAMEOVER":
        box_w = min(w - 4, 38)
        box_h = 9
        top_y = max(1, (h - box_h) // 2)
        left_x = max(0, (w - box_w) // 2)

        _put(stdscr, top_y, left_x, "┌" + "─" * (box_w - 2) + "┐", s)
        _put(stdscr, top_y + 1, left_x, "│" + " G A M E   O V E R ".center(box_w - 2) + "│", s)
        _put(stdscr, top_y + 2, left_x, "├" + "─" * (box_w - 2) + "┤", s)
        _put(stdscr, top_y + 3, left_x, "│" + f"  Score:       {st['score']:<10}".ljust(box_w - 2) + "│", s)
        _put(stdscr, top_y + 4, left_x, "│" + f"  High Score:  {high_score:<10}".ljust(box_w - 2) + "│", s)
        _put(stdscr, top_y + 5, left_x, "│" + f"  Distance:    {dist_text:<10}".ljust(box_w - 2) + "│", s)
        _put(stdscr, top_y + 6, left_x, "│" + "  Press SPACE / R to restart".ljust(box_w - 2) + "│", s)
        _put(stdscr, top_y + 7, left_x, "│" + "  Press Q to quit".ljust(box_w - 2) + "│", s)
        _put(stdscr, top_y + 8, left_x, "└" + "─" * (box_w - 2) + "┘", s)

    elif status == "START":
        banner = "PRESS SPACE TO START"
        _put(stdscr, h // 2 - 2, max(0, (w - len(banner)) // 2), banner, s | curses.A_BOLD)
        sub = "SPACE/UP Jump | DOWN Duck | P Pause | Q Quit"
        _put(stdscr, h // 2, max(0, (w - len(sub)) // 2), sub, s)

    elif status == "COUNTDOWN":
        num_str = f"--- {st['countdown']} ---"
        _put(stdscr, h // 2 - 1, max(0, (w - len(num_str)) // 2), num_str, s | curses.A_BOLD)

    elif status == "PAUSED":
        pause_msg = " [ P A U S E D ] "
        _put(stdscr, h // 2, max(0, (w - len(pause_msg)) // 2), pause_msg, s | curses.A_BOLD)

    elif status == "PLAYING":
        hint = "SPACE Jump  DOWN Duck  P Pause  Q Quit"
        _put(stdscr, h - 1, max(0, (w - len(hint)) // 2), hint, s)

    stdscr.refresh()


def _play(stdscr) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)

    use_color = False
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # Obstacles
        curses.init_pair(2, curses.COLOR_WHITE, -1)   # Dino / Ground
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Score / UI
        curses.init_pair(4, curses.COLOR_CYAN, -1)    # Stars / Sky
        use_color = True
    except curses.error:
        pass

    high_score = _load_high_score()

    maxy, maxx = stdscr.getmaxyx()
    width = max(35, min(maxx, 90))
    height = max(12, min(maxy, 25))
    state = _new_game(width, height)

    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
        dt = max(0.005, min(0.1, dt))

        stdscr.nodelay(True)
        stdscr.timeout(FRAME_MS)
        key = stdscr.getch()

        if key == curses.KEY_RESIZE:
            maxy, maxx = stdscr.getmaxyx()
            state["width"] = max(35, min(maxx, 90))
            state["height"] = max(12, min(maxy, 25))
            state["ground"] = max(6, state["height"] - 3)
            stdscr.clear()

        elif key in (ord("q"), ord("Q"), 27):
            return

        elif key in (ord("p"), ord("P")):
            if state["status"] == "PLAYING":
                state["status"] = "PAUSED"
            elif state["status"] == "PAUSED":
                state["status"] = "PLAYING"

        elif key in (ord("r"), ord("R")):
            state = _new_game(state["width"], state["height"])
            state["status"] = "PLAYING"

        elif key in (curses.KEY_UP, ord(" "), ord("w"), ord("W")):
            if state["status"] == "START":
                state["status"] = "COUNTDOWN"
                state["countdown_timer"] = 3.0
                state["countdown"] = 3
            elif state["status"] == "GAMEOVER":
                state = _new_game(state["width"], state["height"])
                state["status"] = "PLAYING"
            elif state["status"] == "PLAYING":
                if (state["grounded"] or state["coyote_timer"] > 0) and state["min_jump_timer"] <= 0:
                    state["vy"] = JUMP_VELOCITY
                    state["grounded"] = False
                    state["coyote_timer"] = 0.0
                    state["jump_counter"] = 5

        elif key in (curses.KEY_DOWN, ord("s"), ord("S"), ord(",")):
            if state["status"] == "PLAYING":
                state["duck_counter"] = 4

        # Tick logic
        _tick(state, dt)

        # Collision logic
        if state["status"] == "PLAYING" and _collides(state):
            state["status"] = "GAMEOVER"
            if state["score"] > high_score:
                high_score = state["score"]
                _save_high_score(high_score)

        over = (state["status"] == "GAMEOVER")
        _draw(stdscr, state, over=over, high_score=high_score, use_color=use_color)


def run_game() -> None:
    """Launch the Dino run game. Returns when the player quits."""
    if curses is None:
        print(
            "The Dino game needs the `curses` module (built into Python on "
            "Linux/macOS).",
            file=sys.stderr,
        )
        print("On Windows install it with: pip install windows-curses", file=sys.stderr)
        return
    try:
        curses.wrapper(_play)
    except KeyboardInterrupt:
        pass