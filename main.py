import os
import logging

from asyncpg.pool import Pool
from dotenv import load_dotenv
from discord.ext import commands
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import discord
from discord import reaction
from datetime import date
import locale

import asyncio
import asyncpg
import re

logging.basicConfig(level=logging.INFO)

# Config aus .env einlesen.
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
my_region = os.getenv('myregion')
api_key = os.getenv('RIOTAPI')

# Variablen assignen
watcher = LolWatcher(api_key)
pool: Pool = "eule"


async def main():
    global pool
    pool = await asyncpg.create_pool(user=os.getenv('DB_USER'), password=os.getenv('DB_PW'),
                                     database=os.getenv('DB_NAME'), host=os.getenv('DB_HOST'),
                                     port=os.getenv('DB_PORT'))
    bot = commands.Bot(command_prefix='!', description="COOLER BOT", case_insensitive=True, )
    client = discord.Client()

    @bot.command(name='me')
    async def riotapitest(ctx, playername):
        me = watcher.summoner.by_name(my_region, playername)
        my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])
        icon_path = "C:\\Daten\\dragontail-10.19.1\\dragontail-10.19.1\\10.19.1\\img\\profileicon\\" + str(
            me['profileIconId']) + ".png"
        file = discord.File(icon_path, filename="image.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://image.png")
        await ctx.send(content="Spieler: " + me['name'] + "\n" + "Level: " + str(me['summonerLevel']) + "\n" +
                               "Flex Rank: " + my_ranked_stats[0]['tier'] + " " + my_ranked_stats[0]['rank'] + "\n"
                                                                                                               "Solo Rank: " +
                               my_ranked_stats[1]['tier'] + " " + my_ranked_stats[1]['rank'], file=file, embed=embed)

    @bot.command(name='clash')
    @commands.has_any_role('Admin', 'Social Media Manager')
    async def getclash(ctx, inputtime1, inputtime2):
        global pool
        poolfunc: Pool = pool

        time1 = re.findall(r"^(?:[0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", inputtime1)
        time2 = re.findall(r"^(?:[0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", inputtime2)

        tournaments = watcher.clash.tournaments(my_region)

        for tournament in tournaments:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM clashdata WHERE id = $1', tournament['id'])
            if row is None:
                async with pool.acquire() as conn:
                    await conn.execute('INSERT INTO clashdata VALUES ($1, $2, $3, $4, $5, $6)', tournament['id'],
                                       tournament['nameKey'], tournament['nameKeySecondary'],
                                       tournament['schedule'][0]['registrationTime'],
                                       tournament['schedule'][0]['startTime'], tournament['schedule'][0]['cancelled'])

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM clashdata WHERE "announced" = False ORDER BY  "registrationTime" ASC')

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
                await conn.execute('UPDATE clashdata SET "announced" = True, "announceMessageID" = $1 '
                                   'WHERE id = $2', message.id, row['id'])

    @bot.command(name='endclash')
    @commands.has_any_role('Admin', 'Social Media Manager')
    async def endclash(ctx):
        async with pool.acquire() as conn:
            events = await conn.fetch("SELECT id FROM clashdata WHERE announced = True AND ended = False")

        if events is not None:
            for event in events:
                async with pool.acquire() as conn:
                    await conn.execute("UPDATE clashdata SET ended = True WHERE id = $1", event['id'])

    @bot.command(name='message')
    async def testmessage(ctx):
        await ctx.send("Test")
        await ctx.send(ctx)

    async def newreaction(reaction):
        print(reaction.message_id)
        async with pool.acquire() as conn:
            event = await conn.fetchrow('SELECT * FROM clashdata WHERE "announceMessageID" = $1',
                                        reaction.message_id)
            player = await conn.fetchrow('SELECT "regnum" FROM playerdata WHERE "idplayer" = $1', reaction.user_id)

        if event is not None and player is not None and event['ended'] is False:

            epochtime = event['registrationTime']
            d = date.fromtimestamp(epochtime / 1000)
            locale.setlocale(locale.LC_TIME, "de-DE")
            day = d.strftime('%A')

            async with pool.acquire() as conn:
                registerd = await conn.fetchrow('SELECT * FROM clashplayerdata WHERE idplayer = $1', reaction.user_id)

            if registerd is not None:
                if reaction.emoji.name == "1️⃣":
                    if day == 'Samstag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day1time1 = True WHERE idplayer = $1',
                                               reaction.user_id)
                    elif day == 'Sonntag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day2time1 = True WHERE idplayer = $1',
                                               reaction.user_id)
                elif reaction.emoji.name == "2️⃣":
                    if day == 'Samstag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day1time2 = True WHERE idplayer = $1',
                                               reaction.user_id)
                    elif day == 'Sonntag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day2time2 = True WHERE idplayer = $1',
                                               reaction.user_id)

            else:
                if reaction.emoji.name == "1️⃣":
                    if day == 'Samstag':
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO clashplayerdata (idplayer, day1time1, regnum) VALUES '
                                               '($1, True, $2) ', reaction.user_id, player['regnum'])
                    elif day == 'Sonntag':
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO clashplayerdata (idplayer, day2time1, regnum) VALUES '
                                               '($1, True, $2) ', reaction.user_id, player['regnum'])
                elif reaction.emoji.name == "2️⃣":
                    if day == 'Samstag':
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO clashplayerdata (idplayer, day1time2, regnum) VALUES '
                                               '($1, True, $2) ', reaction.user_id, player['regnum'])
                    elif day == 'Sonntag':
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO clashplayerdata (idplayer, day2time2, regnum) VALUES '
                                               '($1, True, $2) ', reaction.user_id, player['regnum'])

    async def removereaction(reaction):
        print(reaction.message_id)
        async with pool.acquire() as conn:
            event = await conn.fetchrow('SELECT * FROM clashdata WHERE "announceMessageID" = $1',
                                        reaction.message_id)
            player = await conn.fetchrow('SELECT "regnum" FROM playerdata WHERE "idplayer" = $1', reaction.user_id)

        if event is not None and player is not None and event['ended'] is False:

            epochtime = event['registrationTime']
            d = date.fromtimestamp(epochtime / 1000)
            locale.setlocale(locale.LC_TIME, "de-DE")
            day = d.strftime('%A')

            async with pool.acquire() as conn:
                registerd = await conn.fetchrow('SELECT * FROM clashplayerdata WHERE idplayer = $1', reaction.user_id)

            if registerd is not None:
                if reaction.emoji.name == "1️⃣":
                    if day == 'Samstag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day1time1 = False WHERE idplayer = $1',
                                               reaction.user_id)
                    elif day == 'Sonntag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day2time1 = False WHERE idplayer = $1',
                                               reaction.user_id)
                elif reaction.emoji.name == "2️⃣":
                    if day == 'Samstag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day1time2 = False WHERE idplayer = $1',
                                               reaction.user_id)
                    elif day == 'Sonntag':
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE clashplayerdata SET day2time2 = False WHERE idplayer = $1',
                                               reaction.user_id)

    @bot.command(name='register', help='Registriere dich im Spielerverzeichniss')
    @commands.dm_only()
    async def register(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is None:
                if member.nick is not None:
                    name = re.findall(r"(\w+)", member.nick)
                    if name is not None:
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO playerdata VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)',
                                               member.id, name[1], name[0], False, False, False, False, False, "k.A.")
                        await ctx.send("Du bist nun Registriert du kannst nun mit !main deine Main Lane eintragen "
                                       "oder mit !top, !jgl usw. eintragen welche Lanes du Spielen kannst")
                    else:
                        await ctx.send("Du hast auf dem STT Discord noch keinen Nickname nach dem Format `vorname | "
                                       "ingamename` bitte richte diesen zuerst ein bevor du dich registrierst")
                else:
                    await ctx.send("Du scheinst von den Admins noch keinen Nicknamen bekommen zu haben. Bitte wende "
                                   "dich an einen STT Admin.")
            else:
                await ctx.send("Du bist bereits Registriert um deinen IGN zu ändern benutze bitte !ign INGAMENAME")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='main', help='Sende mit `!main` `top, jgl, mid, bot, sup` deine Hauptlane')
    @commands.dm_only()
    async def mainl(ctx, lane):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        value = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                if lane is not None:
                    lane = lane.upper()
                    if lane == "TOP":
                        value = True
                        if row[3] is not True:
                            async with pool.acquire() as conn:
                                await conn.execute('UPDATE playerdata SET top = True WHERE idplayer = $1', member.id)
                    elif lane == "JGL":
                        value = True
                        if row[4] is not True:
                            async with pool.acquire() as conn:
                                await conn.execute('UPDATE playerdata SET jgl = True WHERE idplayer = $1', member.id)
                    elif lane == "MID":
                        value = True
                        if row[5] is not True:
                            async with pool.acquire() as conn:
                                await conn.execute('UPDATE playerdata SET mid = True WHERE idplayer = $1', member.id)
                    elif lane == "BOT" or lane == "ADC":
                        lane = "BOT"
                        value = True
                        if row[6] is not True:
                            async with pool.acquire() as conn:
                                await conn.execute('UPDATE playerdata SET bot = True WHERE idplayer = $1', member.id)
                    elif lane == "SUP":
                        value = True
                        if row[7] is not True:
                            async with pool.acquire() as conn:
                                await conn.execute('UPDATE playerdata SET sup = True WHERE idplayer = $1', member.id)
                    else:
                        await ctx.send(
                            "Bitte überprüfe deine Eingabe! Valide Optionen sind: `TOP , JGL, MID, BOT, SUP`")
                    if value is True:
                        async with pool.acquire() as conn:
                            await conn.execute('UPDATE playerdata SET primarylane = $1 WHERE idplayer = $2',
                                               lane.upper(), member.id)
                        await ctx.send("Deine Hauptlane ist: " + lane.upper())

            else:
                await ctx.send("Du scheinst noch nicht registriert zu sein bitte tu dies zuerst mit !register")
        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='ign', help='Update deinen ingame namen')
    @commands.dm_only()
    async def ign(ctx, ign):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT firstname FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                await member.edit(nick=ign + " | " + row[0])
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET gametag = $1 WHERE idplayer = $2', ign, member.id)
                await ctx.send("Dein Nickname sieht nun folgendermaßen aus: `" + member.nick + "`")
            else:
                await ctx.send("Du scheinst noch nicht registriert zu sein bitte tu dies zuerst mit !register")
        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='lanes', help='Zeigt dir an welche Lanes du angegeben hast Spielen zu können')
    @commands.dm_only()
    async def lanes(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        mainlane = ""
        top = ":x:"
        jgl = ":x:"
        mid = ":x:"
        adc = ":x:"
        sup = ":x:"

        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                if row[3] is True:
                    top = ":white_check_mark:"
                if row[4] is True:
                    jgl = ":white_check_mark:"
                if row[5] is True:
                    mid = ":white_check_mark:"
                if row[6] is True:
                    adc = ":white_check_mark:"
                if row[7] is True:
                    sup = ":white_check_mark:"
                if row[8] is not None:
                    mainlane = row[8]
                await ctx.send("TOP  " + top + "\n" + "JGL   " + jgl + "\n" + "MID  " + mid + "\n" + "BOT  " + adc +
                               "\n" + "SUP   " + sup + "\n" + "Main Lane: " + mainlane)
            else:
                await ctx.send("Du bist noch nicht registriert bitte registriere dich zuerst mit `!register`")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='top', help='Sende diesen Command um uns mitzuteilen das du Top spielen kannst')
    @commands.dm_only()
    async def top(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow('SELECT top FROM playerdata WHERE idplayer = $1', member.id)
                if row[0] is True:
                    await ctx.send('Deine Einstellung wurde geändert du spielst keine Toplane')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET top = FALSE WHERE idplayer = $1', member.id)
                elif row[0] is False or row[0] is None:
                    await ctx.send('Deine Einstellung wurde geändert du spielst Toplane')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET top = TRUE WHERE idplayer = $1', member.id)
            else:
                await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='jgl', help='Sende diesen Command um uns mitzuteilen das du Jungle spielen kannst')
    @commands.dm_only()
    async def jgl(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow('SELECT jgl FROM playerdata WHERE idplayer = $1', member.id)
                if row[0] is True:
                    await ctx.send('Deine Einstellung wurde geändert du spielst keinen Jungle')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET jgl = FALSE WHERE idplayer = $1', member.id)
                elif row[0] is False or row[0] is None:
                    await ctx.send('Deine Einstellung wurde geändert du spielst Jungle')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET jgl = TRUE WHERE idplayer = $1', member.id)
            else:
                await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='mid', help='Sende diesen Command um uns mitzuteilen das du Mid spielen kannst')
    @commands.dm_only()
    async def mid(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow('SELECT mid FROM playerdata WHERE idplayer = $1', member.id)
                if row[0] is True:
                    await ctx.send('Deine Einstellung wurde geändert du spielst keine Midlane')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET mid = FALSE WHERE idplayer = $1', member.id)
                elif row[0] is False or row[0] is None:
                    await ctx.send('Deine Einstellung wurde geändert du spielst Midlane')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET mid = TRUE WHERE idplayer = $1', member.id)
            else:
                await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='adc', help='Sende diesen Command um uns mitzuteilen das du Bot spielen kannst',
                 aliases=("bot", "adcarry", "marksman"))
    @commands.dm_only()
    async def adc(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow('SELECT bot FROM playerdata WHERE idplayer = $1', member.id)
                if row[0] is True:
                    await ctx.send('Deine Einstellung wurde geändert du spielst keine Botlane')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET bot = FALSE WHERE idplayer = $1', member.id)
                elif row[0] is False or row[0] is None:
                    await ctx.send('Deine Einstellung wurde geändert du spielst Botlane')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET bot = TRUE WHERE idplayer = $1', member.id)
            else:
                await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='sup', help='Sende diesen Command um uns mitzuteilen das du Support spielen kannst',
                 aliases=("ks", "killsteal", "griagtkagold"))
    @commands.dm_only()
    async def sup(ctx):
        global pool
        poolfunc: Pool = pool
        schildkroete = False
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        user = ctx.message.author

        for member in guild.members:
            if member.id == user.id:
                break
        for role in member.roles:
            if role.name == "Schildkröte":
                schildkroete = True

        if schildkroete is True:
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', member.id)
            if row is not None:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow('SELECT sup FROM playerdata WHERE idplayer = $1', member.id)
                if row[0] is True:
                    await ctx.send('Deine Einstellung wurde geändert du spielst keinen Support')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET sup = FALSE WHERE idplayer = $1', member.id)
                elif row[0] is False or row[0] is None:
                    await ctx.send('Deine Einstellung wurde geändert du spielst Support')
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET sup = TRUE WHERE idplayer = $1', member.id)
            else:
                await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")

        elif schildkroete is False:
            await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                           "sind Schildkröten vorbehalten.")

    @bot.command(name='geo', alias=('geozukunft', 'viktor', 'meister', 'erde'), hidden=True)
    async def geo(ctx):
        await ctx.send("AHH DER DEFINTIV BESTE SOCIAL MEDIA MANAGER UND ADC FARM GOTT :innocent: ")

    @bot.command(name='schmidi', alias=('schmidi49', 'erik', 'schlechtersupport'), hidden=True)
    async def schmidi(ctx):
        await ctx.send("Du hast dich vermutlich verschrieben meintest du nicht `!gott` ?")

    @bot.command(name='gott', hidden=True)
    async def gott(ctx):
        await ctx.send("Meintest du womöglich `!schmidi`?")

    @bot.event
    async def on_ready():
        for guild in bot.guilds:
            if guild.id == GUILD:
                break

        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')

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
        print(error)

    bot.add_listener(newreaction, 'on_raw_reaction_add')
    bot.add_listener(removereaction,  "on_raw_reaction_remove")

    await bot.start(TOKEN)
    await client.run(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
