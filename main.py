from __future__ import annotations

import logging
import sys

from bot.client import VoidBot
from bot.config import ConfigError, Settings


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1

    bot = VoidBot(settings)
    bot.load_all_extensions()
    bot.run(settings.token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
