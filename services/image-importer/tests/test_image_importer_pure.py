import json
import pytest
from pathlib import Path
from PIL import Image as PILImage


class TestPublicPolicy:
    def test_contains_bucket_name(self):
        from services.image_importer import _public_policy
        policy = json.loads(_public_policy("my-bucket"))
        resource = policy["Statement"][0]["Resource"][0]
        assert "my-bucket" in resource

    def test_allows_get_object(self):
        from services.image_importer import _public_policy
        policy = json.loads(_public_policy("b"))
        actions = policy["Statement"][0]["Action"]
        assert "s3:GetObject" in actions

    def test_principal_is_wildcard(self):
        from services.image_importer import _public_policy
        policy = json.loads(_public_policy("b"))
        assert "*" in policy["Statement"][0]["Principal"]["AWS"]


class TestScanImages:
    def test_finds_png_and_jpg(self, tmp_path):
        from services.image_importer import scan_images
        (tmp_path / "a.png").write_bytes(b"x")
        (tmp_path / "b.jpg").write_bytes(b"x")
        (tmp_path / "c.txt").write_bytes(b"x")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "d.webp").write_bytes(b"x")
        results = scan_images(str(tmp_path))
        names = [Path(f).name for f in results]
        assert "a.png" in names
        assert "b.jpg" in names
        assert "d.webp" in names
        assert "c.txt" not in names

    def test_empty_directory_returns_empty(self, tmp_path):
        from services.image_importer import scan_images
        assert scan_images(str(tmp_path)) == []


class TestToInt:
    def test_converts_valid_int(self):
        from services.image_importer import to_int
        assert to_int({"steps": "20"}, "steps") == 20

    def test_returns_none_for_missing_key(self):
        from services.image_importer import to_int
        assert to_int({}, "steps") is None

    def test_returns_none_for_invalid_value(self):
        from services.image_importer import to_int
        assert to_int({"steps": "abc"}, "steps") is None


class TestReadPngMetadata:
    def test_returns_none_for_missing_file(self, tmp_path):
        from services.image_importer import read_png_metadata
        result = read_png_metadata(tmp_path / "nope.png")
        assert result is None

    def test_returns_none_for_png_without_prompt(self, tmp_path):
        from services.image_importer import read_png_metadata
        img = PILImage.new("RGB", (10, 10))
        path = tmp_path / "plain.png"
        img.save(path)
        result = read_png_metadata(path)
        assert result is None


class TestReadPngSidecar:
    def test_returns_none_when_no_sidecar(self, tmp_path):
        from services.image_importer import read_png_sidecar
        result = read_png_sidecar(tmp_path / "img.png")
        assert result is None

    def test_reads_sidecar_json(self, tmp_path):
        from services.image_importer import read_png_sidecar
        sidecar = tmp_path / "img.json"
        sidecar.write_text(json.dumps({"prompt": {}}))
        result = read_png_sidecar(tmp_path / "img.png")
        assert result is not None
        assert "sidecar" in result


class TestImageMetadata:
    def test_returns_none_for_missing_file(self, tmp_path):
        from services.image_importer import image_metadata
        result = image_metadata(tmp_path / "nope.png")
        assert result is None

    def test_returns_dict_for_plain_png(self, tmp_path):
        from services.image_importer import image_metadata
        img = PILImage.new("RGB", (10, 10))
        path = tmp_path / "plain.png"
        img.save(path)
        result = image_metadata(path)
        assert result is not None
        assert "filename" in result

    def test_reads_sidecar_alongside_png(self, tmp_path):
        from services.image_importer import image_metadata
        img = PILImage.new("RGB", (10, 10))
        path = tmp_path / "img.png"
        img.save(path)
        (tmp_path / "img.json").write_text(json.dumps({"prompt": {}}))
        result = image_metadata(path)
        assert result is not None
        assert "sidecar" in result
