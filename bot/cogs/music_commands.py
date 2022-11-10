from discord.ui import View, Select
from discord.ext.commands import Cog, Bot
from discord import VoiceClient, VoiceChannel, FFmpegPCMAudio, Interaction, Option, SelectOption, Embed,\
                    ClientException, slash_command, Member, VoiceState

from bot.misc import Config, GuildPlayData, LoopState, QueueItem,\
                     SpotifyWrapper, YoutubeWrapper, SongObject
                      
from typing import Union
import asyncio


class MusicCommandsCog(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.guild_playdata = {}

    @classmethod
    def __play_music(cls, vc: VoiceClient, song_obj: Union[None, SongObject]) -> None:
        """Plays music from the source url and then calls the __check_new_songs method."""

        if song_obj is None:
            cls.__check_new_songs(vc)
            return
            
        if vc.is_playing():
            return

        try:
            vc.play(FFmpegPCMAudio(
                source=YoutubeWrapper.get_audio_url(song_obj.url),
                before_options=Config.FFMPEG_OPTIONS['before_options'],
                options=Config.FFMPEG_OPTIONS['options']
            ), after=lambda _: cls.__check_new_songs(vc))

        except ClientException:
            return

    @classmethod
    def __check_new_songs(cls, vc: VoiceClient) -> None:
        """Plays the remaining songs if there is any and loops the track or queue."""

        play_data = GuildPlayData.get_play_data(vc.guild.id)
        if play_data is None:
            return

        if play_data.loop == LoopState.TRACK:  # track loop
            cls.__play_music(vc, play_data.queue[play_data.cur_song_pos])
            return

        try:  # trying to get the next song
            song_obj = play_data.queue[play_data.cur_song_pos+1]
            play_data.cur_song_pos += 1
        except IndexError:
            if play_data.playlists_being_added:
                play_data.waiting_for_next_song = True
                return

            if play_data.loop != LoopState.QUEUE:
                GuildPlayData.remove_play_data(vc.guild.id)
                return

            # queue loop
            play_data.cur_song_pos = 0
            song_obj = play_data.queue[0]

        cls.__play_music(vc, song_obj)

    @staticmethod
    async def __join_user_channel(interaction: Interaction) -> VoiceChannel:
        """Joins to the voice channel where the user is located."""

        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect()
        else:
            await interaction.guild.voice_client.move_to(channel)

        await interaction.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)  # self deaf
        return channel

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:
        """Deletes play data when the bot has disconnected from the voice channel."""

        if member.id == self.bot.application_id and after.channel is None\
                and GuildPlayData.get_play_data(member.guild.id) is not None:
            GuildPlayData.remove_play_data(member.guild.id)

    async def spotify_query(self, interaction: Interaction, query: str) -> SongObject:
        if 'track' in query:
            song_obj = await SpotifyWrapper.track(query)
            if song_obj.title is not None and song_obj.url is None:
                return

        elif 'album' in query:
            song_obj = await SpotifyWrapper.album(query)
            if song_obj.title is not None and song_obj.url is None:
                return

        elif 'playlist' in query:
            song_obj = await SpotifyWrapper.playlist(query)
            if song_obj.title is not None:
                if song_obj.url is None:
                    return

        return song_obj

    async def youtube_query(self, interaction: Interaction, query: str) -> SongObject:
        song_obj = None

        if 'youtube.com' in query or 'youtu.be' in query:
            if not await YoutubeWrapper.is_valid_url(query): return

            if 'list=' in query:
                song_obj = await YoutubeWrapper.search_playlist(query)
                if song_obj.url is None:
                    await interaction.channel.send('An error occurred while processing playlist.')

            else:
                song_obj = await YoutubeWrapper.search(query)
                if song_obj.url is None:
                    await interaction.channel.send('An error occurred while processing video.')
                    
        else:
            songs = await YoutubeWrapper.search_list(query)
            i, options = 0, []
            for s in songs:
                title = (s.title[:75] + '...') if len(s.title) > 75 else s.title
                options.append(SelectOption(label=f"{i+1}. {title}", value=str(i)))
                i = i + 1

            select = Select(placeholder="Choose Song", options=options)
            selection = await interaction.send(view=View(select))

            def check(msg: Interaction):
                if msg.user == interaction.user:
                    return selection == msg.message
                return False

            while True:
                try:
                    res = await self.bot.wait_for("interaction", check=check, timeout=30)
                    song_obj = songs[int(res.data['values'][0])-1]

                    await res.response.defer()
                    break
                
                except asyncio.TimeoutError:
                    await selection.delete()
                    await interaction.respond("Sorry, you didn't reply in time!", view=None)
                    break
            
            await selection.delete()

        return song_obj

    @slash_command(name='play', description='The bot joins to your voice channel and plays music from a known link or a search query.')
    async def play_command(self, interaction: Interaction, query: str = Option(description='Known link or a search query', required=True)) -> None:
        await interaction.response.defer()
        
        if interaction.user.voice is None:
            await interaction.respond(f'{interaction.user.mention}, you have to be connected to a voice channel.')
            return

        channel = await self.__join_user_channel(interaction)
        vc = interaction.guild.voice_client

        # get song object from query
        if 'open.spotify.com' not in query:
            song_obj = await self.youtube_query(interaction, query)
        else:
            song_obj = await self.spotify_query(interaction, query)

        if song_obj is None: return

        play_data = GuildPlayData.get_play_data(interaction.guild_id)
        if play_data is None:
            play_data = GuildPlayData.create_play_data(interaction.guild_id)
            
        # adding song object to queue
        if 'playlist' not in song_obj.type:
            embed=Embed(
                title='Song successfully added.',
                description=f'[{song_obj.title}]({song_obj.url})',
                color=Config.EMBED_COLOR).set_thumbnail(url=song_obj.thumbnail)

            await interaction.respond(embed=embed)

            play_data.queue.append(QueueItem(song_obj.title, song_obj.url, song_obj.thumbnail))
            self.__play_music(vc, song_obj)

        else:
            embed=Embed(
                title='Adding playlist to queue.',
                description=f'[{song_obj.title}]({song_obj.url})',
                color=Config.EMBED_COLOR).set_thumbnail(url=song_obj.thumbnail)

            await interaction.respond(embed=embed)

            # adding the remaining videos from the YouTube playlist to queue
            if song_obj.type == 'youtube_playlist':
                for video_url in song_obj.track_urls:
                    print(video_url)
                    video = await YoutubeWrapper.search(video_url)

                    play_data = GuildPlayData.get_play_data(interaction.guild_id)
                    if play_data is None:
                        return

                    play_data.queue.append(QueueItem(video.title, video.url, video.thumbnail))
                    self.__play_music(vc, video)

                await interaction.channel.send('✅ YouTube playlist was fully added to the queue.')

            # adding the remaining videos from the Spotify album/playlist to queue
            elif song_obj.type == 'spotify_playlist':
                for track_url in song_obj.track_urls:
                    track = await SpotifyWrapper.track(track_url)
                    if track.url is None:
                        await interaction.channel.send(
                            'An error occurred while processing one of the Spotify album/playlist tracks or'
                            ' this track wasn\'t found.')
                        continue

                    play_data = GuildPlayData.get_play_data(interaction.guild_id)
                    if play_data is None:
                        return

                    play_data.queue.append(QueueItem(track.title, track.url, track.thumbnail))
                    self.__play_music(vc, track)

                await interaction.channel.send('✅ Spotify album/playlist was fully added to the queue.')

    @slash_command(name='lofi', description='Joins to the channel and plays lofi hip hop.', dm_permission=False)
    async def lofi_command(self, interaction: Interaction) -> None:
        # just calling play_command method with 'lofi hip hop radio' query
        await self.play_command(interaction, 'https://www.youtube.com/watch?v=80UgmX_sa88')