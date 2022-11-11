import discord, abc

class Config(abc.ABC):
    TOKEN = ''
    SPOTIFY_CLIENT_ID = ''
    SPOTIFY_CLIENT_SECRET = ''

    COOKIES_FILE_PATH = 'cookies.txt'
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    BOT_NAME = 'SushiMusic'
    BOT_VERSION = '1.0.1'
    BOT_LOGO_URL = 'https://raw.githubusercontent.com/KamiSushii/SushiMusic/main/logo.png'
    EMBED_COLOR = discord.Colour.lighter_gray()