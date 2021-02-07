import locale
import re
from datetime import datetime
from pyot.models import lol
import discord.embeds
from dateutil import tz
from discord.ext import commands

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(getclash)
    bot.add_command(listclash)
    bot.add_command(endreg)
    bot.add_command(aclash)
    bot.add_command(printclash)


@commands.command(name='lclash', help="Lists all Clash Events which have not yet been announced")
@commands.has_any_role('Admin', 'Social Media Manager')
async def listclash(ctx):
    pool = ctx.bot.pool
    currenttime: float = datetime.timestamp(datetime.now())
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
        locale.setlocale(locale.LC_TIME, "de_DE")
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


@commands.command(name='clash', help="Format !clash <id> <time> prints opens the registraton for the clash event with "
                                     "the specifc id")
@commands.has_any_role('Admin', 'Social Media Manager')
async def getclash(ctx, *args):
    pool = ctx.bot.pool
    clash_id: list
    times = []
    event_times = []
    event_times_unix = []
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    if len(args) < 2:
        await ctx.send("Bitte stelle sicher an erster Stelle die ID des Clash Events das du erstellen möchtest "
                       "gelistet zu haben und danach bis zu 10 verschiedene Uhrzeiten!")
    if len(args) >= 2:
        clash_id = re.findall(r"(?<!\d)\d{4}(?!\d)", args[0])
        if clash_id:
            async with pool.acquire() as conn:
                event = await conn.fetchrow('SELECT * FROM clash_events WHERE id = $1', int(clash_id[0]))

            for arg in args[1:]:
                rawtime = re.findall(r"^(?:[0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", arg)
                times.append(rawtime)

            playday = datetime.utcfromtimestamp(event['registrationTime'])
            for time in times:
                splittime = time[0].split(":")
                temptime = playday.replace(hour=int(splittime[0]), minute=int(splittime[1]),
                                           tzinfo=tz.gettz('Europe/Vienna'))
                event_times.append(temptime)
                event_times_unix.append(temptime.timestamp())
            locale.setlocale(locale.LC_TIME, "de_DE")
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
            for _ in event_times:
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


@commands.command(name='aclash', help="Prints all announced and ready for register clash events!")
@commands.has_any_role('Admin', 'Social Media Manager')
async def aclash(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        announced_events = await conn.fetch(
            'SELECT * FROM clash_events WHERE announced = True AND ended = False ORDER BY "registrationTime"')

        embed = discord.Embed(title="Clash mit laufender Registrierung",
                              description="Für diese Clashspieltage kann man sich bereits anmelden!")
        for event in announced_events:
            locale.setlocale(locale.LC_TIME, "de_DE")
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


@commands.command(name='endreg', help='Ends the registration for a specific Clash Event! !endreg <id>')
@commands.has_any_role('Admin', 'Social Media Manager')
async def endreg(ctx, *args):
    pool = ctx.bot.pool

    clash_id = re.findall(r"(?<!\d)\d{4}(?!\d)", args[0])

    if clash_id:
        async with pool.acquire() as conn:
            await conn.execute('UPDATE clash_events SET ended = True WHERE id = $1', int(clash_id[0]))
            clash_event = await conn.fetchrow('SELECT * FROM clash_events WHERE id = $1', int(clash_id[0]))
        await ctx.send(f'Die Registrierung für Clash mit der Event ID {clash_id[0]} wurde beendet. Ab sofort sind '
                       f'keine Registrierungen für dieses Event mehr möglich.')
        channel = discord.utils.get(ctx.bot.get_all_channels(), name='clash-announcements')
        msg = await channel.fetch_message(clash_event['announceMessageId'])
        print(msg)
        embed = msg.embeds[0]
        embed.add_field(name="Die Registrierung für dieses Event wurde beendet!",
                        value="Deine Registrierung kann nicht mehr verändert werden!", inline=False)
        await msg.edit(embed=embed)
        print(embed)
    else:
        await ctx.send("Bitte stelle sicher an erster Stelle die ID des Clash Events bei welchem du die Registrierung "
                       "beenden möchtest. Du scheinst die ID des Events vergessen zu haben!")


@commands.command(name='pclash', help='Prints the set teams for this specific Clash Event')
@commands.has_any_role('Admin', 'Social Media Manager')
async def printclash(ctx, *args):
    pool = ctx.bot.pool

    clash_id = re.findall(r"(?<!\d)\d{4}(?!\d)", args[0])

    if clash_id:
        async with pool.acquire() as conn:
            event_times_record = await conn.fetchrow('SELECT event_times FROM clash_events WHERE id = $1',
                                                     int(clash_id[0]))

            for event_time_list in event_times_record:
                for event_time in event_time_list:
                    try:
                        teams_record = await conn.fetchrow(
                            'SELECT COUNT(*) FROM clash_participation WHERE clash_id = $1 AND teamlead = True AND '
                            '"participationTime" = $2', int(clash_id[0]), event_time)

                        i: int = 0

                        for team in range(int(teams_record[0])):

                            try:
                                teamlead = await conn.fetchrow(
                                    'SELECT * FROM clash_participation WHERE clash_id = $1 AND teamlead = True AND '
                                    'team_id = $2 AND "participationTime" = $3', int(clash_id[0]), i, event_time)
                            except Exception as error:
                                print(error)
                            teamplayers = await conn.fetch(
                                'SELECT * FROM clash_participation WHERE clash_id = $1 AND team_id = $2 AND '
                                ' "participationTime" = $3 ORDER BY CASE lane WHEN \'top\' THEN 1 WHEN \'jgl\' THEN 2 '
                                'WHEN \'mid\' THEN 3 WHEN \'adc\' THEN 4 WHEN \'sup\' THEN 5 ELSE 6 end ',
                                int(clash_id[0]), i, event_time)
                            locale.setlocale(locale.LC_TIME, "de-DE")
                            from_zone = tz.gettz('UTC')
                            to_zone = tz.gettz('Europe/Vienna')
                            playtime = datetime.utcfromtimestamp(teamlead['participationTime'])
                            playtime = playtime.replace(tzinfo=from_zone)
                            cetplaytime = playtime.astimezone(to_zone).strftime('%A %d %b %H:%M')
                            embed_title = f'Clash am {cetplaytime}'
                            embed_desc = f'Teamlead: <@{teamlead["discord_id"]}>'
                            embed = discord.Embed(title=embed_title, description=embed_desc)
                            embed.add_field(name='Einteilung:',
                                            value=f'<:TopLane:748296960586416168> <@{teamplayers[0]["discord_id"]}>\n'
                                                  f'<:Jungle:748296968295677993> <@{teamplayers[1]["discord_id"]}>\n'
                                                  f'<:MidLane:748296979322241145> <@{teamplayers[2]["discord_id"]}>\n'
                                                  f'<:BotLane:807773264184737814> <@{teamplayers[3]["discord_id"]}>\n'
                                                  f'<:Support:748296949689483385> <@{teamplayers[4]["discord_id"]}>',
                                            inline=False)
                            i += 1
                            await ctx.channel.send(content=None, embed=embed)

                    except TypeError as error:
                        print(error)
                        print("Da gibts halt kein Team für die Uhrzeit")
                    except Exception as error:
                        print(error)
