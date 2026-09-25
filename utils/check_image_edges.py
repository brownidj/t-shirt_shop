#!/usr/bin/env python3
"""Review product images against a black background, one image at a time.

Run from the ``Topository_01`` directory:

    python3 utils/check_image_edges.py

Controls: N = next, P = previous, Q = quit.
"""

from pathlib import Path

from PIL import Image, ImageOps


IMAGE_DIRECTORY = Path(
    "/Users/david/PycharmProjects/DjangoProject/Topository_01/media/images/products/2025/12"
)
IMAGE_EXTENSIONS = {".jpg", ".png"}
BACKGROUND = (0, 0, 0, 255)
PADDING = 40


def image_paths(directory: Path) -> list[Path]:
    """Return the supported images in a stable, alphabetical order."""
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def black_background_preview(path: Path) -> Image.Image:
    """Place an image on a black opaque canvas so edge artefacts are visible."""
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")

    preview = Image.new(
        "RGBA",
        (image.width + PADDING * 2, image.height + PADDING * 2),
        BACKGROUND,
    )
    preview.alpha_composite(image, (PADDING, PADDING))
    return preview.convert("RGB")


def show_images(paths: list[Path]) -> None:
    """Show one preview at a time using Pillow's platform image viewer."""
    index = 0
    print("Controls: n = next, p = previous, q = quit")

    while True:
        path = paths[index]
        print(f"\n[{index + 1}/{len(paths)}] {path.name}")
        black_background_preview(path).show(title=f"{index + 1}/{len(paths)} — {path.name}")

        command = input("Command: ").strip().lower()
        if command in {"q", "quit", "exit"}:
            return
        if command in {"n", "next", ""}:
            index = (index + 1) % len(paths)
        elif command in {"p", "prev", "previous"}:
            index = (index - 1) % len(paths)


def main() -> None:
    if not IMAGE_DIRECTORY.is_dir():
        raise SystemExit(f"Image directory not found: {IMAGE_DIRECTORY}")

    paths = image_paths(IMAGE_DIRECTORY)
    if not paths:
        raise SystemExit(f"No .jpg or .png files found in: {IMAGE_DIRECTORY}")

    print(f"Found {len(paths)} images in {IMAGE_DIRECTORY}")
    show_images(paths)


if __name__ == "__main__":
    main()
