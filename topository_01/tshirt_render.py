from PIL import Image, ImageChops
import os


def hex_to_rgb(hex_colour):
    hex_colour = hex_colour.strip().lstrip("#")
    return (
        int(hex_colour[0:2], 16),
        int(hex_colour[2:4], 16),
        int(hex_colour[4:6], 16),
    )


def autocrop(img, white_threshold=250):
    """
    Trim away transparent borders, then remove any solid near-white band at
    the bottom of the design image. This helps avoid faint white stripes
    introduced by export padding, without requiring changes to the source art.
    """
    # Ensure RGBA
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # --- Step 1: trim fully transparent border using alpha ---
    alpha = img.split()[-1]
    alpha_bbox = alpha.getbbox()
    if alpha_bbox:
        img = img.crop(alpha_bbox)
        alpha = img.split()[-1]

    # --- Step 2: trim uniform near-white rows from the bottom ---
    w, h = img.size
    bottom = h

    # Walk upwards from the last row until we hit a row that is not "all white"
    for y in range(h - 1, -1, -1):
        row = img.crop((0, y, w, y + 1))
        pixels = row.getdata()

        all_white = True
        for (r, g, b, a) in pixels:
            # Ignore fully transparent pixels; focus on visible ones
            if a > 10 and (r < white_threshold or g < white_threshold or b < white_threshold):
                all_white = False
                break

        if all_white:
            bottom = y
        else:
            break

    if bottom < h:
        img = img.crop((0, 0, w, bottom))

    return img


def tint_shirt(base_img, mask_img, rgb_colour):
    base_rgba = base_img.convert("RGBA")
    mask_l = mask_img.convert("L")

    solid = Image.new("RGBA", base_rgba.size, rgb_colour + (255,))
    tinted = ImageChops.multiply(base_rgba, solid)

    transparent = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    return Image.composite(tinted, transparent, mask_l)


def place_design_on_shirt(shirt_img, design_img, side_margin_frac, chest_y_frac):
    sw, sh = shirt_img.size
    dw, dh = design_img.size

    avail_w = int(sw * (1 - 2 * side_margin_frac))
    scale = avail_w / dw

    target_w = avail_w
    target_h = int(dh * scale)

    resized = design_img.resize((target_w, target_h), Image.LANCZOS)

    x = int(sw * side_margin_frac)
    y = int(sh * chest_y_frac)

    shirt = shirt_img.convert("RGBA")
    shirt.paste(resized, (x, y), resized)
    return shirt


def render_tshirt(base_path, mask_path, design_path, colour_hex,
                  side_margin_frac=0.31, chest_y_frac=0.28):
    """
    Returns a PIL Image containing the final composited T-shirt.
    """

    # Load assets
    base = Image.open(base_path)
    mask = Image.open(mask_path)

    # Load design and AUTOCROP
    design = Image.open(design_path)
    design = autocrop(design)        # <---- IMPORTANT FIX

    rgb = hex_to_rgb(colour_hex)

    tinted = tint_shirt(base, mask, rgb)
    final = place_design_on_shirt(tinted, design,
                                  side_margin_frac,
                                  chest_y_frac)

    # Add white background to eliminate any transparency
    bg = Image.new("RGBA", final.size, (249, 249, 249, 255))
    return Image.alpha_composite(bg, final)