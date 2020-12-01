from discord import reaction, Client
from discord.ext import commands
from datetime import date, datetime
import locale
from main import Tokens
from asyncpg.pool import Pool
import asyncpg
import discord.utils
from discord.utils import get
import os




TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION
DB_USER = Tokens.DB_USER
DB_PW = Tokens.DB_PW
DB_HOST = Tokens.DB_HOST
DB_NAME = Tokens.DB_NAME
DB_PORT = Tokens.DB_PORT

pool: Pool = "eule"


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_listener(newreaction, 'on_raw_reaction_add')
    bot.add_listener(removereaction, "on_raw_reaction_remove")


async def newreaction(reaction):
    global pool
    pool = await asyncpg.create_pool(user=DB_USER, password=DB_PW, database=DB_NAME, host=DB_HOST, port=DB_PORT)
    currenttime = datetime.timestamp(datetime.now())
    async with pool.acquire() as conn:
        reactionmessage = await conn.fetchrow('SELECT type, discord_id FROM reactions WHERE message_id = $1',
                                              reaction.message_id)
        user = await conn.fetchrow('SELECT firstname FROM members WHERE discord_id = $1', reaction.user_id)

    if reactionmessage is not None:
        if reactionmessage['type'] == "RULES":
            if reaction.emoji.name == "✅":
                if user is None:
                    async with pool.acquire() as conn:
                        await conn.execute('INSERT INTO members VALUES ($1, $2, $3)', reaction.member.id,
                                           reaction.member.name, reaction.member.name)
                        await conn.execute('INSERT INTO league_player VALUES ($1)', reaction.member.id)
                        await conn.execute('INSERT INTO role_assign VALUES ($1, $2)', reaction.member.id, "Schildkröte")
                    await reaction.member.send("Hallo und herzlich Willkommen auf dem STT Discord Server ich bin "
                                               "Tommy!\n\n "
                                               "Mit !ign kannst du deinen Ingame Namen der auf dem Server angezeigt "
                                               "wird Ändern dieser ist Standardmäßig dein Discord Username. \n "
                                               "Mit !name kannst du einen Namen angeben der neben deinem Ingame Namen "
                                               "angezeigt wird. Dies kann dein Vorname sein oder wie auch immer du "
                                               "gennant werden möchtest.")
                async with pool.acquire() as conn:
                    await conn.execute('INSERT INTO audit_log(discord_id, action_type, timestamp) VALUES ($1, $2, $3)', reaction.member.id, "ACCEPT_RULES", currenttime)

        elif reactionmessage['type'] == "LANES":
            if user is not None:
                if reaction.emoji.name == "TopLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET top = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "Jungle":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET jgl = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "MidLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET mid = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "BotLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET adc = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "Support":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET sup = True WHERE discord_id = $1',
                                           reaction.member.id)
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, channel_id)"
                        "VALUES ($1,$2,$3,$4)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.channel_id)

        elif reactionmessage['type'] == "CLASH":
            return
        elif reactionmessage['type'] == "MAINLANE":
            if user is not None:
                if reaction.emoji.name == "TopLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "TOP",
                                           reaction.member.id)

                elif reaction.emoji.name == "Jungle":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "JGL",
                                           reaction.member.id)

                elif reaction.emoji.name == "MidLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "MID",
                                           reaction.member.id)

                elif reaction.emoji.name == "BotLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "BOT",
                                           reaction.member.id)

                elif reaction.emoji.name == "Support":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "SUP",
                                           reaction.member.id)

                async with pool.acquire() as conn:
                    await conn.execute(
                        'INSERT INTO reaction_history(discord_id, message_id, emoji_id, channel_id, timestamp) '
                        'VALUES ($1,$2,$3,$4,$5)',
                        reaction.user_id, reaction.message_id, reaction.emoji.id, reaction.channel_id,
                        currenttime)
                    results = await conn.fetch(
                        "SELECT * FROM reaction_history WHERE discord_id = $1 AND message_id = $2 "
                        "ORDER BY unique_id DESC", reaction.user_id, reaction.message_id)
                    if len(results) > 1:
                        to_delete = results[1]
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, channel_id)"
                            "VALUES ($1,$2,$3,$4)", to_delete['discord_id'], to_delete['message_id'],
                            to_delete['emoji_id'], to_delete['channel_id'])
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, channel_id)"
                        "VALUES ($1,$2,$3,$4)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.channel_id)



