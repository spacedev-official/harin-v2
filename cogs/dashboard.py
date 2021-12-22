import discord
import aiosqlite
from discord.ext.commands import Cog,Bot,command
from py_cord_components import Interaction
from tools.dashboard_tool import DashBoard
class dashboard(Cog):
    def __init__(self,bot):
        self.bot:Bot = bot

    @Cog.listener(name='on_button_click')
    async def dashboard_control(self,interaction:Interaction):
        database = await aiosqlite.connect("db/db.sqlite")
        cur = await database.execute("SELECT * FROM dashboard WHERE guild = ?", (interaction.guild_id,))
        data = await cur.fetchone()
        if data != None:
            await interaction.respond(type=6)
            value = interaction.custom_id
            dash = DashBoard(bot=self.bot,interaction=interaction)
            await dash.dashboard_process(value)

    @command(name='대시보드')
    async def setup_dashboard(self,ctx):
        dash = DashBoard(bot=self.bot, ctx=ctx)
        await dash.dashboard_setup()

def setup(bot):
    bot.add_cog(dashboard(bot))