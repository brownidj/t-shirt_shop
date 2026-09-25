#!/usr/bin/env python3
"""
Simple console menu to run Topository utility scripts.

Run with:
    python3 utils/menu.py
from the project root (Topository_01).
"""

import os
import sys
import django

# --------------------------------------------------------------------
#  Django setup
# --------------------------------------------------------------------
PROJECT_SETTINGS = "topository_01.settings"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PROJECT_SETTINGS)
django.setup()

# --------------------------------------------------------------------
#  Import utility modules (siblings in utils/)
# --------------------------------------------------------------------
# Because this file sits in utils/, Python adds utils/ to sys.path when
# you run `python3 utils/menu.py`, so we can import siblings directly.
# Adjust imports as needed if you add more utilities.
try:
    import update_prices
except ImportError:
    update_prices = None

try:
    import generate_tshirt_variants
except ImportError:
    generate_tshirt_variants = None

try:
    import fix_slugs
except ImportError:
    fix_slugs = None


# --------------------------------------------------------------------
#  Menu configuration
# --------------------------------------------------------------------
def build_menu():
    """
    Return a dict mapping menu keys to (label, callable) pairs.
    Only include options for utilities that imported successfully.
    """
    options = {}

    if update_prices and hasattr(update_prices, "update_prices"):
        options["1"] = (
            "Update prices for all variants of an editable list of design parents",
            update_prices.update_prices,
        )

    if generate_tshirt_variants and hasattr(
            generate_tshirt_variants, "generate_variants"
    ):
        options["2"] = (
            "Generate T-shirt variants (style × colour × size) for selected designs",
            generate_tshirt_variants.generate_variants,
        )

    if fix_slugs and hasattr(fix_slugs, "fix_slugs"):
        options["3"] = (
            "Normalise slugs for design parents (and optionally children)",
            fix_slugs.fix_slugs,
        )

    # You can add more here later, e.g.:
    # if assign_colours and hasattr(assign_colours, "assign_colours"):
    #     options["4"] = (
    #         "Assign T-shirt colour options to a style",
    #         assign_colours.assign_colours,
    #     )

    return options


def print_menu(options):
    print("\n=== Topository Utilities ===\n")
    for key in sorted(options.keys(), key=lambda x: int(x)):
        label, _ = options[key]
        print(f"  {key}. {label}")
    print("\n  0. Quit\n")


def main():
    options = build_menu()

    if not options:
        print("No utilities available. Check imports in utils/menu.py.")
        sys.exit(1)

    while True:
        print_menu(options)
        choice = input("Select an option (number): ").strip().lower()

        if choice in ("0", "q", "quit", "exit"):
            print("Bye.")
            break

        if choice not in options:
            print(f"Unrecognised option: '{choice}'. Try again.\n")
            continue

        label, func = options[choice]
        print(f"\n--- Running: {label} ---\n")

        try:
            func()
        except Exception as e:
            # Keep it simple but visible; you can improve this later.
            print(f"\n⚠ Error while running '{label}': {e}\n")

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()