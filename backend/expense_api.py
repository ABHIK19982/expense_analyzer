"""
Author: Abhik Pramanik
Change Date: 2026-08-09
Change details: Bootstrap console-script entry point for expense-api.
Purpose: Start the FastAPI server even when macOS marks editable-install .pth
         files as hidden (UF_HIDDEN), which prevents Python from loading app.
Inputs: None (reads editable-install metadata from the local virtualenv).
Outputs: Starts uvicorn via app.main.run().
"""

from __future__ import annotations

import sys
from pathlib import Path


def _editable_backend_root() -> Path | None:
    """
    Purpose: Resolve the backend source directory for editable installs.
    Inputs: None.
    Outputs: Path to the backend project root, or None if not found.
    """
    try:
        import site
    except ImportError:
        return None

    for site_dir in site.getsitepackages():
        for pth_file in Path(site_dir).glob("_editable_impl_*.pth"):
            line = pth_file.read_text(encoding="utf-8").strip()
            if not line or line.startswith(("import ", "#")):
                continue
            candidate = Path(line)
            if candidate.is_dir():
                return candidate
    return None


def _ensure_app_importable() -> None:
    """
    Purpose: Guarantee the app package is importable before loading app.main.
    Inputs: None (mutates sys.path when needed).
    Outputs: None; raises ModuleNotFoundError if app cannot be resolved.
    """
    try:
        import app  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    backend_root = _editable_backend_root()
    if backend_root is not None:
        root = str(backend_root)
        if root not in sys.path:
            sys.path.insert(0, root)

    import app  # noqa: F401


def run() -> None:
    """
    Purpose: Bootstrap imports and start the local development API server.
    Inputs: None.
    Outputs: None; blocks while uvicorn serves the app.
    """
    _ensure_app_importable()
    from app.main import run as start_server

    start_server()
