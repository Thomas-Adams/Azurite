import pytest
from utils.excerpt_parser import (
    extract_comfyui_essentials,
    _find_by_class_type,
    _find_by_title_contains,
    _first_input_value,
    _prompt_nodes,
)


def test_extract_model_name(minimal_prompt):
    result = extract_comfyui_essentials({"prompt": minimal_prompt})
    assert result["model"] == "test_model.safetensors"


def test_extract_model_name_missing():
    result = extract_comfyui_essentials({"prompt": {}})
    assert result["model"] is None


def test_extract_loras(minimal_prompt):
    result = extract_comfyui_essentials({"prompt": minimal_prompt})
    assert len(result["loras"]) == 1
    lora = result["loras"][0]
    assert lora["name"] == "test_lora.safetensors"
    assert lora["strength_model"] == 0.8
    assert lora["strength_clip"] == 0.8


def test_extract_no_loras():
    data = {"prompt": {"1": {"inputs": {}, "class_type": "CheckpointLoaderSimple", "_meta": {"title": "x"}}}}
    result = extract_comfyui_essentials(data)
    assert result["loras"] == []


def test_extract_ksampler_params(minimal_prompt):
    result = extract_comfyui_essentials({"prompt": minimal_prompt})
    assert result["steps"] == 30
    assert result["cfg"] == 7.5
    assert result["seed"] == 42
    assert result["sampler_name"] == "euler"
    assert result["scheduler"] == "normal"


def test_extract_ksampler_missing():
    result = extract_comfyui_essentials({"prompt": {}})
    assert result["steps"] is None
    assert result["cfg"] is None
    assert result["seed"] is None
    assert result["sampler_name"] is None
    assert result["scheduler"] is None


def test_extract_positive_prompts(minimal_prompt):
    result = extract_comfyui_essentials({"prompt": minimal_prompt})
    assert result["positive_prompts"] == ["great quality, solo"]


def test_extract_negative_prompts(minimal_prompt):
    result = extract_comfyui_essentials({"prompt": minimal_prompt})
    assert result["negative_prompts"] == ["bad quality, blurry"]


def test_extract_prompt_ordering():
    prompt = {
        "1": {"inputs": {"value": "end part"}, "class_type": "Text Multiline", "_meta": {"title": "Positive Prompt End"}},
        "2": {"inputs": {"value": "start part"}, "class_type": "Text Multiline", "_meta": {"title": "Positive Prompt Start"}},
        "3": {"inputs": {"value": "middle part"}, "class_type": "Text Multiline", "_meta": {"title": "Positive Prompt Middle"}},
    }
    result = extract_comfyui_essentials({"prompt": prompt})
    assert result["positive_prompts"] == ["start part", "middle part", "end part"]


def test_extract_image_dimensions(minimal_prompt):
    result = extract_comfyui_essentials({"prompt": minimal_prompt})
    assert result["image_width"] == 512
    assert result["image_height"] == 768


def test_extract_image_dimensions_missing():
    result = extract_comfyui_essentials({"prompt": {}})
    assert result["image_width"] is None
    assert result["image_height"] is None


def test_extract_dimensions_numeric_string():
    prompt = {
        "1": {"inputs": {"value": "1024"}, "class_type": "Basic data handling: IntCreate", "_meta": {"title": "Image Width"}},
        "2": {"inputs": {"value": "768"}, "class_type": "Basic data handling: IntCreate", "_meta": {"title": "Image Height"}},
    }
    result = extract_comfyui_essentials({"prompt": prompt})
    assert result["image_width"] == 1024
    assert isinstance(result["image_width"], int)


def test_extract_styles():
    prompt = {
        "1": {
            "inputs": {"select_styles": ["Style A", "Style B"]},
            "class_type": "easy stylesSelector",
            "_meta": {"title": "Styles"},
        }
    }
    result = extract_comfyui_essentials({"prompt": prompt})
    assert result["styles"] == ["Style A", "Style B"]


def test_extract_empty_prompt():
    result = extract_comfyui_essentials({})
    assert result["model"] is None
    assert result["loras"] == []
    assert result["positive_prompts"] == []
    assert result["negative_prompts"] == []
    assert result["styles"] == []


def test_real_comfyui_example(comfyui_data):
    result = extract_comfyui_essentials(comfyui_data)
    assert result["model"] == "cyberrealisticPony_v8.safetensors"
    assert result["steps"] == 60
    assert result["cfg"] == 7.0
    assert result["seed"] == 174487603130068
    assert result["sampler_name"] == "euler_ancestral"
    assert result["scheduler"] == "normal"
    assert len(result["styles"]) == 6
    # Note: this workflow's Text Multiline nodes use "text" not "value" as their
    # input key, so positive/negative prompts are empty here. The parser extracts
    # correctly from workflows that use "value" (as in the minimal fixture tests).
    assert len(result["positive_prompts"]) == 5
    assert len(result["negative_prompts"]) == 5


def test_find_by_class_type():
    nodes = {
        "1": {"class_type": "KSampler", "inputs": {}},
        "2": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
        "3": {"class_type": "KSampler", "inputs": {}},
    }
    result = _find_by_class_type(nodes, "KSampler")
    assert len(result) == 2


def test_find_by_title_contains():
    nodes = {
        "1": {"_meta": {"title": "Positive Prompt Start"}, "inputs": {}},
        "2": {"_meta": {"title": "Negative Prompt"}, "inputs": {}},
        "3": {"_meta": {"title": "KSampler"}, "inputs": {}},
    }
    result = _find_by_title_contains(nodes, "positive")
    assert len(result) == 1


def test_first_input_value():
    nodes = [
        {"inputs": {"value": "first"}},
        {"inputs": {"value": "second"}},
    ]
    assert _first_input_value(nodes, "value") == "first"
    assert _first_input_value([], "value") is None
    assert _first_input_value(nodes, "missing") is None
