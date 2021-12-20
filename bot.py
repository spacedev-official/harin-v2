import asyncio
import os
import sys

import config
import discord
from discord.ext import commands
from pretty_help import PrettyHelp, PrettyMenu, DefaultMenu
from tools.autocogs import AutoCogs
from dotenv import load_dotenv
from py_cord_components import PycordComponents
from cogs.tasks import twloop, ytloop
load_dotenv(verbose=True)


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.remove_command("help")
        AutoCogs(self)
    async def on_ready(self):
        """Called upon the READY event"""
        PycordComponents(self)
        twloop.twloops(self).twloop_start()
        print('Twitch loop start!')
        ytloop.ytloops(self).ytloop_start()
        print('Youtube loop start!')
        #await self.change_presence(status=discord.Status.online, activity=discord.Activity(name="하린아 도움 | 서버: {}".format(len(self.guilds)),type=discord.ActivityType.playing))
        await self.change_presence(status=discord.Status.online,
                                   activity=discord.Activity(name="하린봇 V2 테스트",
                                                             type=discord.ActivityType.playing))
        print("Bot is ready.")

    async def is_owner(self, user):
        if user.id in config.OWNER:
            return True


menu = DefaultMenu(page_left="🎄", page_right="❄", remove="☃", active_time=60)

# Custom ending note
ending_note = "'{help.clean_prefix}{help.invoked_with} 카테고리명'으로 더 자세하게 보실수있어요."

INTENTS = discord.Intents.all()
my_bot = MyBot(command_prefix=commands.when_mentioned_or("."), intents=INTENTS,help_command=PrettyHelp(menu=menu,ending_note=ending_note))

# @my_bot.check
# async def global_check(ctx):
#     print(ctx.author)
#     return True

async def shutdown():
    await my_bot.close()
    sys.exit(0)

try:
    my_bot.run(os.getenv('TOKEN'))
except KeyboardInterrupt:
    asyncio.get_event_loop().run_until_complete(shutdown())