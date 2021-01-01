import asyncio
import itertools
import logging
import os
import signal
import sys
from types import ModuleType
from typing import Optional

import aiohttp
import asyncpg
import discord
import pkg_resources
from avibot.core.data_manager import DatabaseManager
from discord.client import _cleanup_loop
from discord.ext import commands
from discord.utils import cached_property

logger = logging.getLogger(__name__)


class AviBot(commands.Bot):
    """This class implements AviBot."""

    def __init__(
        self,
        config: ModuleType,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.config = config
        self.prefix = config.bot_prefix
        super().__init__(command_prefix=self.prefix, loop=loop)
        self.owner: int = config.bot_owner
        self.core_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.bot_dir: str = os.path.dirname(self.core_dir)
        self.data_dir: str = os.path.join(self.bot_dir, "data")
        self.ext_dir: str = os.path.join(self.bot_dir, "exts")
        self.token: Optional[str] = os.getenv("DISCORD_TOKEN")
        self.session: Optional[aiohttp.ClientSession] = None
        self.dbm: Optional[DatabaseManager] = None
        self.logger: logging.Logger = logging.getLogger("avibot")
        self.loop.run_until_complete(self.startup())

    async def startup(self):
        tasks = [self._create_http_session(), self._create_dbm_connection()]
        await asyncio.gather(*tasks)

    async def _create_http_session(self):
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def _create_dbm_connection(self):
        options = {
            "password": os.getenv("POSTGRES_PASSWORD"),
            "hostname": os.getenv("POSTGRES_HOST"),
            "username": os.getenv("POSTGRES_USER"),
            "database": os.getenv("POSTGRES_DB"),
        }
        self.dbm = DatabaseManager(**options, loop=self.loop)
        try:
            await self.dbm.start()
        except Exception as e:
            print(f"Error {type(e)}: {e}")

    async def shutdown(self):
        await self.logout()
        if self.session:
            await self.session.close()
        if self.dbm:
            await self.dbm.close()

    @property
    def name(self):
        return self.user.name

    @property
    def avatar(self):
        return self.user.avatar_url_as(static_format="png")

    @property
    def avatar_small(self):
        return self.user.avatar_url_as(static_format="png", size=64)

    async def on_ready(self):
        print("AviBot")

    def run(self, *args, **kwargs):
        """Run the bot."""
        loop = self.loop

        async def runner():
            try:
                await self.start(self.token, *args, **kwargs)
            finally:
                await self.shutdown()
                if not self.is_closed():
                    await self.close()

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)

        loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received signal to terminate bot and event loop.")
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            logger.info("Cleaning up tasks.")
            _cleanup_loop(loop)
