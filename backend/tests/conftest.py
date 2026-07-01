"""
pytest configurations and shared mock fixtures.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))
