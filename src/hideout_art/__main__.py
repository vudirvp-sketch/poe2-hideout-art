"""Allow ``python -m hideout_art`` to invoke the CLI.

This is a thin shim around ``hideout_art.cli:main`` so the README's
``python -m hideout_art img2hideout ...`` examples work as documented.
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
