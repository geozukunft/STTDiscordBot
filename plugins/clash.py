from discord.ext import commands
from asyncpg.pool import Pool
import re
from datetime import date
import locale

from main import Tokens
from main import watcher

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(getclash)
    bot.add_command(endclash)
    bot.add_command(clashstream)


@commands.command(name='clash')
@commands.has_any_role('Admin', 'Social Media Manager')
async def getclash(ctx, inputtime1, inputtime2):
    pool = ctx.bot.pool

    time1 = re.findall(r"^(?:[0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", inputtime1)
    time2 = re.findall(r"^(?:[0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", inputtime2)

    tournaments = watcher.clash.tournaments(my_region)

    for tournament in tournaments:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM clash_events WHERE id = $1', tournament['id'])
        if row is None:
            async with pool.acquire() as conn:
                await conn.execute('INSERT INTO clash_events VALUES ($1, $2, $3, $4, $5, $6)', tournament['id'],
                                   tournament['nameKey'], tournament['nameKeySecondary'],
                                   tournament['schedule'][0]['registrationTime'],
                                   tournament['schedule'][0]['startTime'], tournament['schedule'][0]['cancelled'])

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT * FROM clash_events WHERE "announced" = False ORDER BY  "registrationTime" ASC')

    await ctx.send("**Clashanmeldung**")

    for row in rows:
        epochtime = row['registrationTime']
        d = date.fromtimestamp(epochtime / 1000)
        locale.setlocale(locale.LC_TIME, "de-DE")
        day = d.strftime('%A %d %b')
        message = await ctx.send(":one: " + day + " " + time1[0] + "\n" +
                                 ":two: " + day + " " + time2[0])
        await message.add_reaction('1️⃣')
        await message.add_reaction('2️⃣')

        async with pool.acquire() as conn:
            await conn.execute('UPDATE clash_events SET "announced" = True, "announceMessageID" = $1 '
                               'WHERE id = $2', message.id, row['id'])


@commands.command(name='endclash')
@commands.has_any_role('Admin', 'Social Media Manager')
async def endclash(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        events = await conn.fetch("SELECT * FROM clashdata WHERE announced = True AND ended = False "
                                  'ORDER BY "registrationTime" ASC')

    if events is not None:
        for event in events:
            async with pool.acquire() as conn:
                await conn.execute("UPDATE clashdata SET ended = True WHERE id = $1", event['id'])
                await conn.execute("DELETE FROM clashplayerdata")

            epochtime = event['registrationTime']
            d = date.fromtimestamp(epochtime / 1000)
            locale.setlocale(locale.LC_TIME, "de-DE")
            day = d.strftime('%A %d %b')

            await ctx.send("Clash Event vom " + day + " gelöscht")


@commands.command(name='clashstream')
@commands.has_any_role('Social Media Manager')
async def clashstream(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        events = await conn.fetch('SELECT * FROM clashdata WHERE announced = True AND ended = False '
                                  'ORDER BY  "registrationTime" ASC')

    await ctx.send("**NUR FÜR STT STREAMER RELEVANT**")

    for event in events:
        epochtime = event['registrationTime']
        d = date.fromtimestamp(epochtime / 1000)
        locale.setlocale(locale.LC_TIME, "de-DE")
        day = d.strftime('%A %d %b')

        message = await ctx.send("CLASH STREAM " + day)
        await message.add_reaction('🔴')

        async with pool.acquire() as conn:
            await conn.execute('UPDATE clashdata SET "streamMessageID" = $1 '
                               'WHERE announced = True AND ended = False', message.id)
