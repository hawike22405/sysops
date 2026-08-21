from types import SimpleNamespace

from sysops.features import htop_view


def test_sort_mode_defaults_to_cpu():
    sort = htop_view.SortMode()
    assert sort.key == "cpu"
    assert sort.label == "CPU%"


def test_process_sort_keys(monkeypatch):
    processes = [
        SimpleNamespace(info={"pid": 2, "name": "zeta", "cpu_percent": 10.0, "memory_percent": 5.0, "username": "u"}),
        SimpleNamespace(info={"pid": 1, "name": "alpha", "cpu_percent": 90.0, "memory_percent": 2.0, "username": "u"}),
    ]
    monkeypatch.setattr(htop_view.psutil, "process_iter", lambda attrs=None: processes)

    panel = htop_view._build_process_table(htop_view.SortMode("cpu", "CPU%"))
    assert "Processes (sorted by CPU%" in panel.title

    panel = htop_view._build_process_table(htop_view.SortMode("name", "Name"))
    assert "Processes (sorted by Name" in panel.title


def test_refresh_interval_validation():
    try:
        htop_view.run_htop_view(refresh_seconds=0)
    except ValueError as exc:
        assert "greater than 0" in str(exc)
    else:
        raise AssertionError("expected ValueError")
