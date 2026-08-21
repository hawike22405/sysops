import sys

from sysops.features import interactive_menu as menu


def test_basic_stats_has_cross_platform_fields(monkeypatch):
    monkeypatch.setattr(menu.platform, "uname", lambda: type("U", (), {
        "node": "test-host",
        "system": "Windows",
        "release": "11",
        "machine": "AMD64",
    })())
    monkeypatch.setattr(menu.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(menu, "_windows_uptime", lambda: "1d 2h 3m")
    monkeypatch.setattr(menu.os, "name", "nt")
    stats = menu.get_basic_stats()
    assert stats["Hostname"] == "test-host"
    assert stats["CPU cores"] == "8"
    assert stats["Uptime"] == "1d 2h 3m"


def test_windows_hidden_stats(monkeypatch):
    monkeypatch.setattr(menu.os, "name", "nt")
    monkeypatch.setattr(menu, "_windows_memory", lambda: "4.0 GB / 16.0 GB")
    monkeypatch.setattr(menu, "_windows_disk", lambda: "100.0 GB / 500.0 GB (20%)")
    monkeypatch.setattr(menu, "_windows_processes", lambda: "125")
    stats = menu.get_hidden_stats()
    assert stats["Memory"] == "4.0 GB / 16.0 GB"
    assert stats["Disk (C:)"] == "100.0 GB / 500.0 GB (20%)"
    assert stats["Processes"] == "125"
    assert "Windows" in stats["Load average"]


def test_linux_hidden_stats(monkeypatch):
    monkeypatch.setattr(menu.os, "name", "posix")
    values = iter([
        "0.12 0.15 0.20",
        "3Gi/16Gi",
        "0Gi/4Gi",
        "100Gi/250Gi (40%)",
        "128",
        "6.12.1",
    ])
    monkeypatch.setattr(menu, "_run", lambda command: next(values))
    stats = menu.get_hidden_stats()
    assert stats["Load average"] == "0.12 0.15 0.20"
    assert stats["Memory"] == "3Gi/16Gi"
    assert stats["Processes"] == "128"
