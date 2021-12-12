import discord
import aiohttp
from discord.ext.commands import Cog,CommandNotFound,NotOwner,Context,CommandError,MissingPermissions,BotMissingPermissions
from tools.execption import PermError
from bot import MyBot

class core(Cog):
    def __init__(self,bot:MyBot):
        self.bot = bot
        super().__init__()


    @Cog.listener('on_command_error')
    async def listen_error(self,ctx:Context,error:CommandError):
        em = discord.Embed(title="⚠ 에러가 발생했어요. ⚠",colour=discord.Colour.red())
        if isinstance(error,CommandNotFound):
            return
        elif isinstance(error,PermError.NotEnoughItem):
            return
        elif isinstance(error,NotOwner):
            em.description = f"<a:cross:893675768880726017> {ctx.author.mention}님은 제 주인이 아니셔서 해당 명령어를 사용하실수없어요."
            return await ctx.reply(embed=em)
        elif isinstance(error,PermError.BlacklistedUser):
            em.description = f"<a:cross:893675768880726017> {ctx.author.mention}님은 블랙리스트에 등록되어있어 해제가 될때까지는 사용하실수없어요."
            return await ctx.reply(embed=em)
        elif isinstance(error,PermError.AlreadyRegisterUser):
            em.description = f"<a:cross:893675768880726017> {ctx.author.mention}님은 이미 가입되어있어요."
            return await ctx.reply(embed=em)
        elif isinstance(error,PermError.NotRegisterUser):
            em.description = f"<a:cross:893675768880726017> {ctx.author.mention}님은 가입되어있지않아요."
            return await ctx.reply(embed=em)
        elif isinstance(error,discord.Forbidden):
            em.description = "<a:cross:893675768880726017> 저에게 권한이 없어요."
            return await ctx.reply(embed=em)
        elif isinstance(error,MissingPermissions):
            em.description = f"<a:cross:893675768880726017> 해당 커맨드를 사용하실수없어요. 최소한 아래의 권한을 가지고있어야해요.\n< 필요권한 >\n\n{MissingPermissions.missing_permissions}"
            return await ctx.reply(embed=em)
        elif isinstance(error,BotMissingPermissions):
            em.description = f"<a:cross:893675768880726017> 저는 해당 커맨드를 수행할수없어요. 최소한 아래의 권한을 부여해주셔야해요.\n< 필요권한 >\n\n{BotMissingPermissions.missing_permissions}"
            return await ctx.reply(embed=em)
        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(url='https://www.toptal.com/developers/hastebin/documents',data=str(error.with_traceback())) as resp:
                    if resp.status == 200:
                        resp_json = await resp.json()
                        code_key = resp_json['key']
                        em.description = "<a:cross:893675768880726017> 알수없는 에러가 발생했어요. 해당에러는 개발자에게 전송되어 수정될 예정이에요."
                        await ctx.reply(embed=em)
                        em.description = f"```py\n{str(error.with_traceback())[:4096]}...\n```"
                        em.add_field(
                            name="전체 에러보기",
                            value=f"[링크](https://www.toptal.com/developers/hastebin/{code_key})"
                        )
                    else:
                        em.description = "<a:cross:893675768880726017> 알수없는 에러가 발생했어요. 해당에러는 개발자에게 전송되어 수정될 예정이에요."
                        await ctx.reply(embed=em)
                        em.description = f"```py\n{str(error.with_traceback())[:4096]}...\n```"
                    await self.bot.get_user(281566165699002379).send(embed=em)
                    await session.close()

def setup(bot):
    bot.add_cog(core(bot))

