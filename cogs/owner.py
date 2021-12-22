import aiosqlite
import discord
from discord.ext.commands import command,Cog,is_owner,group,Context
from bot import MyBot
class owner(Cog):
    "관리자 전용 명령어"
    def __init__(self,bot:MyBot):
        self.bot = bot

    @group(name="블랙", invoke_without_command=True)
    async def blacklist(self, ctx: Context):
        database = await aiosqlite.connect("db/db.sqlite")
        cur = await database.execute("SELECT * FROM blacklist WHERE user = ?", (ctx.author.id,))
        if await cur.fetchone() == None:
            return await ctx.reply(f"{ctx.author}님은 블랙리스트에 등록되어있지 않아요.")
        data = await cur.fetchone()
        await ctx.reply(f"블랙사유: {data[1]}")

    @blacklist.command(name="추가")
    @is_owner()
    async def blacklist_add(self, ctx: Context, user_id: int, *, reason):
        user = await self.bot.fetch_user(user_id)
        database = await aiosqlite.connect("db/db.sqlite")
        cur = await database.execute("SELECT * FROM blacklist WHERE user = ?", (user_id,))
        datas = await cur.fetchone()
        if datas != None:
            return await ctx.reply(f"{user}님은 블랙리스트에 등록되어있어요.\n사유: {datas[1]}")
        await database.execute("INSERT INTO blacklist(user,reason) VALUES (?,?)", (user_id, reason))
        await database.commit()
        try:
            await user.send(f"__관리자로부터 블랙등록됨.__\n\n"
                            f"관리자가 아래의 사유로 블랙하셨어요.\n\n"
                            f"사유: \n{reason}")
        except:
            pass
        await ctx.reply("등록완료!")

    @blacklist.command(name="삭제")
    @is_owner()
    async def blacklist_del(self, ctx: Context, user_id: int):
        user = await self.bot.fetch_user(user_id)
        database = await aiosqlite.connect("db/db.sqlite")
        cur = await database.execute("SELECT * FROM blacklist WHERE user = ?", (user_id,))
        datas = await cur.fetchone()
        if datas == None:
            return await ctx.reply(f"{user}님은 블랙리스트에 등록되어있지않아요.")
        await database.execute("DELETE FROM blacklist WHERE user = ?", (user_id,))
        await database.commit()
        try:
            await user.send(f"__관리자로부터 블랙해제됨.__\n\n"
                            f"관리자가 블랙해제하셨어요.")
        except:
            pass
        await ctx.reply("해제완료!")

    @command(name="공지")
    @is_owner()
    async def send_notice(self,ctx,*,value):
        em = discord.Embed(
            title="하린 봇 공지사항!",
            description=value,
            colour=discord.Colour.random()
        )
        em.set_thumbnail(url=self.bot.user.avatar_url)
        em.set_image(
            url="https://media.discordapp.net/attachments/889514827905630290/896359450544308244/37cae031dc5a6c40.png")
        em.set_footer(text="특정 채널에 받고싶다면 대시보드 채널에서 설정하세요! 권한 확인 필수!")
        msg = await ctx.reply("발송중...")
        guilds = self.bot.guilds
        ok = []
        success = 0
        failed = 0
        for guild in guilds:
            channels = guild.text_channels
            for channel in channels:
                if guild.id in [653083797763522580, 786470326732587008]:
                    break
                if (
                        channel.topic is not None
                        and str(channel.topic).find("-HOnNt") != -1
                ):
                    ok.append(channel.id)
                    break
        for i in ok:
            channel = self.bot.get_channel(i)
            try:
                await channel.send(embed=em)
                success += 1
            except discord.Forbidden:
                failed += 1
        await msg.edit("발송완료!\n성공: `{ok}`\n실패: `{no}`".format(ok=success, no=failed))



def setup(bot):
    bot.add_cog(owner(bot))