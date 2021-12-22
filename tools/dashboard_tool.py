import asyncio

import aiosqlite
import discord
from discord.ext.commands import Bot, Context
from py_cord_components import Interaction, Button,ButtonStyle

from tools.database_tool import DataBaseTool


class DashBoard:
    def __init__(self,bot,interaction=None,ctx=None):
        self.bot:Bot = bot
        self.interaction:Interaction = interaction
        self.ctx:Context = ctx
        self.version = "ver. 1.0"

    def dashboard_embed(self):
        em = discord.Embed(
            title="대시보드",
            description="하린봇 대시보드입니다.\n이곳에서 봇 셋팅을 하실수있습니다!\n업데이트가 있을때마다 직접 업데이트를 하셔야합니다.",
            colour=discord.Colour.random()
        )
        em.add_field(
            name="🎶 뮤직 설정",
            value="```뮤직기능을 사용하기위해 설정하거나 비활성화합니다.```"
        )
        em.add_field(
            name="🧩 개인채널 설정",
            value="```개인채널기능을 사용하기위해 설정하거나 비활성화합니다.```"
        )
        em.add_field(
            name="🎉 생일알림 설정",
            value="```생일알림기능을 설정합니다.```"
        )
        em.add_field(
            name="👋 환영인사 설정",
            value="```환영인사기능을 설정합니다.```"
        )
        em.add_field(
            name="🗺 초대추적 설정",
            value="```초대추적기능을 설정합니다.```"
        )
        em.add_field(
            name="📢 봇 공지설정",
            value="```봇 공지를 수신하거나 수신거절설정을 합니다.```"
        )
        em.add_field(
            name="📥 대시보드 업데이트",
            value="```현재 사용중인 대시보드를 업데이트합니다.```"
        )
        em.set_footer(
            text=self.version
        )
        return em

    async def dashboard_setup(self):
        db = await aiosqlite.connect('db/db.sqlite')
        cur = await db.execute("SELECT * FROM dashboard WHERE guild = ?",(self.ctx.guild.id,))
        if await cur.fetchone() is not None:
            return await self.ctx.reply('이미 설정되어있어요.')
        text_channel:discord.TextChannel = await self.ctx.guild.create_text_channel(name='하린-봇-대시보드')
        msg = await text_channel.send(embed=self.dashboard_embed(),components=[
            [
                Button(label="뮤직 설정(사용불가)",style=ButtonStyle.green,custom_id='dash_music',emoji='🎶',disabled=True),
                Button(label='개인채널 설정',style=ButtonStyle.green,custom_id='dash_temp',emoji='🧩'),
                Button(label='생일알림 설정',style=ButtonStyle.green,custom_id='dash_birth',emoji='🎉'),
                Button(label='환영인사 설정',style=ButtonStyle.green,custom_id='dash_welcome',emoji='👋'),
                Button(label='초대추적 설정',style=ButtonStyle.green,custom_id='dash_ivt',emoji='🗺')
             ],
            [
                Button(label='봇 공지설정',style=ButtonStyle.green,custom_id='dash_notify',emoji='📢'),
                Button(label='대시보드 업데이트',style=ButtonStyle.blue,custom_id='dash_update',emoji='📥')
            ]
        ])
        await db.execute("INSERT  INTO dashboard(guild,channel,message) VALUES (?,?,?)",(self.ctx.guild.id,text_channel.id,msg.id))
        await db.commit()
        await self.ctx.reply('✅ 성공적으로 대시보드를 추가하였습니다.\n임의로 채널을 삭제할시 더 이상 커스터마이징이 불가하며 에러가 발생할수있으니 주의바랍니다.')

    async def dashboard_update(self):
        await self.interaction.message.edit(embed=self.dashboard_embed(),components=[
            [
                Button(label="뮤직 설정(사용불가)",style=ButtonStyle.green,custom_id='dash_music',emoji='🎶',disabled=True),
                Button(label='개인채널 설정',style=ButtonStyle.green,custom_id='dash_temp',emoji='🧩'),
                Button(label='생일알림 설정',style=ButtonStyle.green,custom_id='dash_birth',emoji='🎉'),
                Button(label='환영인사 설정',style=ButtonStyle.green,custom_id='dash_welcome',emoji='👋'),
                Button(label='초대추적 설정',style=ButtonStyle.green,custom_id='dash_ivt',emoji='🗺')
             ],
            [
                Button(label='봇 공지설정',style=ButtonStyle.green,custom_id='dash_notify',emoji='📢'),
                Button(label='대시보드 업데이트',style=ButtonStyle.blue,custom_id='dash_update',emoji='📥')
            ]
        ])
        url = ""
        await self.interaction.channel.send(f'✅ 성공적으로 대시보드를 업데이트하였습니다.\n업데이트 내역보기 - {url}',delete_after=10)

    async def tsetup(self):
        db = await aiosqlite.connect("db/db.sqlite")
        check_ = await DataBaseTool(db).check_db_temporary(guild=self.interaction.guild)
        if not check_:
            return await self.interaction.channel.send(content="❎ 이미 설정되어있는것같아요!",delete_after=5)
        text_channel = await self.interaction.guild.create_text_channel(name="❓개인채널 안내")
        voice_channel = await self.interaction.guild.create_voice_channel(name="➕ 개인채널 생성")
        category = await self.interaction.guild.create_category(name="개인채널 리스트")
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
        await DataBaseTool(db).add_temporary_data(guild=self.interaction.guild, voice_channel=voice_channel,
                                                  category_channel=category)
        await self.interaction.channel.send(content="✅ 성공적으로 설정되었어요!\n생성된 채널들의 이름과 위치,권한은 마음껏 커스터마이징이 가능하지만 임의로 삭제하시면 오류가 발생할수있어요.",delete_after=5)

    async def birth_setup(self):
        for channel in self.interaction.guild.text_channels:
            if channel.topic is not None and "-HOnBtd" in str(channel.topic):
                msg = await self.interaction.channel.send(f'이미 설정되어있어요. \n설정된 채널: {channel.mention}\n사용해제하시겠어요?',components=[
                    [Button(label='사용해제',style=ButtonStyle.red,custom_id='delete'),
                     Button(label='취소',custom_id='cancel')]
                ])
                try:
                    inter: Interaction = await self.bot.wait_for('button_click',check=lambda i, msg=msg:i.user.id == self.interaction.user.id and i.message.id == msg.id,timeout=30)
                    value = inter.custom_id
                    if value == 'delete':
                        await msg.delete()
                        await channel.edit(topic=str(channel.topic).replace('-HOnBtd',''))
                        return await inter.channel.send('성공적으로 사용해제하였습니다.',delete_after=5)
                    else:
                        return await msg.delete()
                except asyncio.TimeoutError:
                    return await msg.delete()
        await self.interaction.guild.create_text_channel(name='🎉생일축하드립니다',topic='-HOnBtd')
        await self.interaction.channel.send('✅ 성공적으로 설정하였습니다.',delete_after=5)

    async def welcome_setup(self):
        database = await aiosqlite.connect("db/db.sqlite")
        cur = await database.execute("SELECT * FROM welcome WHERE guild = ?", (self.interaction.guild.id,))
        data = await cur.fetchone()
        if data is not None:
            msg = await self.interaction.channel.send(f'이미 설정되어있어요. \n설정된 채널: <#{data[1]}>\n사용해제하시겠어요?',
                                                      components=[
                                                          [Button(label='사용해제', style=ButtonStyle.red,
                                                                  custom_id='delete'),
                                                           Button(label='취소', custom_id='cancel')]
                                                      ])
            try:
                inter: Interaction = await self.bot.wait_for('button_click', check=lambda
                    i: i.user.id == self.interaction.user.id and i.message.id == msg.id, timeout=30)
                value = inter.custom_id
                if value == 'delete':
                    await msg.delete()
                    await database.execute('DELETE FROM welcome WHERE guild = ?',(self.interaction.guild_id,))
                    await database.commit()
                    await inter.channel.send('성공적으로 사용해제하였습니다.', delete_after=5)
                else:
                    await msg.delete()
            except asyncio.TimeoutError:
                await msg.delete()
        elif self.interaction.guild.system_channel is None:
            msg = await self.interaction.channel.send('시스템 채널이 발견되지않았습니다.\n환영메세지를 보내기위해 채널ID만 30초내에 입력해주세요.')
            try:
                message:discord.Message = await self.bot.wait_for('message',
                                                                  check=lambda i:i.author.id == self.interaction.user.id and i.channel.id == self.interaction.channel_id,
                                                                  timeout=30)
                await database.execute("INSERT INTO welcome(guild,channel) VALUES (?,?)",(self.interaction.guild_id,int(message.content)))
                await database.commit()
                await self.interaction.channel.send('✅ 성공적으로 설정하였습니다.', delete_after=5)
            except asyncio.TimeoutError:
                await msg.delete()
        else:
            await database.execute("INSERT INTO welcome(guild,channel) VALUES (?,?)",
                                   (self.interaction.guild_id, self.interaction.guild.system_channel.id))
            await database.commit()
            await self.interaction.channel.send('✅ 성공적으로 설정하였습니다.', delete_after=5)

    async def ivt_setup(self):
        database = await aiosqlite.connect("db/db.sqlite")
        cur = await database.execute("SELECT * FROM invite_tracker WHERE guild = ?", (self.interaction.guild.id,))
        data = await cur.fetchone()
        if data is not None:
            msg = await self.interaction.channel.send(f'이미 설정되어있어요. \n설정된 채널: <#{data[1]}>\n사용해제하시겠어요?',
                                                      components=[
                                                          [Button(label='사용해제', style=ButtonStyle.red,
                                                                  custom_id='delete'),
                                                           Button(label='취소', custom_id='cancel')]
                                                      ])
            try:
                inter: Interaction = await self.bot.wait_for('button_click', check=lambda
                    i: i.user.id == self.interaction.user.id and i.message.id == msg.id, timeout=30)
                value = inter.custom_id
                if value == 'delete':
                    await msg.delete()
                    await database.execute('DELETE FROM invite_tracker WHERE guild = ?',(self.interaction.guild_id,))
                    await database.commit()
                    await inter.channel.send('성공적으로 사용해제하였습니다.', delete_after=5)
                else:
                    await msg.delete()
            except asyncio.TimeoutError:
                await msg.delete()
        elif self.interaction.guild.system_channel is None:
            msg = await self.interaction.channel.send('시스템 채널이 발견되지않았습니다.\n환영메세지를 보내기위해 채널ID만 30초내에 입력해주세요.')
            try:
                message:discord.Message = await self.bot.wait_for('message',
                                                                  check=lambda i:i.author.id == self.interaction.user.id and i.channel.id == self.interaction.channel_id,
                                                                  timeout=30)
                await database.execute("INSERT INTO invite_tracker(guild,channel) VALUES (?,?)",(self.interaction.guild_id,int(message.content)))
                await database.commit()
                await self.interaction.channel.send('✅ 성공적으로 설정하였습니다.', delete_after=5)
            except asyncio.TimeoutError:
                await msg.delete()
        else:
            await database.execute("INSERT INTO invite_tracker(guild,channel) VALUES (?,?)",
                                   (self.interaction.guild_id, self.interaction.guild.system_channel.id))
            await database.commit()
            await self.interaction.channel.send('✅ 성공적으로 설정하였습니다.', delete_after=5)

    async def bot_notify_setup(self):
        for channel in self.interaction.guild.text_channels:
            if channel.topic is not None and "-HOnNt" in str(channel.topic):
                msg = await self.interaction.channel.send(f'이미 설정되어있어요. \n설정된 채널: {channel.mention}\n사용해제하시겠어요?',components=[
                    [Button(label='사용해제',style=ButtonStyle.red,custom_id='delete'),
                     Button(label='취소',custom_id='cancel')]
                ])
                try:
                    inter: Interaction = await self.bot.wait_for('button_click',check=lambda i, msg=msg:i.user.id == self.interaction.user.id and i.message.id == msg.id,timeout=30)
                    value = inter.custom_id
                    if value == 'delete':
                        await msg.delete()
                        await channel.edit(topic=str(channel.topic).replace('-HOnNt',''))
                        return await inter.channel.send('성공적으로 사용해제하였습니다.',delete_after=5)
                    else:
                        return await msg.delete()
                except asyncio.TimeoutError:
                    return await msg.delete()
        await self.interaction.guild.create_text_channel(name='하린봇-공지사항',topic='-HOnNt')
        await self.interaction.channel.send('✅ 성공적으로 설정하였습니다.',delete_after=5)

    async def dash_update(self):
        version = self.interaction.message.embeds[0].footer.text
        print(version)
        if self.version != version:
            return await self.dashboard_update()
        return await self.interaction.channel.send('이미 최신버전입니다.',delete_after=5)


    async def dashboard_process(self,type):
        if type == 'dash_temp':
            return await self.tsetup()
        elif type == 'dash_birth':
            return await self.birth_setup()
        elif type == 'dash_welcome':
            return await self.welcome_setup()
        elif type == 'dash_ivt':
            return await self.ivt_setup()
        elif type == 'dash_notify':
            return await self.bot_notify_setup()
        elif type == 'dash_update':
            return await self.dash_update()