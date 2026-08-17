#!/usr/bin/env python3
"""
Add X-Men era categories to an existing x-men.json without changing the
existing reading order or metadata.

Usage:
    python categorize_xmen.py x-men.json x-men-categorised.json

The script preserves every existing field and only adds/updates:
    "category": "..."

If an entry has no year, the script uses the nearest known year in the
reading order. This is intentionally conservative and is documented below.
"""

import json
import sys
from pathlib import Path


CATEGORIES = [
    "Original X-Men",
    "The New X-Men",
    "The Claremont Era",
    "The 1990s X-Men",
    "The New X-Men Era",
    "The Decimation Era",
    "Utopia & Schism",
    "Avengers vs. X-Men & Aftermath",
    "The Time-Displaced X-Men",
    "ResurrXion",
    "The Late 2010s",
    "The Krakoa Era",
    "From the Ashes",
    "Modern X-Men",
]


def nearest_year(entries, index):
    """Find the nearest explicit year without changing the source data."""
    if entries[index].get("year") is not None:
        return entries[index]["year"]

    for distance in range(1, len(entries)):
        left = index - distance
        right = index + distance

        if left >= 0 and entries[left].get("year") is not None:
            return entries[left]["year"]

        if right < len(entries) and entries[right].get("year") is not None:
            return entries[right]["year"]

    return None


def category_for(entry, year):
    """Assign one broad, mutually exclusive era category."""

    title = str(entry.get("title") or "").lower()
    name = str(entry.get("name") or "").lower()

    # Modern title-specific eras first.
    if year is not None and year >= 2024:
        return "From the Ashes"

    if year is not None and 2019 <= year <= 2023:
        return "The Krakoa Era"

    # ResurrXion and the late 2010s.
    if year is not None and year in (2017, 2018):
        return "ResurrXion"

    if year is not None and 2015 <= year <= 2016:
        return "The Late 2010s"

    # All-New X-Men and the time-displaced original five.
    if "all-new x-men" in title or "all-new x-men" in name:
        return "The Time-Displaced X-Men"

    if year is not None and 2012 <= year <= 2014:
        return "Avengers vs. X-Men & Aftermath"

    if year is not None and 2011 <= year <= 2012:
        return "Utopia & Schism"

    if year is not None and 2005 <= year <= 2010:
        return "The Decimation Era"

    if year is not None and 2001 <= year <= 2004:
        return "The New X-Men Era"

    if year is not None and 1990 <= year <= 2000:
        return "The 1990s X-Men"

    # Original publication eras.
    if year is not None and year <= 1974:
        return "Original X-Men"

    if year is not None and 1975 <= year <= 1979:
        return "The New X-Men"

    if year is not None and 1980 <= year <= 1989:
        return "The Claremont Era"

    # If a year is genuinely unavailable, use recognizable title cues.
    if "new x-men" in title or "new x-men" in name:
        return "The New X-Men Era"

    if "all-new x-men" in title or "all-new x-men" in name:
        return "The Time-Displaced X-Men"

    return "Modern X-Men"


def main():
    if len(sys.argv) != 3:
        print("Usage: python categorize_xmen.py x-men.json x-men-categorised.json")
        raise SystemExit(2)

    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])

    with source.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError("Expected x-men.json to contain a top-level JSON array.")

    result = []

    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {index} is not a JSON object.")

        updated = dict(entry)
        year = nearest_year(data, index)
        updated["category"] = category_for(updated, year)
        result.append(updated)

    with destination.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    counts = {}
    for entry in result:
        category = entry["category"]
        counts[category] = counts.get(category, 0) + 1

    print(f"Wrote {len(result)} entries to {destination}")
    print("\nCategory counts:")
    for category in CATEGORIES:
        if category in counts:
            print(f"  {category}: {counts[category]}")


if __name__ == "__main__":
    main()
