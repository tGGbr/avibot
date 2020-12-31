"""Launcher Module."""
import asyncio
import logging

import config
from avibot import AviBot

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)


def run_bot():
    """Run the bot."""
    loop = asyncio.get_event_loop()
    bot = AviBot(config, loop=loop)
    bot.run()


def main():
    """Launch the bot."""
    run_bot()


if __name__ == "__main__":
    main()
