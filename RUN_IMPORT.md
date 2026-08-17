# Marvel Reading Tracker — GitHub Actions setup

The automation file is:

`UPDATE-READING-ORDERS.yml`

GitHub requires it to live at exactly:

`.github/workflows/update-reading-orders.yml`

The ZIP also contains the correct `.github/workflows/` folder already.

## If GitHub's upload screen lets you upload folders

Upload the `.github` folder and `tools` folder from the ZIP.

## If GitHub only lets you upload individual files

1. Open your repository.
2. Choose **Add file → Create new file**.
3. In the filename box, type exactly:

`.github/workflows/update-reading-orders.yml`

4. Open `UPDATE-READING-ORDERS.yml` from this ZIP, copy all of its contents, and paste them into the GitHub editor.
5. Commit the new file.
6. Do the same for:

`tools/import_reading_orders.py`

7. Go to **Actions**.
8. You should now see **Update Marvel Reading Orders**.
9. Open it and choose **Run workflow**.

Do NOT name the workflow file just `UPDATE-READING-ORDERS.yml` inside the repository. The top-level copy is provided only to make it easy to find on a phone; GitHub needs the `.github/workflows/` location for Actions to recognize it.
