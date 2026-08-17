import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

SOURCES = {
    "x-men": "https://comicbookreadingorders.com/marvel/characters/x-men-reading-order/",
    "avengers": "https://comicbookreadingorders.com/marvel/characters/avengers-reading-order/",
    "fantastic-four": "https://comicbookreadingorders.com/marvel/characters/fantastic-four-reading-order/",
    "daredevil": "https://comicbookreadingorders.com/marvel/characters/daredevil-reading-order/",
}

# Matches the issue/one-shot/graphic-novel style lines used by the source.
ISSUE_RE = re.compile(
    r"^(?P<title>.+?)\s+#(?P<number>\d+)"
    r"(?:\s+\((?P<year>19\d{2}|20\d{2})\))?"
    r"(?:\s+-\s+(?P<note>.*))?$"
)

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def parse_page(slug, url):
    response = requests.get(
        url,
        timeout=45,
        headers={"User-Agent": "MarvelReadingTracker/1.0 (+GitHub Actions)"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # The reading-order content is represented as text in the page. Using the
    # rendered text rather than brittle CSS classes makes the importer resilient
    # to minor theme changes.
    lines = [clean(x) for x in soup.get_text("\n").splitlines()]
    lines = [x for x in lines if x]

    records = []
    seen = set()

    for line in lines:
        match = ISSUE_RE.match(line)
        if not match:
            continue

        title = clean(match.group("title"))
        number = int(match.group("number"))
        year = match.group("year")
        note = clean(match.group("note"))

        # Avoid navigation/header false positives.
        if title.lower() in {
            "ongoing series", "limited series", "one-shots",
            "single issues", "comments"
        }:
            continue

        key = (title.lower(), number, year or "", note.lower())
        if key in seen:
            continue
        seen.add(key)

        decade = f"{int(year)//10*10}s" if year else ""

        records.append({
            "id": f"{slug}-{len(records)+1:05d}",
            "name": line,
            "title": title,
            "issueNumber": number,
            "year": int(year) if year else None,
            "decade": decade,
            "writer": "",
            "artist": "",
            "storyline": "",
            "note": note,
            "statusType": "optional" if "optional" in note.lower() else "essential",
            "universe": "alternate" if "alternate universe" in note.lower() else "main",
            "readLinks": [],
            "wikiUrl": ""
        })

    if not records:
        raise RuntimeError(f"No issues parsed from {url}")

    return records

def main():
    library_path = ROOT / "library.json"
    library = json.loads(library_path.read_text(encoding="utf-8"))

    for entry in library:
        slug = entry["id"]
        if slug == "spider-man":
            continue

        data = parse_page(slug, SOURCES[slug])
        (ROOT / entry["data"]).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        entry["ready"] = True
        entry["count"] = len(data)
        entry["lastImportedSource"] = SOURCES[slug]

    library_path.write_text(
        json.dumps(library, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
