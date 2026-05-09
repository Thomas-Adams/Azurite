import json
import pytest
from pathlib import Path
from PIL import Image, PngImagePlugin


EXAMPLE_JSON = Path(__file__).parent.parent / "example_ComfyUI_00798_.json"

MINIMAL_PROMPT = {
    "1": {
        "inputs": {"ckpt_name": "test_model.safetensors"},
        "class_type": "CheckpointLoaderSimple",
        "_meta": {"title": "Load Checkpoint"},
    },
    "2": {
        "inputs": {"value": "great quality, solo"},
        "class_type": "Text Multiline",
        "_meta": {"title": "Positive Prompt Start"},
    },
    "3": {
        "inputs": {"value": "bad quality, blurry"},
        "class_type": "Text Multiline",
        "_meta": {"title": "Negative Prompt Start"},
    },
    "4": {
        "inputs": {
            "seed": 42,
            "steps": 30,
            "cfg": 7.5,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
        },
        "class_type": "KSampler",
        "_meta": {"title": "KSampler"},
    },
    "5": {
        "inputs": {
            "lora_name": "test_lora.safetensors",
            "strength_model": 0.8,
            "strength_clip": 0.8,
        },
        "class_type": "LoraLoader",
        "_meta": {"title": "LoRA Loader"},
    },
    "6": {
        "inputs": {"value": "512"},
        "class_type": "Basic data handling: IntCreate",
        "_meta": {"title": "Image Width"},
    },
    "7": {
        "inputs": {"value": "768"},
        "class_type": "Basic data handling: IntCreate",
        "_meta": {"title": "Image Height"},
    },
}


@pytest.fixture
def comfyui_data():
    return json.loads(EXAMPLE_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def minimal_prompt():
    return MINIMAL_PROMPT


@pytest.fixture
def png_with_metadata(tmp_path) -> Path:
    info = PngImagePlugin.PngInfo()
    info.add_text("prompt", json.dumps(MINIMAL_PROMPT))
    info.add_text("workflow", json.dumps({"nodes": []}))
    img = Image.new("RGB", (512, 768), color=(100, 150, 200))
    path = tmp_path / "test_comfyui.png"
    img.save(path, "PNG", pnginfo=info)
    return path


@pytest.fixture
def plain_png(tmp_path) -> Path:
    img = Image.new("RGB", (200, 100), color=(255, 0, 0))
    path = tmp_path / "plain.png"
    img.save(path, "PNG")
    return path


@pytest.fixture
def sidecar_png(tmp_path) -> Path:
    img = Image.new("RGB", (300, 400), color=(0, 255, 0))
    path = tmp_path / "sidecar_test.png"
    img.save(path, "PNG")
    sidecar = tmp_path / "sidecar_test.json"
    sidecar.write_text(json.dumps({"prompt": MINIMAL_PROMPT}), encoding="utf-8")
    return path
