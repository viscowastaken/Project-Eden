import importlib
import os
import re
import abc
from pathlib import Path

import discord
from discord.ext import commands

from config import main as config

CONFIG_PATH = Path(__file__).parent / "config" / "main.py"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # required for on_member_join

bot = commands.Bot(command_prefix="!", intents=intents)


class run(abc.ABC):
    """Abstract launcher for the Discord bot."""

    def __init__(self, bot_client: commands.Bot):
        self.bot_client = bot_client

    @abc.abstractmethod
    def start(self, token: str) -> None:
        """Start the bot."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop the bot gracefully."""


class DiscordRunner(run):
    """Concrete implementation that starts and stops a bot instance."""

    def start(self, token: str) -> None:
        self.bot_client.run(token)

    def stop(self) -> None:
        self.bot_client.loop.create_task(self.bot_client.close())


def get_token() -> str:
    """Return the Discord token from the environment, keeping compatibility with the original variable name."""
    candidates = (
        "Bot_Token",
        "Bot_Token",
        "Bot_Token",
    )
    for name in candidates:
        token = os.environ.get(name)
        if token:
            return token
    raise RuntimeError("No Discord bot token configured.")


def save_join_count(value: int) -> None:
    """Rewrite JOIN_COUNT in config/main.py and reload the module."""
    text = CONFIG_PATH.read_text()
    new_text, n = re.subn(
        r"^JOIN_COUNT\s*=.*$", f"JOIN_COUNT = {value}", text, flags=re.MULTILINE
    )
    if n == 0:  # line missing, so add it
        new_text = text.rstrip() + f"\nJOIN_COUNT = {value}\n"
    CONFIG_PATH.write_text(new_text)
    importlib.reload(config)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")


@bot.event
async def on_member_join(member: discord.Member):
    importlib.reload(config)  # pick up any manual edits to the file
    new_value = config.JOIN_COUNT + 1
    save_join_count(new_value)
    print(f"{member} joined. JOIN_COUNT is now {new_value}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.content.startswith("hello"):
        await message.channel.send(f"test {message.author}!")

    await bot.process_commands(message)  # keep !commands working

@bot.command()
async def fakejoin(ctx):
    bot.dispatch("member_join", ctx.author)
    await ctx.send("Fake join done!")

bot.run("Bot_Token")
