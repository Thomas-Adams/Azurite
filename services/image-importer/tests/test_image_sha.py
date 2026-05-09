import hashlib
import pytest
from utils.image_sha import sha256_of_file


def test_sha256_known_content(tmp_path):
    content = b"hello azurite"
    path = tmp_path / "known.bin"
    path.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert sha256_of_file(str(path)) == expected


def test_sha256_is_hex_string(tmp_path):
    path = tmp_path / "file.bin"
    path.write_bytes(b"data")
    result = sha256_of_file(str(path))
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_sha256_consistent(plain_png):
    first = sha256_of_file(str(plain_png))
    second = sha256_of_file(str(plain_png))
    assert first == second


def test_sha256_differs_for_different_content(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"aaaa")
    b.write_bytes(b"bbbb")
    assert sha256_of_file(str(a)) != sha256_of_file(str(b))


def test_sha256_empty_file(tmp_path):
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert sha256_of_file(str(path)) == expected
