# Contributing to hideout-art

Thanks for considering a contribution! This project is small, so the
workflow is intentionally lightweight.

## The two things we always need

1. **New `KNOWN_HASHES` entries.** Every time you encounter a decoration
   not in the catalogue, open a PR adding it to
   `src/hideout_art/constants.py`. Include the source hideout name in the
   commit message so others can verify.
2. **Test coverage for new transforms.** If you add a geometric transform,
   add a test that runs it on `tests/data/sample.hideout` and asserts the
   result.

## Setup

```bash
git clone https://github.com/vudirvp-sketch/poe2-hideout-art.git
cd poe2-hideout-art
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest                    # full suite
pytest -k parser          # only parser tests
pytest --cov=hideout_art  # with coverage
```

## Linting

```bash
ruff check src tests
ruff format src tests
```

## Workflow

1. Open an issue describing what you want to change (skip for trivial fixes).
2. Fork & branch from `main`:
   ```bash
   git checkout -b feat/my-new-thing
   ```
3. Make your changes. Keep commits focused; one logical change per commit.
4. Run `pytest` and `ruff check` before pushing.
5. Open a PR. Reference the issue in the description.

## Conventions

- **Python ≥ 3.10.** Use modern syntax: `X | None`, `match` if it helps,
  dataclasses over `__init__`.
- **Typing is enforced.** Every public function has type hints.
- **No hard dependencies beyond the stdlib** for the core package.
  `matplotlib` and `pillow` are optional extras — never import them at
  module top-level except in `preview.py` and `img2hideout.py`.
- **Tests live in `tests/`**, fixtures in `tests/data/`. Keep fixtures
  tiny — the synthetic sample is < 1 KB on purpose.
- **Docs go in `docs/`**, not in inline docstrings longer than a few lines.
  Docstrings describe *what* a function does; `docs/` explains *why*.

## Adding a new decoration hash

1. Parse a hideout file containing the new decoration:
   ```bash
   hideout-art inspect path/to/file.hideout
   ```
   Unknown hashes are flagged in the output.
2. Edit `src/hideout_art/constants.py`:
   ```python
   KNOWN_HASHES: dict[str, int] = {
       # ...existing entries...
       "Your Decoration Name": 1234567890,
   }
   ```
3. If the decoration is purely artistic (not a gameplay object), also add
   it to `ART_TYPES`.
4. Add a test in `tests/test_parser.py` verifying the hash round-trips
   through parse → write → parse.
5. Commit with a message like:
   `feat(constants): add Your Decoration Name (hash 1234567890) from Some Hideout`

## Reporting bugs

Open an issue with:

- The smallest `.hideout` file that reproduces the problem (or a synthetic
  minimal one).
- The exact command you ran.
- The full traceback, if any.
- `python --version` and `pip show hideout-art`.

## Code of conduct

Be excellent to each other. Disagreements about code are fine; personal
attacks are not.
