from discord.ext import commands
from asyncpg.pool import Pool
import re
from datetime import date, datetime
from dateutil import tz
import locale
import discord.embeds

from main import Tokens
from main import watcher

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION

from pyot.models import lol
from pyot.utils import loop_run
from pyot.core import Gatherer
import pyot.core


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(getclash)
    bot.add_command(endclash)
    bot.add_command(clashstream)
    bot.add_command(listclash)


@commands.command(name='listclash')
@commands.has_any_role('Admin', 'Social Media Manager')
async def listclash(ctx):
    pool = ctx.bot.pool
    currenttime: int = datetime.timestamp(datetime.now())
    tournaments = await lol.clash.ClashTournaments().get()
    print(tournaments)
    for tournament in tournaments.tournaments:
        print(str(tournament.schedule[0].registration_time.timestamp()))
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM clash_events WHERE id = $1', tournament.id)
        if row is None:
            async with pool.acquire() as conn:
                await conn.execute('INSERT INTO clash_events VALUES ($1, $2, $3, $4, $5, $6)', tournament.id,
                                   tournament.name_key, tournament.name_key_secondary,
                                   tournament.schedule[0].registration_time.timestamp(),
                                   tournament.schedule[0].start_time.timestamp(), tournament.schedule[0].cancelled)
        else:
            async with pool.acquire() as conn:
                await conn.execute('UPDATE clash_events SET cancelled = $1 WHERE id = $2',
                                   tournament.schedule[0].cancelled, tournament.id)

    async with pool.acquire() as conn:
        future_events = await conn.fetch('SELECT * FROM clash_events WHERE "registrationTime" > $1 '
                                         'AND cancelled = FALSE AND announced = FALSE', currenttime)

    embed = discord.Embed(title="Zukünftige Clash Spieltage", description="Die noch nicht announced wurden!")
    for event in future_events:
        locale.setlocale(locale.LC_TIME, "de-DE")
        playday = datetime.utcfromtimestamp(event['registrationTime']).strftime('%A %d %b')
        starttime = datetime.utcfromtimestamp(event['registrationTime'])
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Vienna')
        starttime = starttime.replace(tzinfo=from_zone)
        cetstarttime = starttime.astimezone(to_zone).strftime('%H:%M')

        value = f'ID: **{str(event["id"])}** \n ' \
                f'Start: **{cetstarttime}** \n' \
                f'Name: {event["nameKey"]} \n' \
                f'Tag: {event["nameKeySecondary"]}'

        embed.add_field(name=playday, value=value, inline=False)
    await ctx.channel.send(content=None, embed=embed)


@commands.command(name='clash')
@commands.has_any_role('Admin', 'Social Media Manager')
async def getclash(ctx, *args):
    pool = ctx.bot.pool
    clash_id: int
    times = []
    event_times = []
    event_times_unix = []
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    if len(args) < 2:
        await ctx.send("Bitte stelle sicher an erster Stelle die ID des Clash Events das du erstellen möchtest "
                       "gelistet zu haben und danach bis zu 10 verschiedene Uhrzeiten!")
    if len(args) >= 2:
        clash_id = re.findall(r"(?<!\d)\d{4,4}(?!\d)", args[0])
        if clash_id:
            async with pool.acquire() as conn:
                event = await conn.fetchrow('SELECT * FROM clash_events WHERE id = $1', int(clash_id[0]))

            for arg in args[1:]:
                rawtime = re.findall(r"^(?:[0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", arg)
                times.append(rawtime)

            playday = datetime.utcfromtimestamp(event['registrationTime'])
            for time in times:
                splittime = time[0].split(":")
                temptime = playday.replace(hour=int(splittime[0]), minute=int(splittime[1]), tzinfo=tz.gettz('UTC'))
                event_times.append(temptime)
                event_times_unix.append(temptime.timestamp())
            locale.setlocale(locale.LC_TIME, "de-DE")
            playday = datetime.utcfromtimestamp(event['registrationTime']).strftime('%A %d %b')
            embed_title = f'Clash am {playday}'
            embed_desc = f'Bitte reagiere auf jene Uhrzeiten ab denen du für Clash Zeit hast!'
            embed = discord.Embed(title=embed_title, description=embed_desc)
            i = 0
            for event_time in event_times:
                embed_field = f'{emojis[i]} {event_time.strftime("%H:%M")}'
                embed.add_field(name=embed_field, value="-----", inline=False)
                i += 1

            clash_channel = discord.utils.get(ctx.guild.channels, name="clash-announcements")
            message = await clash_channel.send(content=None, embed=embed)
            j = 0
            for event_time in event_times:
                await message.add_reaction(emojis[j])
                j += 1

            async with pool.acquire() as conn:
                await conn.execute('INSERT INTO reactions(message_id, type) VALUES ($1, $2)', message.id, "CLASH")
                await conn.execute('UPDATE clash_events SET event_times = $1 , "announceMessageId" = $2, announced = '
                                   'True WHERE id = $3', event_times_unix, message.id, event['id'])

        else:
            await ctx.send("Bitte stelle sicher an erster Stelle die ID des Clash Events das du erstellen möchtest "
                           "gelistet zu haben und danach bis zu 10 verschiedene Uhrzeiten! Du scheinst die ID des "
                           "Events vergessen zu haben!")
            return


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
