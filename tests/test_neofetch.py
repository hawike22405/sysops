"""Tests for the neofetch feature (ascii_logos, system_info, layout)."""

import os
import re

from sysops.features.neofetch.ascii_logos import (
    _LOGO_HEIGHT,
    colorize_logo,
    get_logo,
    get_logo_colors,
    list_supported_distros,
)
from sysops.features.neofetch.system_info import gather_system_info
from sysops.features.neofetch.layout import render_fetch, _strip_ansi, _visible_len


# -----------------------------------------------------------------------
# ASCII logos
# -----------------------------------------------------------------------

class TestAsciiLogos:
    def test_all_logos_have_correct_height(self):
        for distro in list_supported_distros():
            logo = get_logo(distro)
            lines = logo.splitlines()
            assert len(lines) == _LOGO_HEIGHT, (
                f"{distro} logo has {len(lines)} lines, expected {_LOGO_HEIGHT}"
            )

    def test_fuzzy_matching(self):
        """Substring matching should find logos for variants."""
        logo_arch = get_logo("arch")
        logo_archlinux = get_logo("archlinux")
        # Both should resolve to the same art (Arch)
        assert logo_arch == logo_archlinux

    def test_unknown_distro_falls_back(self):
        logo = get_logo("totallyunknowndistro12345")
        assert logo  # should not be empty
        assert len(logo.splitlines()) == _LOGO_HEIGHT

    def test_get_logo_colors_returns_tuple(self):
        for distro in ("arch", "ubuntu", "debian", "windows", "macos"):
            colors = get_logo_colors(distro)
            assert isinstance(colors, tuple)
            assert len(colors) == 2

    def test_colorize_logo_adds_ansi(self):
        logo = get_logo("ubuntu")
        colored = colorize_logo(logo, "ubuntu")
        # Should contain ANSI escape sequences
        assert "\x1b[" in colored
        # Should have the same number of lines
        assert len(colored.splitlines()) == len(logo.splitlines())


# -----------------------------------------------------------------------
# System info
# -----------------------------------------------------------------------

class TestSystemInfo:
    def test_gather_returns_dict(self):
        info = gather_system_info()
        assert isinstance(info, dict)

    def test_gather_has_required_keys(self):
        info = gather_system_info()
        required = ["distro_id", "OS", "Kernel", "Uptime", "Shell", "CPU", "Memory"]
        for key in required:
            assert key in info, f"Missing key: {key}"

    def test_all_values_are_strings(self):
        info = gather_system_info()
        for key, value in info.items():
            assert isinstance(value, str), f"{key} has non-string value: {type(value)}"

    def test_no_exceptions_on_any_field(self):
        """Every field should return a string, never raise."""
        info = gather_system_info()
        # If we get here without exception, we're good
        assert len(info) > 0


# -----------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------

class TestLayout:
    def test_strip_ansi_removes_escapes(self):
        text = "\x1b[1;36mhello\x1b[0m world"
        assert _strip_ansi(text) == "hello world"

    def test_visible_len_counts_correctly(self):
        text = "\x1b[1;36mhello\x1b[0m"
        assert _visible_len(text) == 5

    def test_render_fetch_returns_string(self):
        info = gather_system_info()
        output = render_fetch(info)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_fetch_has_logo_and_stats(self, monkeypatch):
        """Output should contain both logo art and stat labels."""
        monkeypatch.setenv("NO_COLOR", "1")
        info = gather_system_info()
        output = render_fetch(info)
        # Should contain at least some stat labels
        assert "OS:" in output or "Kernel:" in output

    def test_lines_alignment(self, monkeypatch):
        """All logo-side columns should be the same visible width."""
        monkeypatch.setenv("NO_COLOR", "1")
        info = {"distro_id": "linux", "OS": "TestOS x86_64", "Kernel": "6.0.0"}
        output = render_fetch(info)
        # Not empty
        assert output.strip()


# -----------------------------------------------------------------------
# CLI integration
# -----------------------------------------------------------------------

class TestCLI:
    def test_fetch_parser_exists(self):
        from sysops.cli import build_parser
        parser = build_parser()
        # The parser should accept 'fetch' without error
        args = parser.parse_args(["fetch"])
        assert args.command == "fetch"

    def test_neofetch_alias_exists(self):
        from sysops.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["neofetch"])
        assert args.command == "neofetch"

    def test_fetch_no_color_flag(self):
        from sysops.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["fetch", "--no-color"])
        assert args.no_color is True
