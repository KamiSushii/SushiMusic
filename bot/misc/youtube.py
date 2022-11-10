from abc import ABC
from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
from typing import Union
from pytube import Search, Playlist, YouTube
from aiohttp import ClientSession
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL

from bot.misc import Config, SongObject, thumbnail

class YoutubeWrapper(ABC):
    @staticmethod
    async def is_valid_url(url: str) -> bool:
        """Checks the YouTube video/playlist url for validity."""
        
        async with ClientSession() as session:
            checker_url = 'https://www.youtube.com/oembed?url=' + url
            async with session.get(checker_url) as resp:
                return resp.status == 200

    @staticmethod
    def get_audio_url(url: str) -> str:
        """Get audio url from YoutubeDL"""

        video_info = \
            YoutubeDL({
                'format': 'bestaudio/best',
                'ignoreerrors': True,
                'cookiefile': Config.COOKIES_FILE_PATH
            }).extract_info(url, False)

        if video_info is None:
            return None
        else:
            return video_info['url']

    @staticmethod
    async def search_list(query: str) -> Union[list[SongObject], None]:
        """Search 5 videos on youtube"""

        songs = []
        try:
            for result in Search(query).results[:5]:
                songs.append(SongObject('youtube_track',
                                        result.title, result.watch_url, thumbnail(result.video_id)))

            return songs
        except IndexError:
            return None

    @staticmethod
    async def search(query: str) -> Union[SongObject, None]:
        """Search video on youtube"""
        
        print(query)
        try:
            result = Search(query).results[0]
            return SongObject('youtube_track',
                              result.title, result.watch_url, thumbnail(result.video_id))
        except IndexError:
            print("error")
            return None  

    @staticmethod
    async def search_ytm(query: str) -> Union[SongObject, None]:
        """Searches for video on YouTube Music."""

        try:
            id = YTMusic().search(query=query, filter='songs', limit=1)[0]['videoId']
            result = Search(f"https://youtube.com/watch?v={id}").results[0]

            return SongObject('youtube_track',
                              result.title, result.watch_url, thumbnail(result.video_id))
        except IndexError:
            return None

    @classmethod
    async def search_playlist(cls, url: str) -> SongObject:
        """Extracts the data needed to play the first video of the playlist
        and saves the remaining video urls of the playlist."""

        def get_playlist_info() -> tuple:
            playlist = Playlist(url)
            playlist.video_urls.generate_all()
            return playlist.title, playlist.playlist_url, list(playlist.video_urls)

        playlist_name, playlist_url, track_urls =\
            await get_event_loop().run_in_executor(ThreadPoolExecutor(), get_playlist_info)

        try:
            playlist_thumbnail = (await cls.search(track_urls[0])).thumbnail
        except:
            playlist_thumbnail = 'https://i.ytimg.com/vi_webp/nonexist/maxresdefault.webp'

        return SongObject('youtube_playlist',
                          playlist_name, playlist_url, playlist_thumbnail, track_urls)