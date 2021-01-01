"""This module implements the database manager logic."""
import asyncio
import json
import logging
from typing import List, Optional

import asyncpg

logger = logging.getLogger(__name__)


async def init_conn(conn):
    """Set up initial codecs."""
    await conn.set_type_codec("jsonb",
                              encoder=json.dumps,
                              decoder=json.loads,
                              schema="pg_catalog")
    await conn.set_type_codec("json",
                              encoder=json.dumps,
                              decoder=json.loads,
                              schema="pg_catalog")


class DatabaseManager:
    """Manage data in a postgres database."""

    def __init__(
        self,
        password: str,
        hostname: str = "localhost",
        username: str = "postgres",
        database: str = "avibot",
        port: int = 5432,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """Initialize the DatabaseManager."""
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.dsn: str = "postgres://{}:{}@{}:{}/{}".format(
            username, password, hostname, port, database)
        self.pool = None
        self.listener_conn: Optional[asyncpg.pool.PoolConnectionProxy] = None
        self.listeners = List[asyncpg.pool.PoolConnectionProxy]

    async def start(self) -> None:
        """Start the DatabaseManager."""
        logger.info("Starting DatabaseManager.")
        self.pool = await asyncpg.create_pool(self.dsn,
                                              loop=self.loop,
                                              init=init_conn)
        await self.setup()

    async def recreate_pool(self) -> None:
        """Recreate pool connection if closed."""
        logger.warning("Re-creating database pool.")
        self.pool = await asyncpg.create_pool(self.dsn,
                                              loop=self.loop,
                                              init=init_conn)
        await self.setup()

    async def setup(self) -> None:
        """Implement initial setup when the DatabaseManager is created."""
        if self.pool:
            self.listener_conn = await self.pool.acquire()

    async def close(self) -> None:
        """Stop the DatabaseManager."""
        if self.pool:
            if self.listener_conn:
                await self.pool.release(self.listener_conn)
            await self.pool.close()
            self.pool.terminate()

    async def execute_query(self, query, *args, **kwargs):
        """Execute database query."""
        try:
            async with self.pool.acquire() as conn:
                sttmnt = await conn.prepare(query)
                return await sttmnt.fetch(*args, **kwargs)

        except asyncpg.exceptions.InterfaceError as e:
            logger.error(f"Exception {type(e)}: {e}")
            await self.recreate_pool()
            return await self.execute_query(query, *args, **kwargs)
        # TODO: add base case

    async def execute_transaction(self, query, *args, **kwargs):
        """Execute database transaction."""
        try:
            async with self.pool.acquire() as conn:
                sttmnt = await conn.prepare(query)
                async with conn.transaction():
                    return [r for r in sttmnt.cursor(*args, **kwargs)]
        except asyncpg.exceptions.InterfaceError as e:
            logger.error(f"Exception {type(e)}: {e}")
            await self.recreate_pool()
            return await self.execute_transaction(query, *args, **kwargs)
        # TODO: add base case

    async def add_conn_listeners(
            self, *listeners: asyncpg.pool.PoolConnectionProxy) -> None:
        """Add connection listeners."""
        conn = self.listener_conn
        add_listeners = [lst for lst in listeners if lst not in self.listeners]
        self.listeners.extend(add_listeners)
        for listener in add_listeners:
            if conn:
                await conn.add_listener(listener[0], listener[1])

    async def remove_listeners(
            self, *listeners: asyncpg.pool.PoolConnectionProxy) -> None:
        """Remove connection listeners."""
        conn = self.listener_conn
        remove_listeners = [lst for lst in listeners if lst in self.listeners]
        for listener in remove_listeners:
            self.listeners.remove(listener)
            if conn:
                await conn.remove_listener(listener[0], listener[1])
