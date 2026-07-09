# Scripts

One-off dev and exploration scripts. **Do not** add scripts here that
users need — those belong in `src/hideout_art/` as proper modules with
tests. This directory is for things like:

- bulk-rebuilding previews
- scraping hashes from a folder of `.hideout` exports
- ad-hoc analysis of an unusual file

Scripts here may depend on `matplotlib`, `pillow`, etc. without being
declared in `pyproject.toml`.

## Available scripts

| File | Purpose |
|---|---|
| `bulk_preview.py` | Render PNGs for every `.hideout` in a folder |
| `scrape_hashes.py` | Walk a folder of exports and print unknown hashes |

These are illustrative; add your own as needed.
