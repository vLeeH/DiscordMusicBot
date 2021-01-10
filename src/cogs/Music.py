import wavelink
import asyncio
import datetime
import discord
import humanize
import itertools
import re
import sys
import traceback
from discord.ext import commands
from typing import Union
import controller

class MusicController:

    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.channel = None

        self.next = asyncio.Event()
        self.queue = asyncio.Queue()

        self.volume = 40
        self.now_playing = None

        self.bot.loop.create_task(self.controller_loop())

    async def controller_loop(self):
        await self.bot.wait_until_ready()

        player = self.bot.wavelink.get_player(self.guild_id)
        await player.set_volume(self.volume)

        while True:
            if self.now_playing:
                await self.now_playing.delete()

            self.next.clear()

            song = await self.queue.get()
            await player.play(song)
            self.now_playing = await self.channel.send(f'Now playing: `{song}`')

            await self.next.wait()


class Music(commands.Cog): 
    pass
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())


    async def start_nodes(self):
        await self.bot.wait_until_ready()
        await self.bot.wavelink.initiate_node(host='127.0.0.1',port=2333,rest_uri='http://127.0.0.1:2333',password='testing',identifier='TEST',region='us_central')
    

    async def on_event_hook(self, event):
        """Node hook callback."""
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            controller = self.get_controller(event.player)
            controller.next.set()


    def get_controller(self, value: Union[commands.Context, wavelink.Player]):
        if isinstance(value, commands.Context):
            gid = value.guild.id
        else:
            gid = value.guild_id

        try:
            controller = self.controllers[gid]
        except KeyError:
            controller = MusicController(self.bot, gid)
            self.controllers[gid] = controller

        return controller


    async def cog_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def cog_command_error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


    #Play command and join command☑️
    @commands.command()
    async def play(self, ctx, *, query: str, channel: discord.VoiceChannel = None):
        if not channel:
            print('join command worked')
            try: 
                channel = ctx.author.voice.channel
            except AttributeError: 
                raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')
            
            player = self.bot.wavelink.get_player(ctx.guild.id)
            if not player.is_connected:
                await ctx.send(f'**Joined** `{channel.name}`  :page_facing_up: And for questions: `sayhelp`')
                try:
                    await player.connect(channel.id)
                except Exception as c:  
                    print(f'[ERRO] {c}')

        tracks = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')

        if not tracks:
            return await ctx.send('**[ERROR]**_Could not find any songs with that query_:interrobang:')

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.connect_)
        
        await ctx.send(f'**Playing** :notes: `{str(tracks[0])}` - Now!')
        await player.play(tracks[0])
    

    #Pause command☑️.
    @commands.command()
    async def pause(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('**[ERROR]** I am not currently playing anything!', delete_after=15)

        await ctx.send(':pause_button: **Pausing the song**', delete_after=15)
        await player.set_pause(True) #put a pause


    #Resume player  from a paused state command☑️.
    @commands.command() 
    async def resume(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.paused:
            return await ctx.send('**[ERROR]** I am not currently paused!', delete_after=15)

        await ctx.send(':play_pause: **Resuming the player!**', delete_after=15)
        await player.set_pause(False) #stop the pause


    #Skip the currently playing song☑️.
    @commands.command()
    async def skip(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('**[ERROR]** I am not currently playing anything!', delete_after=15)

        await ctx.send('Skipping the song!', delete_after=15)
        await player.stop()


    #Retrieve the currently playing song☑️.
    @commands.command(aliases=['np', 'nowplaying'])
    async def now_playing(self, ctx):
        
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.current:
            return await ctx.send('I am not currently playing anything!')

        controller = self.get_controller(ctx)
        await controller.now_playing.delete()

        controller.now_playing = await ctx.send(f':notes: **Now playing:** `{player.current}`')


    #Retrieve information on the next 5 songs from the queue.
    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        controller = self.get_controller(ctx)

        if not player.current or not controller.queue._queue:
            return await ctx.send('There are no songs currently in the queue.', delete_after=20)

        upcoming = list(itertools.islice(controller.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{str(song)}`**' for song in upcoming)
        embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)}', description=fmt)

        await ctx.send(embed=embed)


    #Stop and disconnect the player and controller.
    @commands.command(aliases=['disconnect', 'dc'])
    async def stop(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)

        try:
            del self.controllers[ctx.guild.id]
        except KeyError:
            await player.disconnect()
            return await ctx.send('There was no controller to stop.')

        await player.disconnect()
        await ctx.send('Disconnected player and killed controller.', delete_after=20)


    #Retrieve various Node/Server/Player information.
    @commands.command()
    async def info(self, ctx):
        
        player = self.bot.wavelink.get_player(ctx.guild.id)
        node = player.node

        used = humanize.naturalsize(node.stats.memory_used)
        total = humanize.naturalsize(node.stats.memory_allocated)
        free = humanize.naturalsize(node.stats.memory_free)
        cpu = node.stats.cpu_cores

        fmt = f'**WaveLink:** `{wavelink.__version__}`\n\n' \
              f'Connected to `{len(self.bot.wavelink.nodes)}` nodes.\n' \
              f'Best available Node `{self.bot.wavelink.get_best_node().__repr__()}`\n' \
              f'`{len(self.bot.wavelink.players)}` players are distributed on nodes.\n' \
              f'`{node.stats.players}` players are distributed on server.\n' \
              f'`{node.stats.playing_players}` players are playing on server.\n\n' \
              f'Server Memory: `{used}/{total}` | `({free} free)`\n' \
              f'Server CPU: `{cpu}`\n\n' \
              f'Server Uptime: `{datetime.timedelta(milliseconds=node.stats.uptime)}`'
        await ctx.send(fmt)


def setup(bot): 
    bot.add_cog(Music(bot))
