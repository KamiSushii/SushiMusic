from discord import ApplicationContext, slash_command, Interaction, Embed, ButtonStyle, Message, VoiceClient
from discord.ui import View, Button, button
from discord.ext.commands import Cog, Bot
from discord.ext.pages import Paginator, PaginatorButton
from random import shuffle

from bot.misc import Config, GuildPlayData, LoopState, SongObject


class ControlCommandsCog(Cog):
    
    def __init__(self, bot: Bot):
        self.bot = bot

    async def is_valid(self, ctx: ApplicationContext) -> bool:
        if ctx.guild.voice_client is None:
            await ctx.respond('I am not playing any songs for you.')
            return False

        if ctx.user.voice is None:
            await ctx.respond(f'{ctx.user.mention}, You have to be connected to a voice channel.')
            return False

        if ctx.user.voice.channel.id != ctx.guild.voice_client.channel.id:
            await ctx.respond('You are in the wrong channel.')
            return False

        return True

    @slash_command(name='skip', description='Skips current song.', dm_permission=False)
    async def skip_command(self, ctx: ApplicationContext) -> None:
        if ctx != ApplicationContext:
            ctx = await self.bot.get_application_context(ctx)

        if not await self.is_valid(ctx):
            return

        ctx.guild.voice_client.stop()
        await ctx.respond('✅ Successfully skipped.')

    @slash_command(name='pause', description='Pauses current song.', dm_permission=False)
    async def pause_command(self, ctx: ApplicationContext) -> None:
        if ctx != ApplicationContext:
            ctx = await self.bot.get_application_context(ctx)

        if not await self.is_valid(ctx):
            return
        
        if ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()

            await ctx.respond('▶️ Successfully resumed.')

            return

        ctx.guild.voice_client.pause()
        await ctx.respond('⏸️ Successfully paused.')

    @slash_command(name='resume', description='Resumes current song if it is paused.', dm_permission=False)
    async def resume_command(self, ctx: ApplicationContext) -> None:
        if ctx != ApplicationContext:
            ctx = await self.bot.get_application_context(ctx)

        if not await self.is_valid(ctx):
            return

        ctx.guild.voice_client.resume()
        await ctx.respond('▶️ Successfully resumed.')

    @slash_command(name='loop', description='Enables/Disables Queue/Track loop.', dm_permission=False)
    async def loop_command(self, ctx: ApplicationContext) -> None:
        if ctx != ApplicationContext:
            ctx = await self.bot.get_application_context(ctx)

        play_data = GuildPlayData.get_play_data(ctx.guild_id)

        if play_data is None:
            await ctx.respond('I am not playing any songs for you.')
            return

        if not await self.is_valid(ctx):
            return

        if play_data.loop == LoopState.NONE:
            play_data.loop = LoopState.QUEUE
            await ctx.respond('🔁 Queue loop enabled!')
        elif play_data.loop == LoopState.QUEUE:
            play_data.loop = LoopState.TRACK
            await ctx.respond('🔁 Current track loop enabled!')
        else:
            play_data.loop = LoopState.NONE
            await ctx.respond('❎ Loop disabled!')

    @slash_command(name='shuffle', description='Shuffles next songs in the queue.', dm_permission=False)
    async def shuffle_command(self, ctx: ApplicationContext) -> None:
        if ctx != ApplicationContext:
            ctx = await self.bot.get_application_context(ctx)

        if not await self.is_valid(ctx):
            return

        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue):
            await ctx.respond('Your queue is empty!')
            return

        # getting the next and previous songs from the queue
        next_songs = play_data.queue[play_data.cur_song_pos+1:]
        previous_songs = play_data.queue[:play_data.cur_song_pos+1]

        if len(next_songs) <= 1:
            await ctx.respond('Not enough songs to shuffle.')
            return

        # unique shuffling next songs
        shuffled_next_songs = next_songs.copy()
        while shuffled_next_songs == next_songs:
            shuffle(shuffled_next_songs)

        play_data.queue = previous_songs + shuffled_next_songs  # replacing the queue
        await ctx.respond('✅ Next songs were successfully shuffled.')


    @slash_command(name='leave', description='Leaves the voice channel.', dm_permission=False)
    async def leave_command(self, ctx: ApplicationContext) -> None:
        if ctx != ApplicationContext:
            ctx = await self.bot.get_application_context(ctx)

        if not await self.is_valid(ctx):
            return

        await ctx.guild.voice_client.disconnect()
        await ctx.respond('✅ Successfully disconnected.')


    @slash_command(name='queue', description='Shows current queue of songs.', dm_permission=False)
    async def queue_command(self, ctx: ApplicationContext) -> None:
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        if play_data is None or not len(play_data.queue):
            await ctx.respond(embed=Embed(
                title='Current Queue',
                description='Your current queue is empty!',
                color=Config.EMBED_COLOR))
            return

        queue = play_data.queue[play_data.cur_song_pos:]

        # splitting the queue into arrays of 15 songs
        current_song = queue[0]
        upcoming_queue = queue[1:]

        arrays = []
        while len(upcoming_queue) > 20:
            piece = upcoming_queue[:20]
            arrays.append(piece)
            upcoming_queue = upcoming_queue[20:]
        arrays.append(upcoming_queue)
        upcoming_queue = arrays

        additional_info = f'🎶 Total tracks: {len(play_data.queue)}\n' \
                          f'🔁 Queue loop: {"enabled" if play_data.loop == LoopState.QUEUE else "disabled"} | ' \
                          f'🔁 Current track loop: {"enabled" if play_data.loop == LoopState.TRACK else "disabled"}'

        # filling each page with song titles, their positions in queue, etc.
        pos = 1
        pages = []
        for arr in upcoming_queue:
            upcoming_list = '**Upcoming:**\n'
            for queue_item in arr:
                upcoming_list += f'`{pos}.` [{queue_item.title[:75] + "..." if len(queue_item.title) > 75 else queue_item.title}]({queue_item.url})\n'
                pos += 1

            embed=Embed(
                title='Current Queue',
                description=f'**Now playing:**\n'
                            f'[{current_song.title[:75] + "..." if len(current_song.title) > 75 else current_song.title}]'
                            f'({current_song.url})\n\n'
                            f'{upcoming_list}',
                color=Config.EMBED_COLOR
            )
            embed.set_footer(text=additional_info)
            embed.set_thumbnail(url=current_song.thumbnail)
            pages.append(embed)


        page_buttons = [
            PaginatorButton("first", emoji="⏪", style=ButtonStyle.primary),
            PaginatorButton("prev", emoji="◀️", style=ButtonStyle.primary),
            PaginatorButton("page_indicator", style=ButtonStyle.gray, disabled=True),
            PaginatorButton("next", emoji="▶️", style=ButtonStyle.primary),
            PaginatorButton("last", emoji="⏩", style=ButtonStyle.primary),
        ]
        paginator = Paginator(
            pages=pages,
            show_disabled=True,
            show_indicator=True,
            use_default_buttons=False,
            custom_buttons=page_buttons,
        )
        await paginator.respond(ctx.interaction)


    @slash_command(name='now-playing', description='Shows what track is playing now.', dm_permission=False)
    async def now_playing_command(self, ctx: ApplicationContext) -> None:
        await self.control_command(ctx)


    @slash_command(name='control', description='Shows control board', dm_permission=False)
    async def control_command(self, ctx: ApplicationContext):
        play_data = GuildPlayData.get_play_data(ctx.guild_id)
        ctx.send_response

        if not await self.is_valid(ctx):
            return

        if play_data is None:
            await ctx.respond('Nothing is playing right now.')
            return

        try:
            current_song: SongObject = play_data.queue[play_data.cur_song_pos]
        except IndexError:
            await ctx.respond('An unexpected error has occurred. Try using the command again.')
            return

        embed = Embed(
            title="Currently playing:",
            description=f"[{current_song.title}]({current_song.url})",
            color=Config.EMBED_COLOR
        ).set_thumbnail(url=current_song.thumbnail)

        pause = Button(label='', style=ButtonStyle.primary, emoji="<:pause:1014645688417660999>")
        skip = Button(label='', style=ButtonStyle.primary, emoji="<:skip:1014645693102694470>")
        stop = Button(label='', style=ButtonStyle.red,emoji="<:stop:1014645696718184478>")
        loop = Button(label='', style=ButtonStyle.primary, emoji="<:loop:1014645681329295411>")
        shuffle = Button(label='', style=ButtonStyle.primary, emoji="<:shuffle:1014645684764422224>")

        pause.callback = self.pause_command
        skip.callback = self.skip_command
        stop.callback = self.leave_command
        loop.callback = self.loop_command
        shuffle.callback = self.shuffle_command

        view = View(pause, skip, stop, loop, shuffle, timeout=30, disable_on_timeout=True)
        await ctx.respond(embed=embed, view=view)
