# Marvel Reading Tracker v9

This version adds a GitHub Actions importer for the four supplied ComicBookReadingOrders pages.

Sources:
- X-Men: https://comicbookreadingorders.com/marvel/characters/x-men-reading-order/
- Avengers: https://comicbookreadingorders.com/marvel/characters/avengers-reading-order/
- Fantastic Four: https://comicbookreadingorders.com/marvel/characters/fantastic-four-reading-order/
- Daredevil: https://comicbookreadingorders.com/marvel/characters/daredevil-reading-order/

## How to run the full import

1. Upload the v9 files to the repository.
2. Open the repository's **Actions** tab.
3. Select **Update Marvel Reading Orders**.
4. Press **Run workflow**.
5. GitHub will fetch the four source pages, parse their issue lists, write:
   - `x-men.json`
   - `avengers.json`
   - `fantastic-four.json`
   - `daredevil.json`
6. The workflow commits the generated JSON back to the repository.
7. GitHub Pages then serves the updated static data.

It also runs automatically once a week.

The importer intentionally leaves writer/artist fields blank unless the source reading-order page itself supplies those credits. It does not invent metadata.

The parser preserves reading-order sequence, issue names, issue numbers, publication years when shown, source notes, and alternate-universe/optional flags.

## v10 library cards

The home page now supports a separate local image for every hero/team:
- `images/spider-man.jpg`
- `images/x-men.jpeg`
- `images/avengers.jpg`
- `images/fantastic-four.jpg`
- `images/daredevil.webp`

Only the currently selected library card is highlighted red. All other cards are visually unhighlighted.

Images are local files, so this remains fully compatible with GitHub Pages.

## v12 full-import fix

The previous importer could capture only a small/random subset because some issue titles are assembled from multiple HTML elements.

v12 parses the complete visible text of issue elements and refuses to overwrite the database if a scrape is suspiciously small.

After uploading v12:
**Actions → Update Marvel Reading Orders → Run workflow**

The workflow prints the number of issues imported and requires at least:
- X-Men: 100
- Avengers: 100
- Fantastic Four: 50
- Daredevil: 50
