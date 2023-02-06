import asyncio
import json
import logging
import os
import platform
import random
import sys
from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

import legendsio_discord.exceptions as exceptions
from legendsio_discord.config import default_config
from legendsio_discord.helpers import db_manager


COLORS = {
    "red": 0xE02B2B,
    "default": None
}

load_dotenv()
user_login = os.getlogin()

default_config_path = os.path.join("/home", user_login, ".config")



if len(sys.argv) < 2:
    print("Missing path to configuration file! Using the default setup")
    config_path = str(input(f"Provide a path to save the .config in or accept the default [{default_config_path}] >>> "))
    if not os.path.exists(config_path):
        config_path = default_config_path

    bot_directory = os.path.join(config_path, 'legends_io')
    try:
        os.mkdir(bot_directory)
    except Exception as e:
        print(e)
        sys.exit("An error occurred while setting up a directory for Legends IO")

    config_path = os.path.join(bot_directory, 'legends.conf')
    config = default_config(config_path)

else:
    config_path = sys.argv[1].strip()
    if not os.path.exists(config_path):
        sys.exit("Invalid path provided for .conf")

    if not os.path.isfile(config_path):
        files = [f for f in os.listdir(config_path) if f.endswith(".conf")]
        if len(files) > 1:
            for f in files:
                print(f)
            choice = str(input("Multiple .conf files found, please specify which one to use >>> "))
            config_path = os.path.join(config_path, choice)
            if not os.path.isfile(config_path):
                sys.exit("Invalid filepath")
        else:
            file = files[0]
            config_path = os.path.join(config_path, file)
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

        except Exception as e:
            print(e)
            sys.exit(f"There was an error loading the configuration at {config_path}")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = Bot(
    command_prefix=commands.when_mentioned_or(config['prefix']),
    intents=intents,
    help_command=None
)


class LoggingFormatter(logging.Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        fmt = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        fmt = fmt.replace("(black)", self.black + self.bold)
        fmt = fmt.replace("(reset)", self.reset)
        fmt = fmt.replace("(levelcolor)", log_color)
        fmt = fmt.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(fmt, '%Y-%m-%d %H:%M:%S', style="{")
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())

file_handler = logging.FileHandler(
    filename="legends_io.log",
    encoding="utf-8",
    mode="w"
)
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}",
    "%Y-%m-%d %H:%M:%S",
    style="{"
)
file_handler.setFormatter(file_handler_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
bot.logger = logger

async def init_db():
    await db_manager.connect_db(config)


bot.config = config


# Actual bot logic
@bot.event
async def on_ready() -> None:
    """
    Called everytime the bot successfully starts up and logs into the server.
    :return:
    """
    bot.logger.info(f"Logged in as {bot.user.name}")
    bot.logger.info(f"discord.py API version: {discord.__version__}")
    bot.logger.info(f"Python version: {platform.python_version()}")
    bot.logger.info(
        f"Running on: {platform.system()} {platform.release()} ({os.name})"
    )
    runtime_info = f"Running on: {platform.system()} {platform.release()} ({os.name})"
    bot.logger.info(runtime_info)
    bot.logger.info(f"{'-'* len(runtime_info)}")
    status_task.start()
    if config['sync_commands_globally']:
        bot.logger.info("Syncing commands to the global tree...")
        await bot.tree.sync()


@tasks.loop(minutes=1.0)
async def status_task() -> None:
    """
    Randomly update the bot's current presence
    :return:
    """
    statuses = ["Insulting your gunny", "dropshotting", "uninstalling the game"]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Called everytime a message is sent within the server.
    :param message:  The message object of the message that triggered the event
    :return:
    """
    if message.author == bot.user or message.author.bot:
        return

    await bot.process_commands(message)


@bot.event
async def on_command_completion(context: Context) -> None:
    """
    Gets called everytime a command successfully executes

    :param context: The command's context
    :return:
    """
    full_cmd_name = context.command.qualified_name
    split_name = full_cmd_name.split(" ")
    executed = str(split_name[0])
    if context.guild is not None:
        log_info = f'Executed {executed} in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})'
    else:
        log_info = f'Executed {executed} by {context.author} (ID: {context.author.id})'

    bot.logger.info(log_info)


@bot.event
async def on_command_error(context: Context, error) -> None:
    """
    Gets called everytime a command fails and raises some Exception

    :param context: The context of the command
    :param error: THe exception that was raised
    :return:
    """

    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            description=f"**Slow down!** You can use this again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes ' if round(minutes) > 0 else ''} {f'and {round(seconds)} seconds ' if round(seconds) > 0 else ''}",
            color=COLORS['red']
        )
        embed.title = "Cooldown"
        await context.send(embed=embed)

    elif isinstance(error, exceptions.UserBlackListed):
        embed = discord.Embed(
            description="You are blacklisted from using this bot.",
            color=COLORS['red']
        )
        await context.send(embed=embed)
        bot.logger.warning(
            f"{context.author} (ID: {context.author.id}) tried to execute a command in {context.guild.name} (ID: {context.guild.id}) but they are in the blacklist."
        )

    elif isinstance(error, exceptions.UserNotOwner):
        embed = discord.Embed(
            description="You are not the owner of the bot, you're not allowed to use that!",
            color=COLORS['red']
        )
        await context.send(embed=embed)

    elif isinstance(error, commands.MissingPermissions):
        perm_list = ", ".join(error.missing_permissions)
        embed = discord.Embed(
            description=f"You are missing the permission(s) `{perm_list}` to execute this command.",
            color=COLORS['red']
        )
        await context.send(embed=embed)

    elif isinstance(error, commands.BotMissingPermissions):
        perm_list = ", ".join(error.missing_permissions)
        embed = discord.Embed(
            description=f"I am missing the permission(s) `{perm_list}` to to execute this command.",
            color=COLORS['red']
        )
        await context.send(embed=embed)

    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            description=str(error).capitalize(),
            color=COLORS['red']
        )
        await context.send(embed=embed)

    else:
        raise error


async def load_cogs() -> None:
    """
    This executes after bot is ready and setup, it simply
    loads all the extensions found in the `cogs` directory
    """
    for file in os.listdir(os.path.join(os.path.realpath(os.path.dirname(__file__)), "cogs")):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                bot.logger.info(f"Successfully loaded extension `{extension}`.")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                bot.logger.error(
                    f"Failed to load extension: {extension}\n{exception}"
                )



if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(load_cogs())
    bot.run(config['token'])