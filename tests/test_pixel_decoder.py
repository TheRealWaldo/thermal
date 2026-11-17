"""Frame-format regression tests; runnable without importing Home Assistant."""

import base64
import importlib.util
from pathlib import Path
import struct
import unittest

SPEC = importlib.util.spec_from_file_location(
    "pixel_decoder",
    Path(__file__).parents[1] / "custom_components/thermal_vision/pixel_decoder.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
decode_pixels = MODULE.decode_pixels


class PixelDecoderTests(unittest.TestCase):
    def test_legacy_frame(self):
        data = bytes([0, 1, 100, 255] + [80] * 60)
        result = decode_pixels(base64.b64encode(data).decode())
        self.assertEqual(len(result), 64)
        self.assertEqual(result[:4], [0, 0.25, 25, 63.75])

    def test_full_frame_signed_magnitude_and_byte_order(self):
        values = [0, 1, 0x804, 0x100, 0x500, 0x7FF, 0xFFF, 0x800] + [100] * 56
        data = b"".join(struct.pack("<H", value) for value in values)
        result = decode_pixels(base64.b64encode(data).decode())
        self.assertEqual(len(result), 64)
        self.assertEqual(result[:8], [0, 0.25, -1, 64, 320, 511.75, -511.75, 0])
        self.assertEqual(result[8:], [25] * 56)

    def test_bad_encoding(self):
        for value in ["bad!", "not base64", "é"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_pixels(value)

    def test_wrong_length(self):
        for length in [0, 1, 63, 65, 127, 129]:
            with self.subTest(length=length), self.assertRaises(ValueError):
                decode_pixels(base64.b64encode(bytes(length)).decode())

    def test_explicit_dimensions(self):
        self.assertEqual(decode_pixels("ZA==", 1), [25])
        self.assertEqual(decode_pixels("AAg=", 1), [0])
        with self.assertRaises(ValueError):
            decode_pixels("", 0)


if __name__ == "__main__":
    unittest.main()
