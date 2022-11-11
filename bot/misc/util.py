from dataclasses import dataclass
from enum import Enum
from typing import Union, List, Dict

def thumbnail(id):
    return f'https://i.ytimg.com/vi_webp/{id}/maxresdefault.webp'

@dataclass
class SongObject:
    """Stores the data needed to play a song or playlist."""
    type: str
    title: Union[None, str]
    url: Union[None, str]
    thumbnail: Union[None, str] = None
    track_urls: Union[None, any] = None


class LoopState(Enum):
    NONE = 0
    QUEUE = 1
    TRACK = 2


class _PlayData:
    """Stores data for playing songs (queue, current song position, loop state, etc.)"""

    def __init__(self):
        self.queue = []
        self.cur_song_pos = 0
        self.loop = LoopState.NONE
        self.playlists_being_added = 0
        self.waiting_for_next_song = False


class GuildPlayData:
    """Stores _PlayData for each guild."""

    __guild_play_data: Dict[int, _PlayData] = {}

    @classmethod
    def create_play_data(cls, guild_id: int) -> _PlayData:
        """Creates new empty guild play data."""
        cls.__guild_play_data[guild_id] = _PlayData()
        return cls.__guild_play_data[guild_id]

    @classmethod
    def get_play_data(cls, guild_id: int) -> Union[None, _PlayData]:
        """Gets guild play data."""
        if guild_id not in cls.__guild_play_data:
            return None
        return cls.__guild_play_data[guild_id]

    @classmethod
    def remove_play_data(cls, guild_id: int) -> None:
        """Removes guild play data."""
        if guild_id in cls.__guild_play_data:
            del cls.__guild_play_data[guild_id]