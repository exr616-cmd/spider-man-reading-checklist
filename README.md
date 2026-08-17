# Spider-Man Reading Checklist v4

Replace `index.html`, `manifest.json`, and `sw.js` in the existing GitHub Pages repository. Keep your existing `data.json`, `background.jpg`, and icon files.

New in v4:
- Click an issue to open an Issue Details panel.
- Search Marvel and Marvel Unlimited for the issue.
- Search for legitimate editions elsewhere.
- Open a Marvel Database Wiki search (or a verified `wikiUrl` if present in data).
- Optional verified `readLinks` and `wikiUrl` fields are supported in data.json.
- Improved service-worker update behavior so new app files replace old cached files without deleting reading progress.

All functionality is static HTML/CSS/JavaScript and works on GitHub Pages.


## v5 interaction update
- Tapping anywhere on an issue opens its details panel.
- Tapping the checkbox only checks/unchecks the issue and does not open the panel.

## v6 checkbox update

The checkbox is now a custom Spider-Man symbol using `spider-check.png`.

- Unchecked: empty outlined circle.
- Checked: uploaded red Spider-Man symbol.
- Tapping the symbol checks/unchecks the issue.
- Tapping the rest of the issue opens the Issue Details panel.
- Existing reading progress is preserved.

## v7 Marvel library

The app now has a Marvel Reading Tracker library with:
- Spider-Man (existing checklist)
- X-Men
- Avengers
- Fantastic Four
- Daredevil

The new character/team source cards link directly to their ComicBookReadingOrders.com reading-order pages. Their full checklist datasets should be imported and verified separately rather than inventing issue metadata.
