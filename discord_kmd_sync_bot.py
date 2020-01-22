import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!syncbot ', description='A bot reporting recent block hash comparison across nodes.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

@bot.command()
async def get_hashes(ctx):
    msg = '```'
    r = requests.get('http://138.201.207.24/show_hashtips')
    if r.status_code == 200:
        hashtips = r.json()
        for ticker in hashtips:
            if ticker == 'last_updated':
                pass
            else:
                block = list(hashtips[ticker].keys())[0]
                if len(hashtips[ticker][block]) > 1:
                    # potentially forked!
                    for blockhash in hashtips[ticker][block]:
                        nodes = hashtips[ticker][block][blockhash]        
                        msg += "{:12s} FORK! Block {:10s} has hash {}\n".format("["+ticker+"]", "["+block+"]", "["+blockhash+"]")
                    pass
                else:
                    blockhash = list(hashtips[ticker][block].keys())[0]
                    nodes = hashtips[ticker][block][blockhash]
                    msg += "{:12s} OK! Block {:10s} has hash {}\n".format("["+ticker+"]", "["+block+"]", "["+blockhash+"]")
            if len(msg) > 1000:
                await ctx.send(msg+"```")
                msg = '```'
    else:
        msg = "`Bot's not here man... (API not responding).`"
        await ctx.send(msg)

bot.run(TOKEN)
