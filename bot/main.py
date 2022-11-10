from discord import Intents, Activity, ActivityType
from discord.ext.commands import Bot

from asyncio import run
from bot.misc import Config, SpotifyWrapper

class SushiMusic(Bot):
    def __init__(self):
        intents = Intents.all()
        super().__init__(intents=intents)

    def run(self):
        print("[*] Starting bot")
        self.load_extension('bot.cogs')

        super().run(Config.TOKEN, reconnect=True)

        # closing the SpotifyWrapper when the bot is stopped
        run(SpotifyWrapper.close())

    async def on_ready(self):
        self.client_id = (await self.application_info()).id
        try:
            await self.change_presence(activity=Activity(type=ActivityType.listening ,name='/commands | /info'))
        except: pass
        await SpotifyWrapper.init()
        
        print(f"[*] Connected to Discord (latency: {self.latency*1000:,.0f} ms).")
        print(f"[*] Discord bot {self.user.name} ready.\n")
        print(f'🎵 {Config.BOT_NAME} v{Config.BOT_VERSION} ready.')