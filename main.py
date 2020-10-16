import os
import logging

from asyncpg.pool import Pool
from dotenv import load_dotenv
from discord.ext import commands

from riotwatcher import LolWatcher, ApiError
import pandas as pd

from discord import reaction
from datetime import date
import locale

import asyncio
import asyncpg
import re

logging.basicConfig(level=logging.INFO)

# Config aus .env einlesen.
load_dotenv()

startup_extensions = ["clash", "general", "league", "memes", "users", "reaction"]

class Tokens:
    TOKEN: str = os.getenv('DISCORD_BOT_TOKEN')
    GUILD: str = os.getenv('DISCORD_GUILD')
    LOL_REGION: str = os.getenv('myregion')
    RIOT_TOKEN: str = os.getenv('RIOTAPI')
    eule: str = 'Jonas'


# Variablen assignen
watcher = LolWatcher(Tokens.RIOT_TOKEN)
pool: Pool = "eule"


class BetterBot(commands.Bot):
    pool = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


async def main():
    global pool
    pool = await asyncpg.create_pool(user=os.getenv('DB_USER'), password=os.getenv('DB_PW'),
                                     database=os.getenv('DB_NAME'), host=os.getenv('DB_HOST'),
                                     port=os.getenv('DB_PORT'))

    # bot = commands.Bot(command_prefix='!', description="COOLER BOT", case_insensitive=True)
    bot = BetterBot(command_prefix='!', description="COOLER BOT", case_insensitive=True)
    bot.pool = pool

    @bot.event
    async def on_ready():
        for guild in bot.guilds:
            if guild.id == Tokens.GUILD:
                break

        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')

        for extension in startup_extensions:
            try:
                bot.load_extension(f'plugins.{extension}')
            except (AttributeError, ImportError) as e:
                print("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
                return
            print("{} loaded.".format(extension))

    # Start Eule

    @bot.command()
    async def load(ctx, extension_name: str):
        """Loads an extension."""
        try:
            bot.load_extension(f'plugins.{extension_name}')
        except (AttributeError, ImportError) as e:
            await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        await ctx.send("{} loaded.".format(extension_name))

    @bot.command()
    async def unload(ctx, extension_name: str):
        """Loads an extension."""
        try:
            bot.unload_extension(f'plugins.{extension_name}')
        except (AttributeError, ImportError) as e:
            await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        await ctx.send("{} unloaded.".format(extension_name))

    # End Eule

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.PrivateMessageOnly):
            await ctx.send('Dieser Command geht nur in einer Privatnachricht!')
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send('Du bist leider keine Schildkröte bei STT lese bitte dazu die Anleitung zum werden einer '
                           'Schildkröte auf dem Discord Server')
        if isinstance(error, commands.UserInputError):
            if error.param.name == "ign":
                await ctx.send('Scheint als hättest du keinen Ingamenamen mit angegeben bitte stelle sicher das du '
                               'den Command folgendermaßen benutzt: `!ign INGAMENAME`')
            elif error.param.name == "lane":
                await ctx.send('Du scheinst vergessen haben deine Hauptlane anzugeben vergiss nicht diese sind '
                               'folgende: `top, jgl, mid, bot, sup`')
        if isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send('Module already loaded')
        print(error)



    await bot.start(Tokens.TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
