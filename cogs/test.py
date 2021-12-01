import discord
from discord.ext.commands import command, Cog
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)

class ExampleCog(Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.cogs_name = {
            "temporary":"개인채널",
            "music":"뮤직"
        }

    @command(name="도움",aliases=["도움말","help"])
    async def help(self,ctx):
        await ctx.reply("~msetup\n뮤직기능을 사용하기위한 명령어입니다.\n\n~tsetup\n개인채널을 사용하기위한 명령어입니다.")


def setup(bot):
    bot.add_cog(ExampleCog(bot))