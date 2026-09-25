import os
import sys
from pathlib import Path

# Add backend to sys.path so app and warfarin_logic can be imported
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
