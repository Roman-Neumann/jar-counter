import sys
from importlib.util import find_spec

from .errors_fallback import (
    write_failed_startup_message,
    write_needs_sync_message,
)


if not find_spec("discord"):
    write_failed_startup_message()
    sys.exit(-1)


from . import jar_io
from .bot import bot
from .errors import NeedsSyncError


args = jar_io.read_args()
config = jar_io.read_config()
try:
    bot.prepare_run(args, config)
except NeedsSyncError:
    write_needs_sync_message()
    sys.exit(-1)

bot.run()
