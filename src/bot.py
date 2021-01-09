import discord 
import os 
from discord.ext import commands 

bot = commands.Bot(command_prefix=',')

@bot.event
async def on_ready(): 
    print(f'{bot.user} has logged in.')
    bot.load_extension('cogs.Music')
    bot.load_extension('cogs.ImagesCog')
    

with open("src/token", "rt+") as f:
    bot.run(str(f.read()))