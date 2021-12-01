import os
import config
import discord
from discord.ext import commands
from tools.autocogs import AutoCogs
from dotenv import load_dotenv
from py_cord_components import PycordComponents
load_dotenv(verbose=True)


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_command("help")
        AutoCogs(self)
    async def on_ready(self):
        """Called upon the READY event"""
        #await self.change_presence(status=discord.Status.online, activity=discord.Activity(name="하린아 도움 | 서버: {}".format(len(self.guilds)),type=discord.ActivityType.playing))
        await self.change_presence(status=discord.Status.online,
                                   activity=discord.Activity(name="하린봇 V2 테스트",
                                                             type=discord.ActivityType.playing))
        print("Bot is ready.")

    async def is_owner(self, user):
        if user.id in config.OWNER:
            return True



INTENTS = discord.Intents.all()
my_bot = MyBot(command_prefix=commands.when_mentioned_or("."), intents=INTENTS)
PycordComponents(my_bot)
if __name__ == "__main__":
    my_bot.run(os.getenv('TOKEN'))