"""
    async with pool.acquire() as conn:
        event = await conn.fetchrow('SELECT * FROM clashdata WHERE "announceMessageID" = $1',
                                    reaction.message_id)
        player = await conn.fetchrow('SELECT "regnum" FROM playerdata WHERE "idplayer" = $1', reaction.user_id)
        stream = await conn.fetchrow('SELECT * FROM clashdata WHERE "streamMessageID" = $1', reaction.message_id)
        registerd = await conn.fetchrow('SELECT * FROM clashplayerdata WHERE idplayer = $1', reaction.user_id)

    if event is not None and player is not None and event['ended'] is False:

        epochtime = event['registrationTime']
        d = date.fromtimestamp(epochtime / 1000)
        locale.setlocale(locale.LC_TIME, "de-DE")
        day = d.strftime('%A')

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

    if stream is not None and player is not None and stream['ended'] is False and registerd is not None:

        for role in reaction.member.roles:
            if role.name == "Streamer":
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE clashplayerdata SET streaming = True WHERE idplayer = $1',
                                       reaction.user_id)
"""


async def removereaction(reaction):
    global pool
    pool = await asyncpg.create_pool(user=DB_USER, password=DB_PW, database=DB_NAME, host=DB_HOST, port=DB_PORT)
    currenttime = datetime.timestamp(datetime.now())
    async with pool.acquire() as conn:
        reactionmessage = await conn.fetchrow('SELECT type, discord_id FROM reactions WHERE message_id = $1',
                                              reaction.message_id)
        user = await conn.fetchrow('SELECT firstname FROM members WHERE discord_id = $1', reaction.user_id)

    if reactionmessage is not None:
        if reactionmessage['type'] == "RULES":
            if reaction.emoji.name == "✅":
                async with pool.acquire() as conn:
                    await conn.execute('INSERT INTO audit_log(discord_id, action_type, timestamp) VALUES ($1, $2, $3)', reaction.user_id, "DENY_RULES", currenttime)

        elif reactionmessage['type'] == "LANES":
            if user is not None:
                if reaction.emoji.name == "TopLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET top = False WHERE discord_id = $1',
                                           reaction.user_id)
                elif reaction.emoji.name == "Jungle":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET jgl = False WHERE discord_id = $1',
                                           reaction.user_id)
                elif reaction.emoji.name == "MidLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET mid = False WHERE discord_id = $1',
                                           reaction.user_id)
                elif reaction.emoji.name == "BotLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET adc = False WHERE discord_id = $1',
                                           reaction.user_id)
                elif reaction.emoji.name == "Support":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET sup = False WHERE discord_id = $1',
                                           reaction.user_id)

        elif reactionmessage['type'] == "CLASH":
            return

        elif reactionmessage['type'] == "MAINLANE":
            if user is not None:
                if reaction.emoji.name == "TopLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = NULL WHERE discord_id = $1 AND main = $2',
                                           reaction.user_id, "TOP")

                elif reaction.emoji.name == "Jungle":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = NULL WHERE discord_id = $1 AND main = $2',
                                           reaction.user_id, "JGL")

                elif reaction.emoji.name == "MidLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = NULL WHERE discord_id = $1 AND main = $2',
                                           reaction.user_id, "MID")

                elif reaction.emoji.name == "BotLane":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = NULL WHERE discord_id = $1 AND main = $2',
                                           reaction.user_id, "BOT")

                elif reaction.emoji.name == "Support":
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = NULL WHERE discord_id = $1 AND main = $2',
                                           reaction.user_id, "SUP")


"""    
    async with pool.acquire() as conn:
        event = await conn.fetchrow('SELECT * FROM clashdata WHERE "announceMessageID" = $1',
                                    reaction.message_id)
        player = await conn.fetchrow('SELECT "regnum" FROM playerdata WHERE "idplayer" = $1', reaction.user_id)
        stream = await conn.fetchrow('SELECT * FROM clashdata WHERE "streamMessageID" = $1', reaction.message_id)
        registerd = await conn.fetchrow('SELECT * FROM clashplayerdata WHERE idplayer = $1', reaction.user_id)

    if event is not None and player is not None and event['ended'] is False:

        epochtime = event['registrationTime']
        d = date.fromtimestamp(epochtime / 1000)
        locale.setlocale(locale.LC_TIME, "de-DE")
        day = d.strftime('%A')

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

    if stream is not None and player is not None and stream['ended'] is False and registerd is not None:
        async with pool.acquire() as conn:
            await conn.execute('UPDATE clashplayerdata SET streaming = False WHERE idplayer = $1',
                               reaction.user_id)
"""