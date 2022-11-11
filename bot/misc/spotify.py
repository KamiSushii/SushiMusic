from async_spotify import SpotifyApiClient
from async_spotify.authentification.authorization_flows import ClientCredentialsFlow
from async_spotify.spotify_errors import SpotifyAPIError

from bot.misc import Config, SongObject, YoutubeWrapper, thumbnail

from abc import ABC
from typing import Union

class SpotifyWrapper(ABC):
    __spotify_client: Union[None, SpotifyApiClient] = None

    @classmethod
    async def init(cls) -> None:
        """Initializes the Spotify client."""
        cls.__spotify_client = SpotifyApiClient(authorization_flow=ClientCredentialsFlow(
            application_id=Config.SPOTIFY_CLIENT_ID, application_secret=Config.SPOTIFY_CLIENT_SECRET))
        await cls.__spotify_client.get_auth_token_with_client_credentials()
        await cls.__spotify_client.create_new_client()
        
    @classmethod
    async def close(cls) -> None:
        """Closes the Spotify client."""
        await cls.__spotify_client.close_client()
        cls.__spotify_client = None

    @staticmethod
    def __get_id_from_spotify_url(url: str) -> str:
        """Gets id from the specified Spotify url."""
        return list(filter(None, url.split('/')))[-1].split('?')[0]

    @classmethod
    async def __fetch_all_next_tracks(cls, info: dict) -> dict:
        """Fetches all next tracks from the specified Spotify album or playlist."""

        next_link = info['tracks']['next']
        while next_link:
            next_tracks = await cls.__spotify_client.next(next_link)
            info['tracks']['items'] += next_tracks['items']
            next_link = next_tracks['next']
        return info

    @classmethod
    async def track(cls, url: str) -> SongObject:
        """Extracts the data needed to play the Spotify track."""

        track_id = cls.__get_id_from_spotify_url(url)
        try:
            track_info = await cls.__spotify_client.track.get_one(track_id)
        except SpotifyAPIError:
            return SongObject('spotify_track', None, None, None)

        track_name = track_info['artists'][0]['name']
        for i in range(len(track_info['artists']) - 1):
            track_name += ', ' + track_info['artists'][i + 1]['name']
        track_name += ' - ' + track_info['name']

        try:
            track_thumbnail = track_info['album']['images'][0]['url']
        except:
            track_thumbnail = 'https://i.ytimg.com/vi_webp/nonexist/maxresdefault.webp'

        return SongObject('spotify_track',
                          track_name, track_info['external_urls']['spotify'], track_thumbnail)

    @classmethod
    async def album(cls, url: str) -> SongObject:
        """Extracts the data needed to play the first track of the Spotify album
        and saves the remaining track urls of the album."""
        album_id = cls.__get_id_from_spotify_url(url)
        try:
            album_info = await cls.__spotify_client.albums.get_one(album_id)
        except SpotifyAPIError:
            return SongObject('spotify_playlist', None, None, None)
        album_info = await cls.__fetch_all_next_tracks(album_info)

        track_urls = []
        for track in album_info['tracks']['items']:
            track_urls.append(track['external_urls']['spotify'])

        try:
            album_thumbnail = album_info['images'][0]['url']
        except:
            album_thumbnail = 'https://i.ytimg.com/vi_webp/nonexist/maxresdefault.webp'

        
        return SongObject('spotify_playlist',
                          album_info['name'], album_info['external_urls']['spotify'], album_thumbnail, track_urls)

    @classmethod
    async def playlist(cls, url: str) -> SongObject:
        """Extracts the data needed to play the first track of the Spotify playlist
        and saves the remaining track urls of the playlist."""
        playlist_id = cls.__get_id_from_spotify_url(url)

        try:
            playlist_info = await cls.__spotify_client.playlists.get_one(playlist_id)
        except SpotifyAPIError:
            return SongObject('spotify_playlist', None, None, None)
        playlist_info = await cls.__fetch_all_next_tracks(playlist_info)

        track_urls = []
        for track in playlist_info['tracks']['items']:
            if track['track']:
                track_urls.append(track['track']['external_urls']['spotify'])

        try:
            playlist_thumbnail = playlist_info['images'][0]['url']
        except:
            playlist_thumbnail = 'https://i.ytimg.com/vi_webp/nonexist/maxresdefault.webp'


        return SongObject('spotify_playlist',
                          playlist_info['name'], playlist_info['external_urls']['spotify'], playlist_thumbnail, track_urls)  
