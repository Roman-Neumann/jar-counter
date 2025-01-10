# messages used before logging is setup by discord.py

import sys


def write_failed_startup_message() -> None:
    _write_error(
        "Failed to start the bot. Ensure you installed all necessary "
        "dependencies and your virtual environment is running, provided you're "
        "using one. Check https://github.com/Roman-Neumann/jar-counter#setup "
        "for more info.",
    )


def write_needs_sync_message() -> None:
    _write_error(
        "You must sync your commands to Discord. "
        "Run 'scripts\\sync.bat' if you're on Windows or 'scripts/sync.sh' if "
        "you're on Linux. Or manually pass the '--sync-and-exit' flag to "
        "'run_host.py'. Check "
        "https://github.com/Roman-Neumann/jar-counter#setup for more info.",
    )


def _write_error(message: str) -> None:
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()
