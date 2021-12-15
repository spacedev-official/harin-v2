import asyncio
import random
import traceback
import aiosqlite
import discord
from discord.ext.commands import Cog,command
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)
from bot import MyBot
from tools.database_tool import temporary_caching, dump_temporary_caching, DataBaseTool


class temporary(Cog):
    """
    개인채널 관련 소스
    """
    def __init__(self, bot:MyBot):
        self.bot = bot
        self.temp = temporary_caching()
        #self.temp_text_channel = {}
        super().__init__()

    async def send_temporary_dafault_chat(self,member:discord.Member,channel:discord.TextChannel):
        em = discord.Embed(
            title="개인채널 사용법!",
            description="개인채널 사용법에대해 알려드려요."
        )
        em.add_field(
            name="<:blurple_invite:914773712895615016>",
            value="특정유저에게 채널 접속권한을 부여해요."
        )
        em.add_field(
            name="🚫",
            value="특정유저에게 부여된 접속권한을 빼앗고 추방해요."
        )
        em.add_field(
            name="👑",
            value="특정유저에게 관리자 권한을 부여해요."
        )
        em.add_field(
            name="✏",
            value="만들어진 음성 채널의 이름을 수정해요."
        )
        em.add_field(
            name="👥",
            value="접속가능인원을 수정해요. 최대 50명까지 가능해요."
        )
        em.add_field(
            name="📥",
            value="채널 초대 텍스트를 발급해요."
        )
        await channel.send(content=f"{member.mention}",
                           embed=em,
                           components=[
                               [
                                   Button(
                                        emoji=self.bot.get_emoji(914773712895615016),
                                        custom_id="temporary_addmember"
                                    ),
                                   Button(
                                       emoji="🚫",
                                       custom_id="temporary_kick"
                                   ),
                                   Button(
                                       emoji="👑",
                                       custom_id="temporary_addcoowner"
                                   ),
                                   Button(
                                       emoji="✏",
                                       custom_id="temporary_rename"
                                   ),
                                   Button(
                                       emoji="👥",
                                       custom_id="temporary_editlimit"
                                   )
                               ],
                               [
                                   Button(
                                       emoji="📥",
                                       custom_id="temporary_code"
                                   )
                               ]
                           ]
                           )

    async def create_temporary_channel(self,member:discord.Member):
        #self.temp = temporary_caching()
        db = await aiosqlite.connect("db/db.db")
        conn = await db.execute("SELECT * FROM temporary WHERE guild = ?", (member.guild.id,))
        resp = await conn.fetchone()
        category: discord.CategoryChannel = self.bot.get_channel(resp[2])
        overwrites = {
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True)
        }
        voice_channel = await category.create_voice_channel(
            name=f"{member.display_name}'s private  voice channel",
            overwrites=overwrites
        )
        await member.move_to(voice_channel)
        text_channel = await category.create_text_channel(
            name=f"{member.display_name}'s private text channel ",
            overwrites=overwrites
        )
        await voice_channel.set_permissions(member.guild.default_role, connect=False)
        await text_channel.set_permissions(member.guild.default_role, read_messages=False, send_messages=False)
        #self.temp_text_channel[text_channel.id] = [member.id]
        data_dict = {}
        data = data_dict[str(member.guild.id)] = {}
        data[str(voice_channel.id)] = {
            "owner":member.id,
            "co_owners":[member.id],
            "members":[member.id],
            "voice": voice_channel.id,
            "text": text_channel.id
        }
        dump_temporary_caching(data_dict)
        await self.send_temporary_dafault_chat(member,text_channel)

    async def delete_temporary_channel(self,member:discord.Member,voice:discord.VoiceState):
        try:
            #self.temp = temporary_caching()
            cache = temporary_caching()
            temp = cache[str(member.guild.id)][str(voice.channel.id)]
            voice_channel = self.bot.get_channel(temp['voice'])
            text_channel = self.bot.get_channel(temp['text'])
            await voice_channel.delete()
            await text_channel.delete()
            del cache[str(member.guild.id)][str(voice.channel.id)]
            dump_temporary_caching(cache)
        except:
            print(traceback.format_exc())


    async def temporary_addmember(self,interaction:Interaction):
        await interaction.respond(type=6)
        channel = interaction.channel
        bot_msg = await channel.send(content="초대하고자 하는 멤버의 ID만 **30초이내**에 입력해주세요.", delete_after=30)
        try:
            msg = await self.bot.wait_for('message', check=lambda x: x.author.id == interaction.user.id, timeout=30)
        except asyncio.TimeoutError:
            await channel.send(content="30초가 지나 취소되었어요. 다시 요청해주세요.", delete_after=5)
            return
        #self.temp = temporary_caching()
        member_id = int(msg.content)
        member = self.bot.get_guild(interaction.guild_id).get_member(member_id)
        text_channel = self.bot.get_channel(interaction.channel_id)
        voice_channel = interaction.user.voice.channel
        cache = temporary_caching()
        temp = cache[str(member.guild.id)][str(voice_channel.id)]
        if member_id in temp['members']:
            return await channel.send(content=f"{member.mention}님은 이미 등록되어있어요.",delete_after=5)
        (temp['members']).append(member_id)
        await text_channel.set_permissions(member, read_messages=True, send_messages=True)
        await voice_channel.set_permissions(member, connect=True)
        await bot_msg.delete()
        await msg.delete()
        dump_temporary_caching(cache)
        await channel.send(content=f"✅ 성공적으로 {self.bot.get_user(member_id).mention}님을 추가했어요.", delete_after=5)


    async def temporary_kick(self,interaction:Interaction,voice_channel):
        await interaction.respond(type=6)
        channel = interaction.channel
        bot_msg = await channel.send(content="킥하고자 하는 멤버의 ID만 **30초이내**에 입력해주세요.", delete_after=30)
        try:
            msg = await self.bot.wait_for('message', check=lambda x: x.author.id == interaction.user.id, timeout=30)
        except asyncio.TimeoutError:
            await channel.send(content="30초가 지나 취소되었어요. 다시 요청해주세요.", delete_after=5)
            return
        #self.temp = temporary_caching()
        member_id = int(msg.content)
        member: discord.Member = self.bot.get_guild(interaction.guild_id).get_member(member_id)
        text_channel = self.bot.get_channel(interaction.channel_id)
        # voice_channel = interaction.user.voice.channel
        cache = temporary_caching()
        temp = cache[str(member.guild.id)][str(voice_channel.id)]
        if member_id not in temp['members']:
            return await channel.send(content=f"{member.display_name}님은 등록되어있지 않아요!", delete_after=5)
        if member_id == temp['owner']:
            return await channel.send(content="자기자신을 킥할수없어요.", delete_after=5)
        temp['members'].remove(member_id)
        try:
            temp['co_owners'].remove(member_id)
        except:
            pass
        await text_channel.set_permissions(member, read_messages=False, send_messages=False)
        await voice_channel.set_permissions(member, connect=False)
        try:
            await member.move_to(None)
        except:
            pass
        await bot_msg.delete()
        await msg.delete()
        dump_temporary_caching(cache)
        await channel.send(content=f"✅ 성공적으로 {self.bot.get_user(member_id).mention}님을 추방 또는 권한을 빼앗았어요.", delete_after=5)


    async def temporary_addcoowner(self,interaction:Interaction,voice_channel):
        await interaction.respond(type=6)
        channel = interaction.channel
        bot_msg = await channel.send(content="관리자로 등록하고자 하는 멤버의 ID만 **30초이내**에 입력해주세요.", delete_after=30)
        try:
            msg = await self.bot.wait_for('message', check=lambda x: x.author.id == interaction.user.id, timeout=30)
        except asyncio.TimeoutError:
            await channel.send(content="30초가 지나 취소되었어요. 다시 요청해주세요.", delete_after=5)
            return
        #self.temp = temporary_caching()
        member_id = int(msg.content)
        cache = temporary_caching()
        temp = cache[str(interaction.guild_id)][str(voice_channel.id)]
        member: discord.Member = self.bot.get_guild(interaction.guild_id).get_member(member_id)
        if member_id in temp['co_owners']:
            return await channel.send(content=f"{member.mention}님은 이미 관리자로 등록되어있어요.", delete_after=5)
        if member_id == temp['owner']:
            return await channel.send(content="자기자신을 추가할수없어요.",delete_after=5)
        (temp['co_owners']).append(member_id)
        await bot_msg.delete()
        await msg.delete()
        dump_temporary_caching(cache)
        await channel.send(content=f"✅ 성공적으로 {member.mention}님을 관리자로 등록했어요.", delete_after=5)

    async def temporary_rename(self,interaction:Interaction,voice_channel):
        await interaction.respond(type=6)
        channel = interaction.channel
        bot_msg = await channel.send(content="채널명을 변경할 글자만 **30초이내**에 입력해주세요.", delete_after=30)
        try:
            msg = await self.bot.wait_for('message', check=lambda x: x.author.id == interaction.user.id, timeout=30)
        except asyncio.TimeoutError:
            await channel.send(content="30초가 지나 취소되었어요. 다시 요청해주세요.", delete_after=5)
            return
        #self.temp = temporary_caching()
        name = str(msg.content)
        try:
            await voice_channel.edit(name=name)
        except:
            await bot_msg.delete()
            await msg.delete()
            await channel.send(content="지원하지않는 글자가 포함되어있는것같아요. 다시 시도해주세요.", delete_after=5)
            return
        await bot_msg.delete()
        await msg.delete()
        await channel.send(content=f"✅ 성공적으로 `{name}`으로 변경했어요.", delete_after=5)


    async def temporary_editlimit(self,interaction:Interaction,voice_channel):
        await interaction.respond(type=6)
        channel = interaction.channel
        bot_msg = await channel.send(content="음성채널의 인원수제한을 변경할 인원수의 숫자만 **30초이내**에 입력해주세요.", delete_after=30)
        try:
            msg = await self.bot.wait_for('message', check=lambda x: x.author.id == interaction.user.id, timeout=30)
        except asyncio.TimeoutError:
            await channel.send(content="30초가 지나 취소되었어요. 다시 요청해주세요.", delete_after=5)
            return
        #self.temp = temporary_caching()
        limit = msg.content
        if int(limit) >= 51:
            return await channel.send(content="앗! 인원제한은 50명까지만 가능해요! 다시 설정해주세요!")
        await voice_channel.edit(user_limit=limit)
        await bot_msg.delete()
        await msg.delete()
        await channel.send(content=f"✅ 성공적으로 `{limit}`으로 변경했어요.", delete_after=5)

    @command(name="tsetup")
    async def tsetup(self,ctx):
        db = await aiosqlite.connect("db/db.db")
        check_ = await DataBaseTool(db).check_db_temporary(guild=ctx.guild)
        if not check_:
            return await ctx.reply("❎ 이미 설정되어있는것같아요!")
        text_channel = await ctx.guild.create_text_channel(name="❓개인채널 안내")
        voice_channel = await ctx.guild.create_voice_channel(name="➕ 개인채널 생성")
        category = await ctx.guild.create_category(name="개인채널 리스트")
        em = discord.Embed(
            title="개인채널에 대한 안내",
            description="개인채널에 대해서 안내해드릴게요.",
            colour=discord.Colour.random()
        )
        em.add_field(
            name="1️⃣ 개인채널이란?",
            value="개인채널 생성용 음성채팅에 접속하면 자동으로 자신만의 채널이 생성되어요.\n그러나 자신만의 음성채널에서 나가면 채널이 사라지거나 주인권한이 같이 접속해있는 유저에게 위임되어요."
        )
        em.add_field(
            name="2️⃣ 개인채널 사용법",
            value="아래에 있는 설명을 참고해주세요! @.@\n참! 그리고 모든 조작은 채널생성시에 따로 마련된 버튼으로 조작이 가능하답니다!"
        )
        em.add_field(
            name="<:blurple_invite:914773712895615016>",
            value="특정유저에게 채널 접속권한을 부여해요.\n그러나 서버관리자는 마음대로 들어올수있고 채널을 볼수있어요.",
            inline=False
        )
        em.add_field(
            name="🚫",
            value="특정유저에게 부여된 접속권한을 빼앗고 추방해요."
        )
        em.add_field(
            name="👑",
            value="특정유저에게 관리자 권한을 부여해요."
        )
        em.add_field(
            name="✏",
            value="만들어진 음성 채널의 이름을 수정해요."
        )
        em.add_field(
            name="👥",
            value="접속가능인원을 수정해요. 최대 50명까지 가능해요."
        )
        em.add_field(
            name="📥",
            value="채널 초대 텍스트를 발급해요."
        )
        await text_channel.send(embed=em)
        await DataBaseTool(db).add_temporary_data(guild=ctx.guild,voice_channel=voice_channel,category_channel=category)
        await ctx.reply("✅ 성공적으로 설정되었어요!\n생성된 채널들의 이름과 위치,권한은 마음껏 커스터마이징이 가능하지만 임의로 삭제하시면 오류가 발생할수있어요.")

    @Cog.listener('on_voice_state_update')
    async def temporary_event(self,member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if before.channel is None and after.channel is not None and not member.bot:
            db = await aiosqlite.connect("db/db.db")
            conn = await db.execute("SELECT * FROM temporary WHERE guild = ?",(member.guild.id,))
            resp = await conn.fetchone()
            if resp is not None and after.channel.id == resp[1]:
                await self.create_temporary_channel(member)
        elif not member.bot:
            #self.temp = temporary_caching()
            try:
                cache = temporary_caching()
                temp = cache[str(member.guild.id)][str(before.channel.id)]
                if (
                    before.channel.id == temp['voice']
                    and member.id == temp['owner']
                ):
                    if len(before.channel.members) == 0:
                        await self.delete_temporary_channel(member, voice=before)
                        return
                    temp['co_owners'].remove(member.id)
                    temp['members'].remove(member.id)
                    if len(temp['members']) >= 1:
                        rand_choice = random.choice(temp['members'])
                        temp['owner'] = rand_choice
                        if rand_choice not in temp['co_owners']:
                            temp['co_owners'].append(rand_choice)
                        await self.bot.get_channel(temp['text']).send(
                            content=f"원 오너인 {self.bot.get_user(member.id).name}님이 나가셔서 {self.bot.get_user(rand_choice).mention}님이 원주인으로 권한이 승격되었습니다."
                        )
                        return
            except:
                pass
    @Cog.listener(name="on_button_click")
    async def temporary_button_control(self,interaction:Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.respond(content="음성채널에 접속하셔야만 조작이 가능해요.")
        guild = self.bot.get_guild(interaction.guild_id)
        try:
            voice_channel: discord.VoiceChannel = guild.get_member(interaction.user.id).voice.channel
            cache = temporary_caching()
            temp = cache[str(guild.id)][str(voice_channel.id)]
            if temp['text'] == interaction.channel_id:
                if (
                    interaction.custom_id.startswith("temporary_")
                    and interaction.user.id not in temp['co_owners']
                ):
                    return await interaction.send(content="관리자가 아니어서 사용할수없어요.",delete_after=5)
                if interaction.custom_id == "temporary_addmember":
                    await self.temporary_addmember(interaction)
                if interaction.custom_id == "temporary_kick":
                    await self.temporary_kick(interaction,voice_channel)
                if interaction.custom_id == "temporary_addcoowner":
                    await self.temporary_addcoowner(interaction,voice_channel)
                if interaction.custom_id == "temporary_rename":
                    await self.temporary_rename(interaction,voice_channel)
                if interaction.custom_id == "temporary_editlimit":
                    await self.temporary_editlimit(interaction,voice_channel)
                if interaction.custom_id == "temporary_code":
                    await interaction.send(content=f"다음 코드를 복사해 붙여넣으세요.\n 텍스트 채널 - `<#{interaction.channel_id}>`\n음성 채널 - `<#{voice_channel.id}>`",ephemeral=False,delete_after=5)
                dump_temporary_caching(cache)
        except KeyError:
            return


def setup(bot):
    bot.add_cog(temporary(bot))