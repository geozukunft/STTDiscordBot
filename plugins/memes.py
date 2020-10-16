from discord.ext import commands

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.my_region
api_key = Tokens.api_key


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(geo)
    bot.add_command(schmidi)
    bot.add_command(gott)


@commands.command(name='geo', alias=('geozukunft', 'viktor', 'meister', 'erde'), hidden=True)
async def geo(ctx):
    await ctx.send("AHH DER DEFINTIV BESTE SOCIAL MEDIA MANAGER UND ADC FARM GOTT :innocent: ")


@commands.command(name='schmidi', alias=('schmidi49', 'erik', 'schlechtersupport'), hidden=True)
async def schmidi(ctx):
    await ctx.send("Du hast dich vermutlich verschrieben meintest du nicht `!gott` ?")


@commands.command(name='gott', hidden=True)
async def gott(ctx):
    await ctx.send("Meintest du womöglich `!schmidi`?")
