from .basic_commands import BasicCommandsCog
from .music_commands import MusicCommandsCog
from .control_commands import ControlCommandsCog

def setup(bot):
    bot.add_cog(BasicCommandsCog(bot))
    bot.add_cog(MusicCommandsCog(bot))
    bot.add_cog(ControlCommandsCog(bot))