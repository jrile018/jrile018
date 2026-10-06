#!/usr/bin/env python3
"""Prepare source artwork for the animated ASCII renderer.

The default Gators image has a black canvas. This script converts that canvas
to transparency, crops tightly around the mark, centers it on a square canvas,
and applies gentle grayscale normalization. Keeping a real alpha mask lets the
ASCII renderer distinguish intentional black outlines from empty background.

Usage:
    python scripts/prep_photo.py [input.jpg] [output.png]
"""

import os
import sys

from PIL import Image, ImageChops, ImageEnhance, ImageOps


HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "source-gator.jpg"
)
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    HERE, "..", "source-prepped.png"
)

PADDING_RATIO = 0.10
BACKGROUND_BLACK = 7
FULL_OPACITY = 24
CONTRAST = 1.08
BRIGHTNESS = 1.05


def alpha_from_black_background(rgb):
    """Return a soft mask that removes a nearly black image canvas."""
    red, green, blue = rgb.split()
    brightest = ImageChops.lighter(ImageChops.lighter(red, green), blue)

    def opacity(value):
        if value <= BACKGROUND_BLACK:
            return 0
        if value >= FULL_OPACITY:
            return 255
        return round((value - BACKGROUND_BLACK) * 255 / (FULL_OPACITY - BACKGROUND_BLACK))

    return brightest.point(opacity)


def prepare(source):
    rgb = Image.open(source).convert("RGB")
    alpha = alpha_from_black_background(rgb)
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("source artwork contains no non-black subject")

    rgba = rgb.convert("RGBA")
    rgba.putalpha(alpha)
    subject = rgba.crop(bbox)

    width, height = subject.size
    padding = max(20, round(max(width, height) * PADDING_RATIO))
    side = max(width, height) + padding * 2
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.alpha_composite(subject, ((side - width) // 2, (side - height) // 2))

    subject_alpha = canvas.getchannel("A")
    gray = ImageOps.grayscale(canvas)
    gray = ImageOps.autocontrast(gray, cutoff=0.3, mask=subject_alpha)
    gray = ImageEnhance.Contrast(gray).enhance(CONTRAST)
    gray = ImageEnhance.Brightness(gray).enhance(BRIGHTNESS)
    return Image.merge("RGBA", (gray, gray, gray, subject_alpha))


if __name__ == "__main__":
    prepared = prepare(INP)
    prepared.save(OUT)
    print("wrote", OUT, prepared.size)
