import discord 
import os 
from discord.ext import commands 

bot = commands.Bot(command_prefix=',')

@bot.event
async def on_ready(): 
    print(f'{bot.user} has logged in.')
    bot.load_extension('cogs.Music')
    bot.load_extension('cogs.ImagesCog')


#HELP
@bot.event 
async def on_message(message):
    if message.content.startswith('sayhelp'):
        embedVar = discord.Embed(title="Commands", description=f"""Hello! Use **sayhelp** to know about the commands.
        Commands found: 8
        Categories found: 1""", color=0x00ff00)
        embedVar.add_field(name="Prefix ", value="For anything commands use the prefix **,** " ,inline=False)
        embedVar.add_field(name="About the role bot", value="It's importante that the bot must have all permissions. " ,inline=False)
        embedVar.add_field(name="Learn more ", value=f"To learn more about the bot -> https://github.com/vLeeH/MikasaBot : " ,inline=False)
        embedVar.add_field(name=":notes: - Musics commands (8)", value="`,play` |`,pause` | `,resume` | `,skip` | `,now_playing(np)` | `,queue` | `,stop` | `info`", inline=False)

        await message.delete()
        await message.channel.send(embed=embedVar)

    await bot.process_commands(message)  


#ERROR
@bot.event
async def on_command_error(ctx, error): 
    if isinstance(error, commands.CommandNotFound): 
        await ctx.send('_Invalid command_. Use **sayhelp** to learn about the commands.')
    
        await ctx.message.delete()


with open("src/token", "rt+") as f:
    bot.run(str(f.read()))