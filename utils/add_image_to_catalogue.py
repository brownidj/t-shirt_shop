#!/usr/bin/env python3
"""Add PDF or PNG artwork as a public design in catalogue categories.

Usage:
/Users/david/PycharmProjects/DjangoProject/Topository_01/.venv/bin/python \
  /Users/david/PycharmProjects/DjangoProject/Topository_01/utils/add_image_to_catalogue.py \
  /Users/david/PycharmProjects/DjangoProject/Topository_01/media/images/products/2025/12/Sagan_01_page_2_inverted.png \
  "[Astrophysics]"

The first PDF page is rendered as a 640px-wide PNG. PNG input is used as-is.
If a source is outside MEDIA_ROOT, a PNG copy is stored under
``media/images/products/<year>/<month>/``. The filename supplies the product
title (for example, ``yunnanzoon_01.pdf`` becomes ``Yunnanzoon``).
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "topository_01.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402
from oscar.core.loading import get_model  # noqa: E402


Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
Category = get_model("catalogue", "Category")
ProductImage = get_model("catalogue", "ProductImage")


def parse_categories(value):
    """Parse ``[Category one, Category two]`` into public categories."""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    names = [name.strip() for name in value.split(",") if name.strip()]
    if not names:
        raise argparse.ArgumentTypeError("provide at least one category")

    categories_by_name = {
        category.name.casefold(): category
        for category in Category.objects.filter(is_public=True)
    }
    missing = [name for name in names if name.casefold() not in categories_by_name]
    if missing:
        raise argparse.ArgumentTypeError(
            "unknown public categor{}: {}".format(
                "y" if len(missing) == 1 else "ies", ", ".join(missing)
            )
        )
    return [categories_by_name[name.casefold()] for name in names]


def title_from_path(image_path):
    """Turn ``yunnanzoon_01.pdf`` into the catalogue title ``Yunnanzoon``."""
    stem = image_path.stem
    if stem.rsplit("_", 1)[-1].isdigit():
        stem = stem.rsplit("_", 1)[0]
    return stem.replace("_", " ").strip().title()


def initial_upc(title):
    """Return the next available concise design UPC, e.g. ``P_YUN_01``."""
    letters = "".join(character for character in title.upper() if character.isalnum())
    prefix = (letters[:3] or "ART").ljust(3, "X")
    number = 1
    while True:
        upc = f"P_{prefix}_{number:02d}"
        if not Product.objects.filter(upc=upc).exists():
            return upc
        number += 1


def destination_for(image_path):
    """Choose a MEDIA_ROOT-relative destination for a catalogue PNG."""
    media_root = Path(settings.MEDIA_ROOT).resolve()
    try:
        image_path.relative_to(media_root)
        return image_path.with_suffix(".png")
    except ValueError:
        today = date.today()
        return (
            media_root
            / "images"
            / "products"
            / f"{today:%Y}"
            / f"{today:%m}"
            / f"{image_path.stem}.png"
        )


def render_pdf_as_png(pdf_path, png_path):
    """Render page one with ImageMagick as a 640px-wide, opaque PNG."""
    magick = shutil.which("magick")
    if not magick:
        raise RuntimeError("ImageMagick is required; install a 'magick' command first.")

    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            magick,
            "-density",
            "144",
            f"{pdf_path}[0]",
            "-resize",
            "640x",
            "-background",
            "white",
            "-alpha",
            "remove",
            "-strip",
            f"PNG24:{png_path}",
        ],
        check=True,
    )


def prepare_png(source_path):
    """Render PDF input or make a catalogue-accessible copy of PNG input."""
    png_path = destination_for(source_path)
    if source_path.suffix.lower() == ".pdf":
        render_pdf_as_png(source_path, png_path)
    elif source_path.resolve() != png_path.resolve():
        png_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, png_path)
    return png_path


def add_to_catalogue(source_path, categories):
    """Prepare, create/update the design, categorise it, and re-index it."""
    title = title_from_path(source_path)
    png_path = prepare_png(source_path)

    media_relative_path = png_path.resolve().relative_to(Path(settings.MEDIA_ROOT).resolve())
    image_name = media_relative_path.as_posix()
    designs = ProductClass.objects.get(name="Designs")

    with transaction.atomic():
        product = Product.objects.filter(
            title__iexact=title, product_class=designs
        ).first()
        if product is None:
            product = Product.objects.create(
                upc=initial_upc(title),
                title=title,
                structure=Product.STANDALONE,
                product_class=designs,
                is_public=True,
            )

        product.categories.set(categories)
        image = ProductImage.objects.filter(product=product).order_by("display_order").first()
        if image is None:
            ProductImage.objects.create(
                product=product,
                original=image_name,
                caption=title,
                display_order=0,
            )
        else:
            image.original = image_name
            image.caption = title
            image.save(update_fields=["original", "caption"])

        # Saving after the category relation is set refreshes Haystack's
        # category field, which powers the catalogue category pages.
        product.save(update_fields=["date_updated"])

    return product, png_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="PDF or PNG artwork to add")
    parser.add_argument(
        "categories",
        nargs="+",
        help="Public category list, for example [Paleontology, Scuba]",
    )
    args = parser.parse_args()

    image_path = args.image.expanduser().resolve()
    if not image_path.is_file() or image_path.suffix.lower() not in {".pdf", ".png"}:
        parser.error(f"PDF or PNG not found: {image_path}")

    try:
        categories = parse_categories(" ".join(args.categories))
        product, png_path = add_to_catalogue(image_path, categories)
    except (
        argparse.ArgumentTypeError,
        RuntimeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        parser.error(str(error))

    print(f"Added {product.title} ({product.upc})")
    print(f"Image: {png_path}")
    print("Categories: " + ", ".join(category.name for category in categories))


if __name__ == "__main__":
    main()
