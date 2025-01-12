from pathlib import Path


_path = Path("needs_sync")


def needs_sync() -> bool:
    return _path.exists()


def mark_synced() -> None:
    _path.unlink(missing_ok=True)
