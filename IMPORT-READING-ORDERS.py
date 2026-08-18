import json
import re
import time
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

# The old importer only accepted #123-style numbers. The source also uses
# decimals and suffixes such as #1.5, #34.1 and #8.NOW.
ISSUE_RE = re.compile(
    r"^(?P<title>.+?)\s+#(?P<number>\d+(?:\.[0-9A-Za-z]+)?)"
    r"(?:\s+\((?P<year>19\d{2}|20\d{2})\))?"
    r"(?:\s*[-–—]\s*(?P<note>.*))?$"
)

MINIMUMS = {
    "x-men": 500,
    "avengers": 500,
    "fantastic-four": 300,
    "daredevil": 300,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ComicOrdersImporter/2.0; "
        "+https://github.com/)"
    )
}

def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()

def extract_issue_lines(soup):
    """
    Extract text in reading-order sequence.

    The source is currently rendered as a sequence of issue lines. We avoid
    scraping navigation/sidebar elements and begin at "Single Issues".
    """
    root = soup.find("main") or soup.body or soup

    # Remove elements that are clearly navigation/UI and can introduce false
    # positives or duplicate text.
    for tag in root.select(
        "nav, header, footer, script, style, noscript, form, "
        ".sidebar, .comments, .comment"
    ):
        tag.decompose()

    text_lines = [clean(x) for x in root.get_text("\n").splitlines()]
    text_lines = [x for x in text_lines if x]

    try:
        start = next(
            i for i, line in enumerate(text_lines)
            if line.lower() == "single issues"
        )
        text_lines = text_lines[start + 1:]
    except StopIteration:
        # Keep working if the site changes the label, but still filter obvious
        # UI strings below.
        pass

    return text_lines

def parse_page(slug, url):
    last_error = None

    for attempt in range(3):
        try:
            response = requests.get(
                url,
                timeout=60,
                headers=HEADERS,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            break
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"Could not fetch {url}: {last_error}")

    lines = extract_issue_lines(soup)

    records = []
    seen_exact = set()

    ignored_exact = {
        "ongoing series",
        "limited series",
        "one-shots",
        "comments",
        "single issues",
    }

    for line in lines:
        low = line.lower()

        # Skip source navigation/instruction lines.
        if low in ignored_exact or low.startswith("alternate starting point:"):
            continue
        if low.startswith("read ") and " here" in low:
            continue
        if low.startswith("after ") and " the series " in low:
            continue

        match = ISSUE_RE.match(line)
        if not match:
            continue

        title = clean(match.group("title"))
        raw_number = match.group("number")
        year_text = match.group("year")
        note = clean(match.group("note"))

        # A few source lines contain malformed OCR-like spacing, e.g. "#1 1".
        # Do not silently reinterpret arbitrary text; only normalize the
        # specific trailing duplicate-digit pattern when it is unambiguous.
        if raw_number.isdigit() and line.endswith(" " + raw_number[-1]):
            candidate = line[:-2].rstrip()
            retry = ISSUE_RE.match(candidate)
            if retry:
                line = candidate
                match = retry
                title = clean(match.group("title"))
                raw_number = match.group("number")
                year_text = match.group("year")
                note = clean(match.group("note"))

        key = (
            title.casefold(),
            raw_number.casefold(),
            year_text or "",
            note.casefold(),
        )
        if key in seen_exact:
            continue
        seen_exact.add(key)

        year = int(year_text) if year_text else None
        decade = f"{year // 10 * 10}s" if year else ""

        # Keep the source wording as the display name. The app can derive
        # title/decade/etc. later if a field is blank.
        records.append({
            "id": f"{slug}-{len(records)+1:05d}",
            "name": line,
            "title": title,
            "issueNumber": raw_number,
            "year": year,
            "decade": decade,
            "writer": "",
            "artist": "",
            "storyline": "",
            "note": note,
            "statusType": (
                "optional" if "optional" in note.casefold() else "essential"
            ),
            "universe": (
                "alternate"
                if "alternate universe" in note.casefold()
                else "main"
            ),
            "readLinks": [],
            "wikiUrl": "",
        })

    if len(records) < MINIMUMS[slug]:
        raise RuntimeError(
            f"{slug}: only parsed {len(records)} entries from {url}. "
            f"Refusing to overwrite the existing file; minimum is "
            f"{MINIMUMS[slug]}."
        )

    return records

def atomic_write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp.replace(path)

def main():
    library_path = ROOT / "library.json"
    library = json.loads(library_path.read_text(encoding="utf-8"))

    for entry in library:
        slug = entry["id"]

        # Spider-Man is intentionally preserved because it contains the
        # affiliate/Masterworks data. Never overwrite it with this importer.
        if slug == "spider-man":
            continue

        if slug not in SOURCES:
            continue

        target = ROOT / entry["data"]

        # Keep a dated backup before replacing a dataset.
        if target.exists():
            backup = target.with_suffix(target.suffix + ".before-import")
            backup.write_bytes(target.read_bytes())

        records = parse_page(slug, SOURCES[slug])

        # If an existing dataset is already much larger, treat a smaller
        # scrape as suspicious and refuse to replace it.
        if target.exists():
            try:
                old = json.loads(target.read_text(encoding="utf-8"))
                old_count = len(old) if isinstance(old, list) else 0
            except Exception:
                old_count = 0

            if old_count >= 100 and len(records) < old_count * 0.75:
                raise RuntimeError(
                    f"{slug}: new parse has {len(records)} entries but the "
                    f"existing file has {old_count}; refusing a >25% regression."
                )

        atomic_write_json(target, records)

        entry["ready"] = True
        entry["count"] = len(records)
        entry["lastImportedSource"] = SOURCES[slug]

        print(f"{slug}: imported {len(records)} entries")

    atomic_write_json(library_path, library)
    print("Import complete.")

if __name__ == "__main__":
    main()
