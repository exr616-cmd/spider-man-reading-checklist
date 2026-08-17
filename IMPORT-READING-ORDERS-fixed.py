import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent

SOURCES = {
    "x-men": "https://comicbookreadingorders.com/marvel/characters/x-men-reading-order/",
    "avengers": "https://comicbookreadingorders.com/marvel/characters/avengers-reading-order/",
    "fantastic-four": "https://comicbookreadingorders.com/marvel/characters/fantastic-four-reading-order/",
    "daredevil": "https://comicbookreadingorders.com/marvel/characters/daredevil-reading-order/",
}

# The site contains issue entries as separate rendered lines. This deliberately
# does NOT require a year, and it accepts decimal/lettered issue numbers too.
ISSUE_RE = re.compile(
    r"^(?P<title>.+?)\s+#(?P<number>\d+(?:\.\d+)?(?:\.[A-Z]+)?)"
    r"(?:\s*\((?P<year>19\d{2}|20\d{2})\))?"
    r"(?:\s*[-–—]\s*(?P<note>.*))?$",
    re.IGNORECASE,
)

SKIP_EXACT = {
    "ongoing series",
    "limited series",
    "one-shots",
    "comments",
    "single issues",
}

def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()

def get_page(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def candidate_lines(soup):
    # Prefer the WordPress article content, but fall back to the whole body.
    content = (
        soup.select_one(".entry-content")
        or soup.select_one(".post-content")
        or soup.select_one("article")
        or soup.body
        or soup
    )

    # stripped_strings preserves the individual rendered text chunks instead
    # of collapsing the whole page into one giant string.
    raw = [clean(x) for x in content.stripped_strings]

    # Some themes put several entries into the same text chunk. Split those
    # only where a new issue-like entry starts.
    out = []
    for chunk in raw:
        if not chunk:
            continue

        # Normalize separators first.
        chunk = chunk.replace("\xa0", " ")

        # If the chunk contains multiple issue entries, split before each
        # capitalized title that ends in #number.
        parts = re.split(
            r"(?<=\S)\s+(?=(?:[A-Z][^#\n]{0,100}?)\s+#\d)",
            chunk
        )
        out.extend(clean(p) for p in parts if clean(p))

    return out

def parse_page(slug, url):
    soup = get_page(url)
    lines = candidate_lines(soup)

    records = []
    seen = set()

    for line in lines:
        match = ISSUE_RE.match(line)
        if not match:
            continue

        title = clean(match.group("title"))
        number = match.group("number")
        year = match.group("year")
        note = clean(match.group("note"))

        if title.lower() in SKIP_EXACT:
            continue

        # Reject obvious page/navigation text.
        if len(title) > 120 or title.lower().startswith(("read ", "alternate starting point")):
            continue

        key = (title.lower(), number.lower(), year or "", note.lower())
        if key in seen:
            continue
        seen.add(key)

        if year:
            decade = f"{int(year)//10*10}s"
        else:
            decade = ""

        # Use an integer when possible; preserve special numbers such as 1.1.
        if number.isdigit():
            issue_number = int(number)
        else:
            issue_number = number

        records.append({
            "id": f"{slug}-{len(records)+1:05d}",
            "name": line,
            "title": title,
            "issueNumber": issue_number,
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

    return records

def main():
    library_path = ROOT / "library.json"
    library = json.loads(library_path.read_text(encoding="utf-8"))

    # These are deliberately conservative. A result below these values is
    # treated as a failed/partial scrape and will NOT overwrite the database.
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

        url = SOURCES[slug]
        data = parse_page(slug, url)

        if len(data) < minimums[slug]:
            raise RuntimeError(
                f"{slug}: only found {len(data)} issues. "
                f"The source page should contain a much larger reading order. "
                f"No files were replaced. Check the GitHub Actions log."
            )

        output = ROOT / entry["data"]
        output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        entry["ready"] = True
        entry["count"] = len(data)
        entry["lastImportedSource"] = url

        print(f"{slug}: imported {len(data)} issues")

    library_path.write_text(
        json.dumps(library, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
