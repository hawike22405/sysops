from pathlib import Path

import pytest
from PIL import Image

from sysops.ascii_art import UnsupportedImageError, render_ascii


def test_render_default_logo():
    result = render_ascii()
    assert isinstance(result, str)
    assert result


def test_render_image(tmp_path: Path):
    image_path = tmp_path / "sample.png"
    Image.new("L", (10, 10), color=0).save(image_path)

    result = render_ascii(str(image_path), width=10)
    assert isinstance(result, str)
    assert len(result.splitlines()) == 5
    assert all(len(line) == 10 for line in result.splitlines())


def test_render_rejects_invalid_width():
    with pytest.raises(ValueError, match="width must be greater than 0"):
        render_ascii(width=0)


def test_render_rejects_missing_image():
    with pytest.raises(UnsupportedImageError, match="No such image file"):
        render_ascii("missing-image.png")
