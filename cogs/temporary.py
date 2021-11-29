import asyncio
import traceback

import discord
from discord.ext.commands import command, Cog
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)
from bot import MyBot
class temporary(Cog):
    def __init__(self, bot:MyBot):
        self.bot = bot
        self.temp = {}
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
        category: discord.CategoryChannel = self.bot.get_channel(914769237971697715)
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
        data = self.temp[member.guild.id] = {}
        data[voice_channel.id] = {
            "owner":member.id,
            "co_owners":[member.id],
            "members":[member.id],
            "voice": voice_channel.id,
            "text": text_channel.id
        }
        await self.send_temporary_dafault_chat(member,text_channel)

    async def delete_temporary_channel(self,member:discord.Member,voice:discord.VoiceState):
        try:
            voice_channel = self.bot.get_channel(self.temp[member.guild.id][voice.channel.id]['voice'])
            text_channel = self.bot.get_channel(self.temp[member.guild.id][voice.channel.id]['text'])
            await voice_channel.delete()
            await text_channel.delete()
            del self.temp[member.guild.id][voice.channel.id]
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
        member_id = int(msg.content)
        member = self.bot.get_guild(interaction.guild_id).get_member(member_id)
        text_channel = self.bot.get_channel(interaction.channel_id)
        voice_channel = interaction.user.voice.channel
        (self.temp[interaction.guild_id][voice_channel.id]['members']).append(member_id)
        await text_channel.set_permissions(member, read_messages=True, send_messages=True)
        await voice_channel.set_permissions(member, connect=True)
        await bot_msg.delete()
        await msg.delete()
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
        member_id = int(msg.content)
        member: discord.Member = self.bot.get_guild(interaction.guild_id).get_member(member_id)
        text_channel = self.bot.get_channel(interaction.channel_id)
        # voice_channel = interaction.user.voice.channel
        list(self.temp[interaction.guild_id][voice_channel.id]['members']).remove(member_id)
        try:
            list(self.temp[interaction.guild_id][voice_channel.id]['co_owners']).remove(member_id)
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
        member_id = int(msg.content)
        member: discord.Member = self.bot.get_guild(interaction.guild_id).get_member(member_id)
        if member_id in self.temp[interaction.guild_id][voice_channel.id]['co_owners']:
            return await interaction.send(content=f"{member.mention}님은 이미 관리자로 등록되어있어요.", delete_after=5)
        (self.temp[interaction.guild_id][voice_channel.id]['co_owners']).append(member_id)
        await bot_msg.delete()
        await msg.delete()
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
        name = msg.content
        await voice_channel.edit(name=name)
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
        limit = msg.content
        await voice_channel.edit(user_limit=limit)
        await bot_msg.delete()
        await msg.delete()
        await channel.send(content=f"✅ 성공적으로 `{limit}`으로 변경했어요.", delete_after=5)

    @Cog.listener('on_voice_state_update')
    async def temporary_event(self,member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if before.channel is None and after.channel is not None and not member.bot:
            if after.channel.id == 914761852708331560:
                await self.create_temporary_channel(member)
        elif not member.bot:
            try:
                if before.channel.id == self.temp[member.guild.id][before.channel.id]['voice']\
                        and member.id == self.temp[member.guild.id][before.channel.id]['owner']:
                    await self.delete_temporary_channel(member,voice=before)
            except:
                pass
    @Cog.listener(name="on_button_click")
    async def temporary_button_control(self,interaction:Interaction):
        try:
            if interaction.custom_id.startswith("temporary_"):
                interaction.user.voice.channel
        except:
            return await interaction.respond(content="음성채널에 접속하셔야만 조작이 가능해요.")
        voice_channel: discord.VoiceChannel = interaction.user.voice.channel
        if interaction.custom_id.startswith("temporary_"):
            if not interaction.user.id in self.temp[interaction.guild_id][voice_channel.id]['co_owners']:
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
            await interaction.send(content=f"다음 코드를 복사해 붙여넣으세요 `<#{interaction.channel_id}>`",ephemeral=False,delete_after=5)


def setup(bot):
    bot.add_cog(temporary(bot))