import asyncio
import random
from datetime import datetime

import discord
from discord.ext.commands import command, Cog, Bot
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)


class mafia(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.data = {}
        self.night = True
        super().__init__()

    def pick(self, guild, m, p, d):
        def seq(value):
            count = 0
            for u in dummy:
                if value == u:
                    return count
                count += 1

        def select(num, role):
            for i in range(num):
                value = random.choice(dummy)
                users[role].append(value)
                del dummy[seq(value)]

        users = self.data[guild]
        dummy = users['users'][:]
        select(m, 'mafia')
        select(p, 'police')
        select(d, 'doctor')
        users['citizen'] = dummy

    async def end(self, guild, winner, data, thread, msg):
        embed = discord.Embed(title="게임 종료!", color=0x5865F2, description='')
        if winner == 'citizen':
            embed.description = "모든 마피아가 사망하였습니다. 시민팀이 승리하였습니다."
        else:
            embed.description = "모든 시민이 사망하였습니다. 마피아가 승리하였습니다."

        data['winner'] = winner

        try:
            doctor = self.bot.get_user(data['doctor'][0]).mention
        except IndexError:
            doctor = '`없음`'

        embed.add_field(name="플레이어",
                        value=f"마피아: {', '.join([self.bot.get_user(m).mention for m in data['mafia']])}\n"
                              f"경찰: {self.bot.get_user(data['police'][0]).mention}\n"
                              f"의사: {doctor}\n"
                              f"시민: {', '.join([self.bot.get_user(c).mention for c in data['citizen']])}")

        await thread.purge(limit=None)
        await thread.send(embed=embed)
        await msg.edit(embed=embed)

        for u in data['users']:
            user = guild.get_member(u)
            await thread.set_permissions(user, send_messages=True)

        del self.data[guild.id]
        await asyncio.sleep(60)
        await thread.delete()

    async def check_finish(self, ctx, dead):
        data = self.data[ctx.guild.id]
        for u in data['mafia']:
            if u == dead:
                data['mafia-count'] -= 1
                break

        if len(data['users']) - (data['mafia-count'] + len(data['dead'])) <= data['mafia-count']:
            return 'mafia'
        elif data['mafia-count'] == 0:
            return 'citizen'
        return False

    @command(name="마피아", aliases=["ㅁㅍㅇ"])
    async def mafia(self, ctx):
        try:
            self.data[ctx.guild.id]
        except KeyError:
            pass
        else:
            embed = discord.Embed(title="Mafia", color=0xED4245,
                                  description="이미 이 서버에서 게임이 진행 중입니다.")
            return await ctx.reply(embed=embed)
        ask_em = discord.Embed(
            title="마피아게임!",
            description="마피아게임을 개최하시겠습니까?"
        )
        ask_msg = await ctx.reply(embed=ask_em, components=[
            [Button(label="개최하기", custom_id="mafia_open", style=ButtonStyle.green),
             Button(label="취소", custom_id="mafia_close", style=ButtonStyle.red)]])

        try:
            interaction: Interaction = await self.bot.wait_for("button_click",
                                                               check=lambda
                                                                   i: i.user.id == ctx.author.id and i.channel_id == ctx.channel.id and i.message.id == ask_msg.id,
                                                               timeout=60)
            await interaction.respond(type=6)
            value = interaction.custom_id
        except asyncio.TimeoutError:
            await ask_msg.delete()
            return await ctx.reply("시간초과로 취소되었어요.")
        if value == "mafia_close":
            await ask_msg.delete()
            return await ctx.reply("취소하셨어요.")
        data = self.data[ctx.guild.id] = {}
        users = data['users'] = []
        data['mafia'], data['police'], data['doctor'], data['citizen'], data['dead'] = [], [], [], [], []
        users.append(ctx.author.id)
        await ask_msg.delete()
        pend_em = discord.Embed(
            title="마피아게임!",
            description=f"{ctx.author.mention}님이 마피아게임을 개최하셨어요!\n아래 '참가하기' 버튼을 통해 참가하세요!\n1분후 게임이 시작됩니다!"
        )

        async def pend_callback(interaction: Interaction):
            value = interaction.custom_id
            user_id = interaction.user.id
            if value == "mafia_waiting_join" and user_id not in users:
                users.append(user_id)
                await interaction.channel.send(content=f"<@{user_id}>님이 게임에 참여하셨어요!")
                await interaction.message.edit(embed=pend_em.set_field_at(0, name="참가자", value=f"`{len(users)}명`"))
            if value == "mafia_waiting_leave" and user_id in users:
                users.remove(user_id)
                await interaction.channel.send(content=f"<@{user_id}>님이 게임에서 나가셨어요..")
                await interaction.message.edit(embed=pend_em.set_field_at(0, name="참가자", value=f"`{len(users)}명`"))

        pend_em.add_field(name="참가자", value=f"`{len(users)}명`")
        pend_components = [
            self.bot.components_manager.add_callback(
                Button(label="참가하기", emoji="📥", custom_id="mafia_waiting_join", style=ButtonStyle.green),
                pend_callback),
            self.bot.components_manager.add_callback(
                Button(label="나가기", emoji="📤", custom_id="mafia_waiting_leave", style=ButtonStyle.red), pend_callback)
        ]
        pending_msg = await ctx.send(embed=pend_em, components=pend_components)
        await asyncio.sleep(60)

        for row in pend_components:
            row.disable_components()
        await pending_msg.edit(components=pend_components)
        if len(users) == 0:
            del self.data[ctx.guild.id]
            return await pending_msg.edit(content="모든 유저가 나가 취소되었어요")
        if len(users) <= 3:
            del self.data[ctx.guild.id]
            return await ctx.send("인원수가 4명보다 부족하여 취소되었어요..")
        elif len(users) >= 24:
            del self.data[ctx.guild.id]
            return await ctx.send("인원수가 24명을 초과하여 취소되었어요..")
        part_embed = discord.Embed(title="Mafia", color=0x5865F2,
                                   description=f"`{len(users)}명`이 게임에 참가합니다."
                                               f"\n참가자: {', '.join([f'<@{u}>' for u in users])}\n\n"
                                               f"잠시 후 게임이 시작됩니다.")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)
        }
        thread = await ctx.guild.create_text_channel(name="마피아", overwrites=overwrites)
        for i in users:
            await thread.set_permissions(ctx.guild.get_member(i), read_messages=True, send_messages=True)
        part_msg = await thread.send(' '.join(f'<@{u}>' for u in users), embed=part_embed)
        await asyncio.sleep(3)
        user_count = len(users)
        if user_count == 4:
            self.pick(ctx.guild.id, 1, 1, 0)
        elif user_count == 5:
            self.pick(ctx.guild.id, 1, 1, 1)
        elif user_count in [6, 7]:
            self.pick(ctx.guild.id, 2, 1, 1)
        else:
            self.pick(ctx.guild.id, 3, 1, 1)

        async def check_job(interaction: Interaction):
            embed = discord.Embed(title="Mafia", color=0x5865F2, description="")
            if interaction.user.id in self.data[interaction.guild_id]['doctor']:
                embed.description = "당신은 `의사`입니다. 매일 밤 마피아로부터 죽임을 당하는 시민을 살릴 수 있습니다."
            elif interaction.user.id in self.data[interaction.guild_id]['police']:
                embed.description = "당신은 `경찰`입니다. 매일 밤 선택한 유저가 마피아인지 아닌지를 확인할 수 있습니다."
            elif interaction.user.id in self.data[interaction.guild_id]['mafia']:
                embed.description = "당신은 `마피아`입니다. 매일 밤 한 시민을 살해할 수 있습니다."
            elif interaction.user.id in self.data[interaction.guild_id]['citizen']:
                embed.description = "당신은 `시민`입니다. 건투를 빕니다."
            else:
                embed.description = "당신은 게임 참가자가 아닙니다."
            return await interaction.respond(embed=embed, ephemeral=True)

        roles_embed = discord.Embed(title="직업이 배정되었습니다.", color=0x5865F2,
                                    description=f"마피아: `{len(data['mafia'])}명`\n"
                                                f"경찰: `{len(data['police'])}명`\n"
                                                f"의사: `{len(data['doctor'])}명`\n"
                                                f"시민: `{len(data['citizen'])}명`\n"
                                                f"\n메시지 하단의 버튼을 눌러 자신의 직업을 확인해주세요.\n"
                                                f"20초 후 1일차 밤이 됩니다.")
        await thread.send(embed=roles_embed, components=[
            self.bot.components_manager.add_callback(
                Button(style=ButtonStyle.blue, label="직업 확인하기"), check_job
            ),
        ], )
        await asyncio.sleep(20)
        await thread.purge(limit=None)
        data['mafia-count'] = len(data['mafia'])
        data['day'] = 1
        data['days'] = {}
        data['days'][1] = {'day': {}, 'night': {}}

        while True:
            print(self.data)
            self.night = True
            for i in users:
                await thread.set_permissions(ctx.guild.get_member(i), read_messages=True, send_messages=False)
            turn_night_embed = discord.Embed(title='Mafia', color=0x5865F2, description=f"밤이 되었습니다.")
            await thread.send(embed=turn_night_embed)
            await asyncio.sleep(0.5)

            if data['day'] == 20:
                del self.data[ctx.guild.id]
                embed = discord.Embed(title="Mafia", color=0xED4245,
                                      description="비정상적으로 게임이 길어져 강제로 종료되었습니다.")
                await thread.send(embed=embed)
                await asyncio.sleep(5)
                await thread.delete()
                break
            target = data['days'][data['day']]['night']
            target['mafia'], target['police'], target['doctor'], target['died'] = 0, 0, 0, 0

            async def callback(interaction: Interaction):
                if self.night is True:
                    user = int(interaction.values[0])
                    target = self.data[interaction.guild_id]['days'][self.data[interaction.guild_id]['day']]['night']

                    if interaction.user.id in self.data[interaction.guild_id]['mafia']:
                        if target['mafia'] and target['mafia'] != user:
                            embed = discord.Embed(title="Mafia", color=0x5865F2,
                                                  description=f"살해대상을 변경하였습니다.")
                            await interaction.send(embed=embed, ephemeral=True)
                        target['mafia'] = user

                    elif interaction.user.id in self.data[interaction.guild_id]['doctor']:
                        target['doctor'] = user

                    elif interaction.user.id in self.data[interaction.guild_id]['police'] and not target['police']:
                        target['police'] = user
                        embed = discord.Embed(title="Mafia", color=0x5865F2, description="")
                        if user in self.data[interaction.guild_id]['mafia']:
                            embed.description = f"{self.bot.get_user(user).mention}님은 마피아입니다."
                        else:
                            embed.description = f"{self.bot.get_user(user).mention}님은 마피아가 아닙니다."
                        return await interaction.send(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(title="Mafia", color=0xED4245, description="이미 능력을 사용하셨습니다.")
                        return await interaction.send(embed=embed, ephemeral=True)
                else:
                    vote = self.data[interaction.guild_id]['days'][self.data[interaction.guild_id]['day']]['day']
                    embed = discord.Embed(title="Mafia", color=0x5865F2, description="")

                    user = None
                    if interaction.values[0] != '건너뛰기':
                        user = interaction.values[0]
                        if interaction.user.id not in vote['voted'] and user:
                            vote['voted'].append(interaction.user.id)
                            vote['votes'][user] += 1
                            embed.description = f"<@{user}>님께 투표하였습니다."
                    elif interaction.user.id not in vote['voted'] and not user:
                        vote['voted'].append(interaction.user.id)
                        vote['votes']['건너뛰기'] += 1
                        embed.description = "투표 건너뛰기에 투표하였습니다."
                    else:
                        embed.description = "이미 투표하셨습니다."
                    return await interaction.send(embed=embed, ephemeral=True)

            async def activate_role(interaction: Interaction):
                options = [
                    SelectOption(label=u.name, value=u.id) for u in
                    [self.bot.get_user(u) for u in data['users'] if u not in data['dead']]
                ]
                if self.night is False:
                    options.insert(0, SelectOption(label='건너뛰기'))
                embed = discord.Embed(title="Mafia", color=0x5865F2, description="")
                if interaction.user.id in self.data[interaction.guild_id]['dead']:
                    embed.description = "사망하셨으므로 능력을 사용할 수 없습니다."
                elif interaction.user.id in self.data[interaction.guild_id]['citizen']:
                    embed.description = "당신은 시민이므로 능력이 존재하지 않습니다."
                elif interaction.user.id in self.data[interaction.guild_id]['mafia']:
                    embed.description = "살해할 유저를 선택해주세요."
                    return await interaction.send(embed=embed, ephemeral=True,
                                                  components=[self.bot.components_manager.add_callback(
                                                      Select(
                                                          options=options,
                                                      ),
                                                      callback,
                                                  )]
                                                  )
                elif interaction.user.id in self.data[interaction.guild_id]['doctor']:
                    embed.description = "살릴 유저를 선택해주세요."
                    return await interaction.send(embed=embed, ephemeral=True,
                                                  components=[self.bot.components_manager.add_callback(
                                                      Select(
                                                          options=options,
                                                      ),
                                                      callback,
                                                  )])
                elif interaction.user.id in self.data[interaction.guild_id]['police'] and \
                        self.data[interaction.guild_id]['day'] != 1:
                    embed.description = "조사할 유저를 선택해주세요."
                    return await interaction.send(embed=embed, ephemeral=True,
                                                  components=[self.bot.components_manager.add_callback(
                                                      Select(
                                                          options=options,
                                                      ),
                                                      callback,
                                                  )])
                else:
                    embed.description = "당신의 능력은 아직 개방되지 않았거나 게임에 참가하지 않으셨습니다."
                return await interaction.send(embed=embed, ephemeral=True)

            night_embed = discord.Embed(title=f"{data['day']}일차 - 밤", color=0x5865F2,
                                        description=f"메시지 하단의 버튼을 눌러 능력을 사용해주세요.\n"
                                                    f"\n30초 후 {data['day'] + 1}일차 낮이 됩니다.")
            night_msg = await thread.send(embed=night_embed, components=[
                self.bot.components_manager.add_callback(
                    Button(style=ButtonStyle.blue, label="능력 사용하기"), activate_role
                ),
            ])
            await asyncio.sleep(30)
            await night_msg.delete()
            data['day'] += 1
            self.night = False
            turn_day_embed = discord.Embed(title='Mafia', color=0x5865F2, description=f"낮이 되었습니다.")
            await thread.send(embed=turn_day_embed)
            await asyncio.sleep(0.5)
            dead_embed = discord.Embed(title=f"{data['day']}일차 - 낮", color=0x5865F2, description='')
            if not target['mafia'] or target['doctor'] == target['mafia']:
                dead_embed.description = "아무도 사망하지 않았습니다."
            else:
                target['died'] = target['mafia']
                data['dead'].append(target['mafia'])
                dead_embed.description = f"<@{target['mafia']}>님께서 사망하셨습니다."
            await thread.send(embed=dead_embed)

            check = await self.check_finish(ctx, target['mafia'])
            if check:
                return await self.end(ctx.guild, check, data, thread, part_msg)

            data['days'][data['day']] = {'day': {}, 'night': {}}

            for u in data['users']:
                if u in data['dead']:
                    continue
                await ctx.channel.set_permissions(self.bot.get_user(u), send_messages=True)

            vote = data['days'][data['day']]['day']
            now = datetime.timestamp(datetime.now())
            until = int(now) + 120
            time_voted = vote['time-voted'] = []
            # time_view = VoteTime(until, time_voted, data['users'])

            day_embed = discord.Embed(title=f"{data['day']}일차 - 낮", color=0x5865F2,
                                      description=f"120초간 자유 토론 시간이 주어집니다.")
            day_embed.add_field(name="남은 시간", value=f"<t:{until}:R>")
            day_msg = await thread.send(embed=day_embed)
            for i in users:
                await thread.set_permissions(ctx.guild.get_member(i), read_messages=True, send_messages=True)
            await asyncio.sleep(120)
            await day_msg.delete()

            vote['voted'], vote['votes'], vote['died'] = [], {}, 0
            vote['votes']['건너뛰기'] = len(data['users']) - len(data['dead'])
            for u in [u for u in data['users'] if u not in data['dead']]:
                vote['votes'][u] = 0

            async def VOTE_callback(interaction):
                if interaction.user.id in self.data[interaction.guild_id]['dead']:
                    embed = discord.Embed(title="Mafia", color=0xED4245, description="사망하셨으므로 투표할 수 없습니다.")
                    return await interaction.send(embed=embed, ephemeral=True)
                elif interaction.user.id not in self.data[interaction.guild_id]['users']:
                    embed = discord.Embed(title="Mafia", color=0xED4245, description="게임에 참가하지 않으셨으므로 투표할 수 없습니다.")
                    return await interaction.send(embed=embed, ephemeral=True)
                options = [
                    SelectOption(label=u.name, value=u.id) for u in
                    [self.bot.get_user(u) for u in data['users'] if u not in data['dead']]
                ]
                embed = discord.Embed(title="Mafia", color=0x5865F2, description="투표로 죽일 유저를 선택해주세요.")
                return await interaction.send(embed=embed, ephemeral=True,
                                              components=[self.bot.components_manager.add_callback(
                                                  Select(
                                                      options=options,
                                                  ),
                                                  callback,
                                              )]
                                              )

            vote_embed = discord.Embed(title=f"{data['day']}일차 - 투표", color=0x5865F2,
                                       description=f"30초 동안 투표로 죽일 사람을 선택해주세요.")
            await thread.send(embed=vote_embed, components=[
                self.bot.components_manager.add_callback(
                    Button(style=ButtonStyle.blue, label="투표하기"), VOTE_callback
                ),
            ])
            await asyncio.sleep(30)

            for v in vote['voted']:
                vote['votes']['건너뛰기'] -= 1

            await thread.purge(limit=None)
            total = sorted(vote['votes'].items(), key=lambda k: k[1], reverse=True)
            vote_result = ''
            for t in total:
                name = t[0]
                if t[0] != '건너뛰기':
                    name = f'<@{t[0]}>'
                vote_result += f'{name}: `{t[1]}표`\n'

            vote_result_embed = discord.Embed(title=f"{data['day']}일차 - 투표 결과", color=0x5865F2, description='')
            if total[0][1] == total[1][1] or total[0][0] == '건너뛰기':
                vote_result_embed.description = "아무도 사망하지 않았습니다."
            else:
                vote['died'] = total[0][0]
                data['dead'].append(total[0][0])
                vote_result_embed.description = f"<@{total[0][0]}>님께서 사망하셨습니다."
            vote_result_embed.add_field(name="투표 결과", value=vote_result)
            await thread.send(embed=vote_result_embed)

            check = await self.check_finish(ctx, total[0][0])
            if check:
                return await self.end(ctx.guild, check, data, thread, part_msg)
            await asyncio.sleep(1)


def setup(bot):
    bot.add_cog(mafia(bot))
