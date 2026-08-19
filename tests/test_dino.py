from sysops.dino import (
    _collides,
    _get_config_dir,
    _load_high_score,
    _new_game,
    _save_high_score,
    _spawn_obstacle,
    _tick,
    DINO_H,
)
from sysops.cli import build_parser


def _obstacle(x, state, height=1, y_top=None):
    if y_top is None:
        y_top = state["ground"] - height + 1
    return {
        "art": ["█"] * height,
        "x": x,
        "w": 1,
        "h": height,
        "y_top": y_top,
        "y_bot": y_top + height - 1,
    }


def test_tick_increments_score():
    state = _new_game(80, 20)
    state["status"] = "PLAYING"
    before = state["score"]
    _tick(state)
    assert state["score"] == before + 1


def test_collision_when_overlapping():
    state = _new_game(80, 20)
    state["status"] = "PLAYING"
    state["obstacles"] = [_obstacle(state["dino_x"] + 1, state)]
    assert _collides(state)


def test_no_collision_when_far():
    state = _new_game(80, 20)
    state["status"] = "PLAYING"
    state["obstacles"] = [_obstacle(60, state)]
    assert not _collides(state)


def test_no_collision_when_jumping_over():
    state = _new_game(80, 20)
    state["status"] = "PLAYING"
    state["dino_y"] = state["ground"] - 10
    state["obstacles"] = [_obstacle(state["dino_x"] + 1, state, height=3)]
    assert not _collides(state)


def test_ducking_avoids_mid_obstacle():
    state = _new_game(80, 20)
    state["status"] = "PLAYING"
    # Mid obstacle at ground - 2
    mid_y_top = state["ground"] - 2
    state["obstacles"] = [_obstacle(state["dino_x"] + 1, state, height=1, y_top=mid_y_top)]

    # When standing (height 3), dino top is ground - 2, so it collides
    state["is_ducking"] = False
    assert _collides(state)

    # When ducking (height 2), dino top is ground - 1, so it passes under safely
    state["is_ducking"] = True
    assert not _collides(state)


def test_pterodactyl_spawn_at_high_score():
    state = _new_game(80, 20)
    state["score"] = 300
    obstacle = _spawn_obstacle(state)
    assert "type" in obstacle
    assert obstacle["type"] in ("cactus", "pterodactyl")


def test_high_score_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert _load_high_score() == 0

    _save_high_score(250)
    assert _load_high_score() == 250


def test_sysops_play_cli_subcommand():
    parser = build_parser()
    args = parser.parse_args(["play"])
    assert args.command == "play"


def test_pause_state_prevents_tick():
    state = _new_game(80, 20)
    state["status"] = "PAUSED"
    score_before = state["score"]
    _tick(state)
    assert state["score"] == score_before

