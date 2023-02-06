"""
All database or SQLite related functionality should be built into this module
"""
import asyncio
import os
from sqlalchemy.future import select
from legendsio_discord.database import models



async def connect_db(config):
    """
    Initializes a SQLite database and creates the tables from the models declared in models.py

    :param config: dictionary of configuration values, must have config_path key set
    :return:
    """
    async with models.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

    await models.engine.dispose()


