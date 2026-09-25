import re
import json
from pathlib import Path

# Adjust these if needed
INPUT_PATH = Path("colours_raw.txt")
OUTPUT_PATH = Path("../static/topository/colours_parsed.json")


def parse_colours(text):
    """
    Parse colour hex + name pairs from a messy JSON-ish string.

    Looks for fragments like:
    "c":[["#00A9E0","Arctic Blue ",null,null]]

    Returns a dict: { "Arctic Blue": "#00A9E0", ... }
    """
    # Match: "c":[["<hex>", "<name>", ...
    pattern = r'"c"\s*:\s*\[\s*\[\s*"(#[0-9A-Fa-f]{6})"\s*,\s*"([^"]+)"'

    matches = re.findall(pattern, text)

    colours = {}
    for hex_code, name in matches:
        name_clean = name.strip()
        # On duplicates, keep the first one we saw
        if name_clean not in colours:
            colours[name_clean] = hex_code

    return colours


def main():
    if not INPUT_PATH.exists():
        print("Input file not found:", INPUT_PATH)
        return

    raw = INPUT_PATH.read_text(encoding="utf-8")
    colours = parse_colours(raw)

    print("Found %d colours" % len(colours))
    print()
    print("As a Python dict:")
    print(colours)
    print()

    # Also save as pretty JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(colours, indent=2), encoding="utf-8")
    print("Wrote JSON to %s" % OUTPUT_PATH)


if __name__ == "__main__":
    main()