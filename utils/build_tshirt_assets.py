#!/usr/bin/env python3
"""
Utility to generate a base PNG and mask PNG for a T-shirt style
from a flat PNG product photo.

Usage (from project root):

    python3 utils/build_tshirt_assets.py --style AS-5001

This will by default:

- Read input PNG from: media/base_style_images/AS-5001.png
- Write outputs to:
    static/topository/tshirts/AS-5001/AS-5001_base.png
    static/topository/tshirts/AS-5001/AS-5001_mask.png

You can override the input and output paths with --input and --output options.

You can then use these in the dynamic renderer.
"""

import argparse
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


BASE_DIR = Path(__file__).resolve().parent.parent


def sample_background_colour(img, border_px=20):
    """
    Estimate background colour by sampling a border region around the edges.
    Assumes the shirt is roughly centred and the background is fairly uniform.
    """
    w, h = img.size
    pixels = img.load()

    samples = []

    # Top and bottom strips
    for y in range(border_px):
        for x in range(w):
            samples.append(pixels[x, y])
    for y in range(h - border_px, h):
        for x in range(w):
            samples.append(pixels[x, y])

    # Left and right strips
    for x in range(border_px):
        for y in range(h):
            samples.append(pixels[x, y])
    for x in range(w - border_px, w):
        for y in range(h):
            samples.append(pixels[x, y])

    # Average RGB
    r_sum = g_sum = b_sum = 0
    count = 0
    for r, g, b in samples:
        r_sum += r
        g_sum += g
        b_sum += b
        count += 1

    if count == 0:
        return (255, 255, 255)

    return (r_sum // count, g_sum // count, b_sum // count)


def build_mask(img, bg_colour, threshold=25, feather_radius=1.5):
    """
    Build a soft mask separating shirt from background.

    - bg_colour: (R, G, B) average background colour
    - threshold: distance in RGB above which a pixel is considered "shirt"
    - feather_radius: Gaussian blur radius to soften edges
    """
    w, h = img.size
    pixels = img.load()

    # Start with a hard mask in L mode (0..255)
    mask = Image.new("L", img.size, 0)
    m_px = mask.load()

    br, bg, bb = bg_colour

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            dr = r - br
            dg = g - bg
            db = b - bb
            dist2 = dr * dr + dg * dg + db * db
            # Compare with threshold^2 in RGB distance space
            if dist2 > threshold * threshold:
                m_px[x, y] = 255
            # else leave as 0 (background)

    # Bright areas of a pale shirt can otherwise be classified as background,
    # producing transparent pinholes inside the garment.  Only fill enclosed
    # background regions; the border-connected background remains transparent.
    inverted = ImageOps.invert(mask)
    ImageDraw.floodfill(inverted, (0, 0), 0)
    mask = ImageChops.lighter(mask, inverted)

    if feather_radius > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather_radius))

    return mask


def build_base(img, mask, contrast=1.35, brightness=1.0):
    """
    Take the original RGB image and the mask, and produce an RGBA base where:

    - Shirt area: original pixels, slightly higher contrast and slightly darker
    - Background: fully transparent

    Returns an RGBA image.
    """
    # Apply gentle contrast / brightness tweaks before alpha-compositing
    enhanced = img.copy()
    enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(brightness)
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=3))

    rgba = enhanced.convert("RGBA")
    r_px = rgba.load()
    m_px = mask.load()
    w, h = rgba.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = r_px[x, y]
            alpha = m_px[x, y]  # 0..255 from mask
            if alpha == 0:
                # Fully transparent background
                r_px[x, y] = (0, 0, 0, 0)
            else:
                # Keep pixel, but use mask's alpha for soft edges
                r_px[x, y] = (r, g, b, alpha)

    return rgba


def main():
    parser = argparse.ArgumentParser(
        description="Generate base + mask PNGs for a T-shirt style from a PNG."
    )
    parser.add_argument("--style", required=True, help="Style code, e.g. AS-5001")
    parser.add_argument(
        "--input",
        required=False,
        help="Path to input PNG (flat shirt photo). Overrides default media/base_style_images/<style>.png",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Output directory for <style>_base.png and <style>_mask.png. Overrides default static/topository/tshirts/<style>",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=12,
        help="RGB distance threshold for separating shirt from background (default: 12)",
    )
    parser.add_argument(
        "--feather",
        type=float,
        default=2.0,
        help="Edge feather (Gaussian blur radius) in pixels (default: 2.0)",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.35,
        help="Contrast multiplier for shirt base (default: 1.35)",
    )
    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0,
        help="Brightness multiplier for shirt base (default: 1.0)",
    )

    args = parser.parse_args()

    style = args.style.strip()

    if args.input:
        input_path = args.input
    else:
        input_path = BASE_DIR / "media" / "base_style_images" / f"{style}.png"

    if args.output:
        out_dir = args.output
    else:
        out_dir = BASE_DIR / "static" / "topository" / "tshirts" / style

    if not Path(input_path).exists():
        raise SystemExit(f"Input file not found: {Path(input_path).resolve()}")

    os.makedirs(str(out_dir), exist_ok=True)

    print("Loading:", input_path)
    img = Image.open(input_path).convert("RGB")

    print("Sampling background colour …")
    bg_colour = sample_background_colour(img)
    print("  Estimated background RGB:", bg_colour)

    print("Building mask …")
    mask = build_mask(
        img,
        bg_colour=bg_colour,
        threshold=args.threshold,
        feather_radius=args.feather,
    )

    print("Building base image …")
    base = build_base(img, mask, contrast=args.contrast, brightness=args.brightness)

    base_filename = f"{style}_base.png"
    mask_filename = f"{style}_mask.png"

    base_path = os.path.join(str(out_dir), base_filename)
    mask_path = os.path.join(str(out_dir), mask_filename)

    print("Saving base:", base_path)
    base.save(base_path, format="PNG")

    print("Saving mask:", mask_path)
    mask.save(mask_path, format="PNG")

    print("Done.")


if __name__ == "__main__":
    main()
