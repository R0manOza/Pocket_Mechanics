"""
Vercel serverless entrypoint for Pocket Mechanics FastAPI backend.

Vercel expects an ASGI app exposed as `app`.
We keep the existing `Backend/` code unchanged and add it to sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `Backend/` importable (so `import main` works as it does locally from Backend/).
_repo_root = Path(__file__).resolve().parents[1]
_backend_dir = _repo_root / "Backend"
sys.path.insert(0, str(_backend_dir))

from main import app  # noqa: E402

