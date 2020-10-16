from discord.ext import commands
from datetime import date
import locale
from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_listener(newreaction, 'on_raw_reaction_add')
    bot.add_listener(removereaction, "on_raw_reaction_remove")


async def newreaction(reaction):
    pool = BetterBot.pool

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


async def removereaction(reaction):
    pool = reaction.bot.pool

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
