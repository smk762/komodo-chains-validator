import os
import time
import asyncio
import discord
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')

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

# sends bot message every 5 min if there are failed syncs, or every 4 hours otherwise.
async def get_sync_loop():
    await bot.wait_until_ready()
    loop_count = 13
    while not bot.is_closed():
        print(loop_count)
        channel = bot.get_channel(int(CHANNEL))
        try:
            msg = ''
            r = requests.get('http://138.201.207.24/show_hashtips')
            if r.status_code == 200:
                hashtips = r.json()
                for ticker in hashtips:
                    if len(msg) > 1500:
                        await channel.send(msg)
                        msg = ''
                    if loop_count < 12:
                        msg = get_sync_msg(hashtips, ticker, msg)
                    else:
                        msg = get_sync_msg(hashtips, ticker, msg, False)
                await channel.send(msg)
            else:
                msg = ":zzz: `Bot's not here man... (Sync API is down!).`"
                await channel.send(msg)
        except Exception as e:
            print(str(e))
        await asyncio.sleep(3600)
        if loop_count < 12:
            loop_count += 1
        else:
            loop_count = 0

def get_sync_msg(hashtips, ticker, msg, failed_only=True):
    if ticker == 'last_updated':
        pass
    else:
        block = list(hashtips[ticker].keys())[0]
        if len(hashtips[ticker][block]) > 1:
            # potentially forked!
            for blockhash in hashtips[ticker][block]:
                nodes = hashtips[ticker][block][blockhash]      
                msg += ":rage: `{:12s} FORK! Block {:10s} has hash {} for {}\n".format("["+ticker+"]", "["+block+"]", "["+blockhash+"]", "["+nodes+"]`")
        elif not failed_only:
            blockhash = list(hashtips[ticker][block].keys())[0]
            nodes = hashtips[ticker][block][blockhash]
            msg += ":koala: `{:12s} OK! Block {:10s} has hash {}\n".format("["+ticker+"]", "["+block+"]", "["+blockhash+"]`")
    return msg

@bot.command()
async def get_hashes(ctx):
    msg = ''
    r = requests.get('http://138.201.207.24/show_hashtips')
    if r.status_code == 200:
        hashtips = r.json()
        for ticker in hashtips:
            msg = get_sync_msg(msg)
            if len(msg) > 1000:
                await ctx.send(msg)
                msg = ''
    else:
        msg = ":sleeping_accommodation: `Bot's not here man... (API not responding).`"
        await ctx.send(msg)

bot.loop.create_task(get_sync_loop())
bot.run(TOKEN)
