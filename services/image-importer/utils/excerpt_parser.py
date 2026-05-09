from __future__ import annotations

from typing import Any, Dict, List, Optional


def _prompt_nodes(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return data.get("prompt", {})


def _find_by_class_type(nodes: Dict[str, Dict[str, Any]], class_type: str) -> List[Dict[str, Any]]:
    return [node for node in nodes.values() if node.get("class_type") == class_type]


def _find_by_title_contains(nodes: Dict[str, Dict[str, Any]], needle: str) -> List[Dict[str, Any]]:
    needle_lower = needle.lower()
    return [
        node for node in nodes.values()
        if needle_lower in node.get("_meta", {}).get("title", "").lower()
    ]


def _node_text(node: Dict[str, Any]) -> str:
    """Return the text content of a prompt node, checking both 'value' and 'text' keys."""
    inputs = node.get("inputs", {})
    return inputs.get("value") or inputs.get("text") or ""


def _first_input_value(nodes: List[Dict[str, Any]], key: str) -> Optional[Any]:
    for node in nodes:
        value = node.get("inputs", {}).get(key)
        if value is not None:
            return value
    return None


def _resolve_ref(nodes: Dict[str, Dict[str, Any]], value: Any) -> Any:
    """
    If value is a ComfyUI node reference [node_id, output_slot], follow it once
    and return the resolved scalar (seed, value, number …).  Returns value as-is
    if it is not a reference or the target node has no recognisable scalar.
    """
    if not (isinstance(value, list) and len(value) == 2):
        return value
    ref_id = str(value[0])
    ref_node = nodes.get(ref_id)
    if ref_node is None:
        return value
    inputs = ref_node.get("inputs", {})
    for key in ("seed", "value", "number", "int"):
        v = inputs.get(key)
        if v is not None and not isinstance(v, list):
            return v
    return value


def extract_comfyui_essentials(data: Dict[str, Any]) -> Dict[str, Any]:
    nodes = _prompt_nodes(data)

    checkpoint_nodes = _find_by_class_type(nodes, "CheckpointLoaderSimple")
    lora_nodes = _find_by_class_type(nodes, "LoraLoader")
    ksampler_nodes = _find_by_class_type(nodes, "KSampler")
    style_nodes = _find_by_class_type(nodes, "easy stylesSelector")

    positive_nodes = _find_by_title_contains(nodes, "positive")
    negative_nodes = _find_by_title_contains(nodes, "negative")
    width_nodes = _find_by_title_contains(nodes, "image width")
    height_nodes = _find_by_title_contains(nodes, "image height")

    model_name = _first_input_value(checkpoint_nodes, "ckpt_name")

    loras = []
    for node in lora_nodes:
        inputs = node.get("inputs", {})
        loras.append(
            {
                "name": inputs.get("lora_name"),
                "strength_model": inputs.get("strength_model"),
                "strength_clip": inputs.get("strength_clip"),
            }
        )

    def prompt_sort_key(node: Dict[str, Any]) -> int:
        title = node.get("_meta", {}).get("title", "").lower()
        if "start" in title:
            return 0
        if "middle" in title:
            return 1
        if "end" in title:
            return 2
        return 99

    positive_prompts = [
        _node_text(node)
        for node in sorted(positive_nodes, key=prompt_sort_key)
    ]

    negative_prompts = [
        _node_text(node)
        for node in sorted(negative_nodes, key=prompt_sort_key)
    ]

    styles: List[str] = []
    for node in style_nodes:
        selected = node.get("inputs", {}).get("select_styles", [])
        if isinstance(selected, list):
            styles.extend(selected)

    sampler = None
    cfg = None
    steps = None
    scheduler = None
    seed = None
    if ksampler_nodes:
        ks_inputs = ksampler_nodes[0].get("inputs", {})
        sampler = ks_inputs.get("sampler_name")
        cfg = ks_inputs.get("cfg")
        steps = ks_inputs.get("steps")
        scheduler = ks_inputs.get("scheduler")
        raw_seed = ks_inputs.get("seed")
        seed = _resolve_ref(nodes, raw_seed)

    width = _first_input_value(width_nodes, "value")
    height = _first_input_value(height_nodes, "value")

    try:
        width = int(width) if width is not None else None
    except (TypeError, ValueError):
        pass

    try:
        height = int(height) if height is not None else None
    except (TypeError, ValueError):
        pass

    return {
        "model": model_name,
        "loras": loras,
        "positive_prompts": positive_prompts,
        "negative_prompts": negative_prompts,
        "styles": styles,
        "image_width": width,
        "image_height": height,
        "sampler_name": sampler,
        "cfg": cfg,
        "steps": steps,
        "scheduler": scheduler,
        "seed": seed,
    }
