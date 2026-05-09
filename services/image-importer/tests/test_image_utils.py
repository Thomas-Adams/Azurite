import pytest
from utils.image_utils import read_image_size


def test_read_size_returns_correct_dimensions(plain_png):
    width, height = read_image_size(str(plain_png))
    assert width == 200
    assert height == 100


def test_read_size_png_with_metadata(png_with_metadata):
    width, height = read_image_size(str(png_with_metadata))
    assert width == 512
    assert height == 768


def test_read_size_missing_file(tmp_path):
    missing = tmp_path / "nonexistent.png"
    width, height = read_image_size(str(missing))
    assert width is None
    assert height is None


def test_read_size_invalid_file(tmp_path):
    not_an_image = tmp_path / "bad.png"
    not_an_image.write_bytes(b"this is not an image")
    width, height = read_image_size(str(not_an_image))
    assert width is None
    assert height is None


def test_read_size_returns_ints(plain_png):
    width, height = read_image_size(str(plain_png))
    assert isinstance(width, int)
    assert isinstance(height, int)
