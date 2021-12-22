import datetime

import discord
from discord.ext.commands import command, Cog,Bot,dm_only,Context, is_owner
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)

class claim(Cog):
    def __init__(self, bot):
        self.bot:Bot = bot
        super().__init__()

    @command(name="문의")
    async def claim_dm(self,ctx:Context,*,value):
        if value == "" or value is None:
            return await ctx.reply("내용을 입력해주세요.")
        msg:discord.Message = ctx.message
        atch:discord.Attachment = msg.attachments
        channel = self.bot.get_channel(922310583175491635)
        em = discord.Embed(
            title=f"{ctx.author}님의 문의입니다.",
            description=value,
            colour=discord.Colour.random(),
            timestamp=datetime.datetime.now()
        )
        em.set_footer(text=str(ctx.author.id))
        if len(atch) == 1:
            if not atch[0].filename.endswith(".png") or not atch[0].filename.endswith(".jpeg") or not atch[
                0].filename.endswith(".gif") or not atch[0].filename.endswith(".jpg"):
                return await ctx.reply('이미지파일만 보내실수있습니다.\n지원형식: .png, .jpeg, .gif, .jpg')
            em.set_image(url=atch[0].url)
        elif len(atch) >=2:
            return await ctx.send('이미지는 최대 1개만 보내실수있습니다.')
        await channel.send(embed=em)
        await ctx.reply("✅ 성공적으로 전송했습니다. 문의에 대한 답변을 정상적으로 전달하기위해 DM차단을 하지마시기 바랍니다.")

    @command(name="문의답장")
    @is_owner()
    async def reply_claim(self,ctx,*,value):
        msg_id = ctx.message.reference.message_id
        await ctx.message.add_reaction('▶')
        user_id:int = (await ctx.channel.fetch_message(msg_id)).embeds[0].footer.text
        user = await self.bot.fetch_user(user_id)
        try:
            await user.send('> 관리자 >> ' + value)
            await ctx.message.add_reaction('✅')
        except Exception:
            await ctx.message.add_reaction('❗')



def setup(bot):
    bot.add_cog(claim(bot))