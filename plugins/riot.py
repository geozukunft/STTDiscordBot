from discord.ext import commands
from asyncpg.pool import Pool
import re

from main import Tokens, watcher

from pyot.models import lol
from pyot.utils import loop_run
from pyot.core import Gatherer
import pyot.core

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(matchcount)
    bot.add_command(mc)
    bot.add_command(addlolacc)


@commands.command()
async def matchcount(ctx, summonername):
    gameIds = []
    partId: int
    goldSum: int = 0
    kills: int = 0
    deaths: int = 0
    summoner = watcher.summoner.by_name(my_region, summonername)
    matchlist = watcher.match.matchlist_by_account(my_region, summoner['accountId'])
    for match in matchlist['matches']:
        gameIds.append(match['gameId'])

    for match in gameIds:
        gameData = watcher.match.by_id(my_region, match)
        for participant in gameData['participantIdentities']:
            if summonername == participant['player']['summonerName']:
                partId = int(participant['participantId'])
        goldSum += int(gameData['participants'][partId - 1]['stats']['goldEarned'])
        kills += int(gameData['participants'][partId - 1]['stats']['kills'])
        deaths += int(gameData['participants'][partId - 1]['stats']['deaths'])
    await ctx.send("Gold Earned: " + goldSum + "\n"
                                               "Total Kills: " + kills + "\n"
                                                                         "Total Deaths: " + deaths + "\n")


@commands.command(name='addlol',
                  help="Mit diesem Befehl kannst du einen League Account hinzufügen oder auch dessen Daten updaten (Daten werden einmal täglich automatisch akuallisiert)! Achte hierbei auf eine korrekte Schreibweise sonst kann ich dich nicht finden!")
@commands.dm_only()
async def addlolacc(ctx, summonername):
    pool = ctx.bot.pool

    summoner = await lol.Summoner(name=summonername, platform="EUW1").get()
    print(summoner)

    async with pool.acquire() as conn:
        lsummoner = await conn.fetchrow('SELECT "summonerName", "summonerLevel" FROM leaguesummoner WHERE puuid = $1',
                                        summoner.puuid)
    if lsummoner is not None:
        async with pool.acquire() as conn:
            usummoner = await conn.execute(
                'UPDATE leaguesummoner SET "accountID" = $1, "summonerID" = $2, "summonerName" = $3, '
                '"profileIconId" = $4, "summonerLevel" = $5, "revisionDate" = $6 WHERE puuid = $7',
                summoner.account_id, summoner.id, summoner.name, summoner.profile_icon_id, summoner.level,
                summoner.revision_date.timestamp(), summoner.puuid)
            ctx.send(f'Dein Account {summoner.name} wurde geupdated dein aktuelles Level ist: {summoner.level}')
    else:
        async with pool.acquire() as conn:
            accounts = await conn.fetch('SELECT "summonerName" FROM leaguesummoner WHERE discord_id = $1',
                                        ctx.author.id)
            if accounts is None:
                await conn.execute(
                    'INSERT INTO leaguesummoner(discord_id, "accountID", "summonerID", puuid, "summonerName", '
                    '"profileIconId", "summonerLevel", "revisionDate", region, "PrimaryAcc") '
                    'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ',
                    ctx.author.id, summoner.account_id, summoner.id, summoner.puuid, summoner.name,
                    summoner.profile_icon_id, summoner.level,
                    summoner.revision_date.timestamp(), summoner.region, True)
                ctx.send(f'Herzlichen Glückwunsch du hast deinen League Account {summoner.name} hinzugefügt. \n'
                         f'Du kannst mit `!addlol <ingamename>` auch noch weitere Accounts hinzufügen.\nMit '
                         f'`!changemain` kannst du sofern du weitere Accounts hinzufügst deinen primären Account '
                         f'ändern. \nMit `!verify <ingamename> kannst du einen Account verifzieren damit sich niemand '
                         f'anders als du ausgeben kann. Die Verifzierung deines Accounts ist auch nötig um sich '
                         f'für die organisierten Clash Teams anmelden zu können. \n Um einen Account wieder zu '
                         f'entfernen benutze `!removelol <ingamename>` beachte dabei solltest du dann keine Accounts '
                         f'mehr haben kannst du auch nicht mehr an internen Turnieren oder organisierten Clash Teams '
                         f'teilnehmen.')
            else:
                await conn.execute(
                    'INSERT INTO leaguesummoner(discord_id, "accountID", "summonerID", puuid, "summonerName", '
                    '"profileIconId", "summonerLevel", "revisionDate", region, "PrimaryAcc") '
                    'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ',
                    ctx.author.id, summoner.account_id, summoner.id, summoner.puuid, summoner.name,
                    summoner.profile_icon_id, summoner.level,
                    summoner.revision_date.timestamp(), summoner.region, False)
                ctx.send(f'Herzlichen Glückwunsch du hast einen weiteren League Account mit dem Namen {summoner.name} '
                         f'hinzugefügt. \n '
                         f'Du kannst mit `!addlol <ingamename>` auch noch weitere Accounts hinzufügen.\nMit '
                         f'`!changemain` kannst du sofern du weitere Accounts hinzufügst deinen primären Account '
                         f'ändern. \nMit `!verify <ingamename> kannst du einen Account verifzieren damit sich niemand '
                         f'anders als du ausgeben kann. Die Verifzierung deines Accounts ist auch nötig um sich '
                         f'für die organisierten Clash Teams anmelden zu können. \n Um einen Account wieder zu '
                         f'entfernen benutze `!removelol <ingamename>` beachte dabei solltest du dann keine Accounts '
                         f'mehr haben kannst du auch nicht mehr an internen Turnieren oder organisierten Clash Teams '
                         f'teilnehmen.')


@commands.command()
async def mc(ctx, summonername):
    goldSum: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    i: int = 0
    summoner = await lol.Summoner(name=summonername, platform="EUW1").get()
    responses = []
    matchlist = await lol.MatchHistory(summoner.account_id).query(begin_index=100).get()
    for match in matchlist.matches:
        matchdata = await lol.match.Match(match.id).get()
        for team in matchdata.teams:
            for participant in team.participants:
                if summonername == participant.summoner_name:
                    goldSum += participant.stats.gold_earned
                    kills += participant.stats.kills
                    deaths += participant.stats.deaths
                    assists += participant.stats.assists
                    print("game" + str(i))
                    i += 1
        temp = await lol.Champion(match.champion.id).get()
        responses.append(temp.name)

    await ctx.send("Kills: " + str(kills))
    await ctx.send("Deaths: " + str(deaths))
    await ctx.send("Assists: " + str(assists))
    await ctx.send("Gold Earned: " + str(goldSum))
    # await ctx.send(responses)
    # await ctx.send(responses.count('Sylas'))
