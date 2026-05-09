from PIL import Image as PILImage


def read_image_size(path: str) -> tuple[int, int] | tuple[None, None]:
    try:
        with PILImage.open(path) as img:
            return img.size  # (width, height)
    except Exception:
        return None, None
