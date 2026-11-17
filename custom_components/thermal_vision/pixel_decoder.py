"""Decode legacy or full-resolution AMG8833 pixel frames without HA dependencies."""

import base64


def decode_pixels(encoded: str, count: int = 64) -> list[float]:
    """Decode unsigned legacy bytes or little-endian signed-magnitude registers.

    Raise ValueError for malformed Base64 or an unexpected frame length.
    """
    if not isinstance(count, int) or count <= 0:
        raise ValueError("Pixel count must be a positive integer")
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) == count:
        return [value * 0.25 for value in raw]
    if len(raw) != count * 2:
        raise ValueError("Unexpected thermal frame length")
    values = [raw[i] | (raw[i + 1] << 8) for i in range(0, len(raw), 2)]
    return [(-1 if value & 0x800 else 1) * (value & 0x7FF) * 0.25 for value in values]
