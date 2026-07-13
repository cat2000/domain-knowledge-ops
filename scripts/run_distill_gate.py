#!/usr/bin/env python3
"""Wiki distill gate entry."""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill.gate import main

if __name__ == "__main__":
    raise SystemExit(main())
