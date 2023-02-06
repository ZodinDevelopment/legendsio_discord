import json
import os
from typing import Callable, TypeVar

from discord.ext import commands

from legendsio_discord.exceptions import *
from legendsio_helpers import db_manager


T = TypeVar("T")


def is_owner() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        config = context.bot.config
        if context.author.id not in config['owners']:
            raise UserNotOwner
        return True

    return commands.check(predicate)



def not_blacklisted() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id):
            raise UserBlackListed
        return True

    return commands.check(predicate)


def is_agent() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        author_id = context.author.id
        author_roles = context.author.roles
        agent_role = await db_manager.get_agent_role(context.guild.id)
        if agent_role is None:
            raise UserNotAgent
        is_agent = False
        for role in author_roles:
            if role.id == agent_role:
                is_agent = True
                break
        if not is_agent:
            raise UserNotAgent
        return is_agent

    return commands.check(predicate)



