"""Load `.env` from the repository root (parent of `scripts/`)."""
from pathlib import Path

from dotenv import load_dotenv


def load_repo_env() -> None:
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
