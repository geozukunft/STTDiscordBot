import uuid
from datetime import datetime
from datetime import timedelta as td

import asyncpg
from asyncpg.pool import Pool
from pyot.models import lol

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION
DB_USER = Tokens.DB_USER
DB_PW = Tokens.DB_PW
DB_HOST = Tokens.DB_HOST
DB_NAME = Tokens.DB_NAME
DB_PORT = Tokens.DB_PORT

# noinspection PyTypeChecker
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
        league_player = await conn.fetchrow(
            'SELECT "summonerName" FROM leaguesummoner WHERE discord_id = $1 AND verified = True', reaction.user_id)

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
                                               "Mit `!ign <name>` kannst du deinen Ingame Namen der auf dem Server angezeigt "
                                               "wird Ändern dieser ist Standardmäßig dein Discord Username. \n "
                                               "Mit `!name <name>` kannst du einen Namen angeben der neben deinem Ingame Namen "
                                               "angezeigt wird. Dies kann dein Vorname sein oder wie auch immer du "
                                               "gennant werden möchtest.\n\n"
                                               "Wenn du LoL Spieler bist und bei Turnieren mitspielen möchtest oder "
                                               "auch Spieler für das nächste Clash Turnier suchst dann füge einfach "
                                               "einen deiner LoL Accounts (du kannst auch mehrere hinzufügen solltest "
                                               "du Smurfs haben) mit `!addlol <ingamename>` deinen Account hinzu. "
                                               "Dies hilft uns dabei dich bei Turnieren in einfacher in Lobbys "
                                               "einladen zu können bzw. bei Clash Teams auf dem gleichen Spielniveau "
                                               "zusammenzustellen. Solltest du auch zu solchen Clash Teams "
                                               "zugeteilt werden können verifiziere deinen Account nach dem "
                                               "hinzufügen. Näheres Teile ich dir nach dem hinzufügen mit.")
                async with pool.acquire() as conn:
                    await conn.execute('INSERT INTO audit_log(discord_id, action_type, timestamp) VALUES ($1, $2, $3)',
                                       reaction.member.id, "ACCEPT_RULES", currenttime)
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

        elif reactionmessage['type'] == "LANES":
            valid: bool = False  # Flag if emoji is a valid one for this message type
            if user is not None:
                if reaction.emoji.name == "TopLane":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET top = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "Jungle":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET jgl = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "MidLane":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET mid = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "BotLane":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET adc = True WHERE discord_id = $1',
                                           reaction.member.id)
                elif reaction.emoji.name == "Support":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET sup = True WHERE discord_id = $1',
                                           reaction.member.id)
                if not valid:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                            "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                            reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

        elif reactionmessage['type'] == "CLASH":
            if league_player is not None:
                emoji_to_number = {
                    '1️⃣': 0,
                    '2️⃣': 1,
                    '3️⃣': 2,
                    '4️⃣': 3,
                    '5️⃣': 4,
                    '6️⃣': 5,
                    '7️⃣': 6,
                    '8️⃣': 7,
                    '9️⃣': 8,
                    '🔟': 9
                }
                number = emoji_to_number.get(reaction.emoji.name, 10)
                async with pool.acquire() as conn:
                    event = await conn.fetchrow(
                        'SELECT event_times, id FROM clash_events WHERE "announceMessageId" = $1 AND ended = False',
                        reaction.message_id)
                if event is not None:
                    times = len(event['event_times'])
                    if number < times:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                'INSERT INTO clash_participation(clash_id, "participationTime", discord_id) '
                                'VALUES ($1, $2, $3)', event['id'], event['event_times'][number], reaction.user_id)
                    else:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, "
                                "channel_id)"
                                "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                                reaction.emoji.id, reaction.emoji.name, reaction.channel_id)
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, "
                        "channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

        elif reactionmessage['type'] == "MAINLANE":
            valid: bool = False  # Flag if emoji is a valid one for this message type
            if user is not None:
                if reaction.emoji.name == "TopLane":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "TOP",
                                           reaction.member.id)

                elif reaction.emoji.name == "Jungle":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "JGL",
                                           reaction.member.id)

                elif reaction.emoji.name == "MidLane":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "MID",
                                           reaction.member.id)

                elif reaction.emoji.name == "BotLane":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "BOT",
                                           reaction.member.id)

                elif reaction.emoji.name == "Support":
                    valid = True
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE league_player SET main = $1 WHERE discord_id = $2', "SUP",
                                           reaction.member.id)
                if valid:
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
                            if to_delete['emoji_id'] != reaction.emoji.id:
                                await conn.execute(
                                    "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, channel_id)"
                                    "VALUES ($1,$2,$3,$4)", to_delete['discord_id'], to_delete['message_id'],
                                    to_delete['emoji_id'], to_delete['channel_id'])
                else:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                            "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                            reaction.emoji.id, reaction.emoji.name, reaction.channel_id)
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

        elif reactionmessage['type'] == "VERIFY":
            if user is not None:
                if reaction.emoji.name == "✅":
                    async with pool.acquire() as conn:
                        verifyrequest = await conn.fetchrow(
                            'SELECT * FROM verify WHERE discord_id = $1 AND successful is Null', reaction.user_id)
                        delta = datetime.now() - verifyrequest['creation']
                        if delta > td(seconds=2):
                            summoner = await conn.fetchrow(
                                'SELECT "summonerID", "summonerName" FROM leaguesummoner WHERE puuid = $1',
                                verifyrequest['puuid'])
                            try:
                                code = await lol.ThirdPartyCode(summoner['summonerID'], verifyrequest['region']).get()
                                code = code.code
                                valid = True
                            except Exception as error:
                                code = ""
                                valid = False
                                print(error)
                            if valid:
                                if verifyrequest['code'] == uuid.UUID(code):
                                    await conn.execute('UPDATE leaguesummoner SET verified = True WHERE puuid = $1',
                                                       verifyrequest['puuid'])
                                    await conn.execute(
                                        'INSERT INTO message_to_send(discord_id, message_type_id, "summonerName") VALUES '
                                        '($1,$2,$3)', reaction.user_id, 0, summoner['summonerName'])
                                    await conn.execute('UPDATE verify SET successful = True WHERE code = $1', verifyrequest['code'])
                                else:
                                    await conn.execute('INSERT INTO message_to_send(discord_id, message_type_id) VALUES '
                                                       '($1,$2)', reaction.user_id, 1)
                                    await conn.execute('UPDATE verify SET successful = False WHERE code = $1', verifyrequest['code'])
                            else:
                                await conn.execute('INSERT INTO message_to_send(discord_id, message_type_id) VALUES '
                                                   '($1,$2)', reaction.user_id, 1)
                                await conn.execute('UPDATE verify SET successful = False WHERE code = $1', verifyrequest['code'])
                        else:
                            print("The bot tried to verify itself LOL")

        elif reactionmessage['type'] == "ROLES":
            valid: bool = False  # Flag if emoji is a valid one for this message type
            if user is not None:
                if reaction.emoji.name == "clash":

                    if league_player:
                        valid = True
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO role_assign VALUES ($1,$2)', reaction.user_id, "Clash")
                    else:
                        await reaction.member.send("Du kannst dich leider noch nicht für Organisierte Clash Events "
                                                   "anmelden da du noch keinen verifizierten League Account bei mir "
                                                   "hinzugefügt hast. Du kannst den Status deiner League Accounts mit "
                                                   "!listlol überprüfen. Falls du noch gar keine Accounts hast kannst "
                                                   "du diese mit !addlol hinzufügen.")

                if not valid:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                            "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                            reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

        elif reactionmessage['type'] == "GAMES":
            if user is not None:
                async with pool.acquire() as conn:
                    RoleEmoji = await conn.fetchrow('SELECT * FROM roles WHERE "emojiID" = $1', reaction.emoji.id)
                if RoleEmoji is not None:
                    async with pool.acquire() as conn:
                        await conn.execute('INSERT INTO role_assign VALUES ($1, $2)', reaction.member.id, RoleEmoji['role_name'])
                else:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                            "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                            reaction.emoji.id, reaction.emoji.name, reaction.channel_id)
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)




