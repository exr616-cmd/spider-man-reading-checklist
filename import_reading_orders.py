import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

SOURCES = {
    "x-men": "https://comicbookreadingorders.com/marvel/characters/x-men-reading-order/",
    "avengers": "https://comicbookreadingorders.com/marvel/characters/avengers-reading-order/",
    "fantastic-four": "https://comicbookreadingorders.com/marvel/characters/fantastic-four-reading-order/",
    "daredevil": "https://comicbookreadingorders.com/marvel/characters/daredevil-reading-order/",
}

ISSUE_RE = re.compile(
    r"^(?P<title>.+?)\s+#(?P<number>\d+)"
    r"(?:\s+\((?P<year>19\d{2}|20\d{2})\))?"
    r"(?:\s*[-–—]\s*(?P<note>.*))?$",
    re.UNICODE,
)

IGNORE_TITLES = {
    "ongoing series", "limited series", "one-shots",
    "single issues", "comments"
}

def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()

def matching_issue_texts(soup):
    # Some source entries are assembled from nested HTML nodes. Matching the
    # complete visible text of the element avoids the partial/random imports
    # produced by splitting the page into individual text nodes.
    tags = soup.find_all(["p", "li", "div", "a", "span", "h4", "h5", "h6"])
    matches = []

    for element in tags:
        text = clean(element.get_text(" ", strip=True))
        if not text or not ISSUE_RE.match(text):
            continue

        child_is_issue = False
        for child in element.find_all(["p", "li", "div", "a", "span", "h4", "h5", "h6"]):
            child_text = clean(child.get_text(" ", strip=True))
            if child_text and ISSUE_RE.match(child_text):
                child_is_issue = True
                break

        if not child_is_issue:
            matches.append(text)

    return matches

def parse_page(slug, url):
    response = requests.get(
        url,
        timeout=60,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/126 Safari/537.36 "
                "MarvelReadingTracker/1.0"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    seen = set()

    for line in matching_issue_texts(soup):
        match = ISSUE_RE.match(line)
        if not match:
            continue

        title = clean(match.group("title"))
        number = int(match.group("number"))
        year = match.group("year")
        note = clean(match.group("note"))

        if title.lower() in IGNORE_TITLES:
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

    minimums = {
        "x-men": 100,
        "avengers": 100,
        "fantastic-four": 50,
        "daredevil": 50,
    }

    for entry in library:
        slug = entry["id"]
        if slug == "spider-man":
            continue

        data = parse_page(slug, SOURCES[slug])

        # Never replace the database with a suspiciously small scrape.
        minimum = minimums[slug]
        if len(data) < minimum:
            raise RuntimeError(
                f"{slug}: only parsed {len(data)} issues; expected at least "
                f"{minimum}. Aborting update."
            )

        (ROOT / entry["data"]).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        entry["ready"] = True
        entry["count"] = len(data)
        entry["lastImportedSource"] = SOURCES[slug]
        print(f"{slug}: imported {len(data)} issues")

    library_path.write_text(
        json.dumps(library, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
