import pytest
from services.image_importer import (
    read_png_metadata,
    read_png_sidecar,
    image_metadata,
    to_int,
)


class TestReadPngMetadata:
    def test_returns_dict_for_comfyui_png(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert result is not None
        assert isinstance(result, dict)

    def test_contains_filename(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert result["filename"] == png_with_metadata

    def test_extracts_model(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert result["model"] == "test_model.safetensors"

    def test_extracts_ksampler_params(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert result["steps"] == 30
        assert result["cfg"] == 7.5
        assert result["seed"] == 42

    def test_extracts_prompts(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert result["positive_prompts"] == ["great quality, solo"]
        assert result["negative_prompts"] == ["bad quality, blurry"]

    def test_extracts_loras(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert len(result["loras"]) == 1
        assert result["loras"][0]["name"] == "test_lora.safetensors"

    def test_contains_raw_and_workflow(self, png_with_metadata):
        result = read_png_metadata(png_with_metadata)
        assert "raw" in result
        assert "workflow" in result

    def test_returns_none_for_plain_png(self, plain_png):
        result = read_png_metadata(plain_png)
        assert result is None

    def test_returns_none_for_missing_file(self, tmp_path):
        result = read_png_metadata(tmp_path / "nonexistent.png")
        assert result is None


class TestReadPngSidecar:
    def test_reads_sidecar_json(self, sidecar_png):
        result = read_png_sidecar(sidecar_png)
        assert result is not None
        assert isinstance(result, dict)

    def test_contains_filename(self, sidecar_png):
        result = read_png_sidecar(sidecar_png)
        assert result["filename"] == sidecar_png

    def test_extracts_model_from_sidecar(self, sidecar_png):
        result = read_png_sidecar(sidecar_png)
        assert result["model"] == "test_model.safetensors"

    def test_contains_sidecar_key(self, sidecar_png):
        result = read_png_sidecar(sidecar_png)
        assert "sidecar" in result

    def test_returns_none_when_no_sidecar(self, plain_png):
        result = read_png_sidecar(plain_png)
        assert result is None

    def test_returns_none_for_missing_image(self, tmp_path):
        result = read_png_sidecar(tmp_path / "ghost.png")
        assert result is None


class TestImageMetadata:
    def test_returns_dict_for_valid_image(self, plain_png):
        result = image_metadata(plain_png)
        assert result is not None
        assert isinstance(result, dict)

    def test_contains_required_keys(self, plain_png):
        result = image_metadata(plain_png)
        assert "filename" in result
        assert "raw" in result
        assert "workflow" in result

    def test_comfyui_png_extracts_fields(self, png_with_metadata):
        result = image_metadata(png_with_metadata)
        assert result["model"] == "test_model.safetensors"
        assert result["steps"] == 30
        assert result["cfg"] == 7.5

    def test_merges_sidecar_when_present(self, sidecar_png):
        result = image_metadata(sidecar_png)
        assert "sidecar" in result
        assert result["model"] == "test_model.safetensors"

    def test_plain_png_has_no_extracted_fields(self, plain_png):
        result = image_metadata(plain_png)
        assert result.get("model") is None

    def test_returns_none_for_missing_file(self, tmp_path):
        result = image_metadata(tmp_path / "missing.png")
        assert result is None


class TestToInt:
    def test_valid_integer_string(self):
        assert to_int({"steps": "30"}, "steps") == 30

    def test_valid_integer(self):
        assert to_int({"steps": 30}, "steps") == 30

    def test_missing_key_returns_none(self):
        assert to_int({}, "steps") is None

    def test_none_value_returns_none(self):
        assert to_int({"steps": None}, "steps") is None

    def test_invalid_string_returns_none(self):
        assert to_int({"steps": "not_a_number"}, "steps") is None

    def test_float_string_returns_none(self):
        assert to_int({"steps": "7.5"}, "steps") is None
