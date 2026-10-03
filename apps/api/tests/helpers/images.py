"""Deterministic in-memory image bytes for API tests."""

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def minimal_png_bytes() -> bytes:
    """Small valid PNG without relying on OCR."""
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(240, 240, 240)).save(buffer, format="PNG")
    return buffer.getvalue()


def png_with_text(text: str, width: int = 640, height: int = 200) -> bytes:
    """PNG containing rendered text (for optional live Tesseract tests)."""
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    draw.text((16, 16), text, fill=(0, 0, 0), font=font)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