async def removereaction(reaction):
    global pool
    pool = await asyncpg.create_pool(user=DB_USER, password=DB_PW, database=DB_NAME, host=DB_HOST, port=DB_PORT)
    currenttime = datetime.timestamp(datetime.now())
    async with pool.acquire() as conn:
        reactionmessage = await conn.fetchrow('SELECT type, discord_id FROM reactions WHERE message_id = $1',
                                              reaction.message_id)
        user = await conn.fetchrow('SELECT firstname FROM members WHERE discord_id = $1', reaction.user_id)
        league_player = await conn.fetchrow(
            'SELECT "summonerName" FROM leaguesummoner WHERE discord_id = $1 AND verified = True', reaction.user_id)

    if reactionmessage is not None:
        if reactionmessage['type'] == "RULES":
            if reaction.emoji.name == "✅":
                async with pool.acquire() as conn:
                    await conn.execute('INSERT INTO audit_log(discord_id, action_type, timestamp) VALUES ($1, $2, $3)',
                                       reaction.user_id, "DENY_RULES", currenttime)

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
            if league_player is not None:
                emoji_to_number = {
                    '1️⃣': 0,
                    '2️⃣': 1,
                    '3️⃣': 2,
                    '4️⃣': 3,
                    '5️⃣': 4,
                    '6️⃣': 5,
                    '7️⃣': 6,
                    '8️⃣': 7,
                    '9️⃣': 8,
                    '🔟': 9
                }
                number = emoji_to_number.get(reaction.emoji.name, 10)
                async with pool.acquire() as conn:
                    event = await conn.fetchrow(
                        'SELECT event_times, id FROM clash_events WHERE "announceMessageId" = $1 AND ended = False',
                        reaction.message_id)
                if event is not None:
                    times = len(event['event_times'])
                    if number < times:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                'DELETE FROM clash_participation WHERE clash_id = $1 AND "participationTime" = $2 AND '
                                'discord_id = $3', event['id'], event['event_times'][number], reaction.user_id)
                    else:
                        async with pool.acquire() as conn:
                            await conn.execute(
                                "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, "
                                "channel_id) VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                                reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

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

        elif reactionmessage['type'] == "ROLES":
            valid: bool = False  # Flag if emoji is a valid one for this message type
            if user is not None:
                if reaction.emoji.name == "clash":

                    if league_player:
                        valid = True
                        async with pool.acquire() as conn:
                            await conn.execute('INSERT INTO role_assign VALUES ($1,$2,$3)', reaction.user_id, "Clash", True)
                            await conn.execute('DELETE FROM clash_participation WHERE discord_id = $1 and "participationTime" > $2', reaction.user_id,
                                               datetime.datetime.utcnow().timestamp())

                if not valid:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                            "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                            reaction.emoji.id, reaction.emoji.name, reaction.channel_id)


        elif reactionmessage['type'] == "GAMES":
            if user is not None:
                async with pool.acquire() as conn:
                    RoleEmoji = await conn.fetchrow('SELECT * FROM roles WHERE "emojiID" = $1', reaction.emoji.id)
                if RoleEmoji is not None:
                    async with pool.acquire() as conn:
                        await conn.execute('INSERT INTO role_assign VALUES ($1, $2, $3)', reaction.user_id, RoleEmoji['role_name'], True)
                else:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                            "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                            reaction.emoji.id, reaction.emoji.name, reaction.channel_id)
            else:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO reaction_to_delete(discord_id, message_id, emoji_id, emoji_name, channel_id)"
                        "VALUES ($1,$2,$3,$4,$5)", reaction.user_id, reaction.message_id,
                        reaction.emoji.id, reaction.emoji.name, reaction.channel_id)

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
