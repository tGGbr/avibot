import asyncio
import itertools
import logging
import os
import sys
from types import ModuleType
from typing import Optional

import aiohttp
import asyncpg
import discord
import pkg_resources
from discord.ext import commands
from discord.utils import cached_property


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
        self.logger: logging.Logger = logging.getLogger("avibot")

    async def _create_session(self):
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def shutdown(self):
        await self.logout()
        if self.session:
            await self.session.close()

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

    def run(self):
        super().run(self.token)
