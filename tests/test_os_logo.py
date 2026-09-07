from sysops.features import os_logo


def test_supported_os_have_flipbook_frames():
    for name in ("Linux", "Windows", "macOS"):
        frames = os_logo.logo_frames(name)
        assert 4 <= len(frames) <= 8
        assert all(len(frame.splitlines()) == len(frames[0].splitlines()) for frame in frames)


def test_frame_index_wraps_and_width_is_stable():
    for name in ("Linux", "Windows", "macOS"):
        a = os_logo.render_os_frame(name, width=40, frame_index=0, color=False)
        b = os_logo.render_os_frame(name, width=40, frame_index=len(os_logo.logo_frames(name)), color=False)
        assert a == b
        assert all(len(line) == 40 for line in a.splitlines())


def test_unknown_os_falls_back():
    assert "SYSOPS" in os_logo.render_os_frame("Unknown", width=24, color=False)


def test_invalid_fps():
    try:
        os_logo.animate_os_logo(fps=0, loops=1)
    except ValueError as exc:
        assert "greater than 0" in str(exc)
    else:
        raise AssertionError("expected ValueError")
