import asyncio
import datetime
import time
import discord
from discord.ext.commands import command, Cog, group
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)
from bot import MyBot
from tools.delivery_tracking import Tracking
from tools.database_tool import dump_delivery_caching, delivery_caching
from dateutil.parser import parse


class ExampleCog(Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.delivery_notify_loop = self.bot.loop.create_task(self.tracker_loop())
        super().__init__()

    @staticmethod
    def convert_timestamp(times):
        convert_time = parse(times)
        strftime = convert_time.strftime('%Y-%m-%d %H:%M:%S')
        return str(time.mktime(datetime.datetime.strptime(strftime, '%Y-%m-%d %H:%M:%S').timetuple()))[:-2]

    @staticmethod
    def convert_strftime(times):
        convert_time = parse(times)
        return convert_time.strftime('%Y-%m-%d %H:%M:%S')

    async def send_delivery_embed(self, ctx, data: dict, interaction: Interaction):
        status = data.get('status')
        message = data.get('message')
        datas = data.get('data')
        em = discord.Embed(color=ctx.author.color)
        if status == 200:
            em.title = f"{ctx.author.display_name}님의 배송상태"
            em.description = f"현재 배송상태\n```yml\n{datas['state']['text']}\n```"
            em.add_field(
                name="보내는분(택배인수시각)",
                value=f"{datas['from']['name']}(<t:{self.convert_timestamp(datas['from']['time'])}:R>)"
            )
            times = datas['to']['time']
            complate = f"<t:{self.convert_timestamp(times)}:R>" if times != None else "정보가 없거나 아직 배송이 완료되지않은 상태입니다."
            em.add_field(
                name="받으시는분(택배배송완료시각)",
                value=f"{datas['to']['name']}({complate})"
            )
            em.add_field(
                name="배송 진행 상태",
                value="\n\n".join(
                    f"상태: {i['status']['text']}(<t:{self.convert_timestamp(i['time'])}:R>)\n위치: {i['location']['name']}\n메세지: {i['description']}"
                    for i in datas['progresses']),
                inline=False
            )
        else:
            em.title = f"{ctx.author.display_name}님의 배송상태를 조회할 수 없어요."
            em.description = message
        return await interaction.respond(embed=em)

    async def add_delivery_data(self, ctx, data, interaction: Interaction):
        cach = delivery_caching()
        try:
            user_data = cach[str(ctx.author.id)]
            for i in user_data:
                if i['code'] == data['code']:
                    return await interaction.respond(content="이미 등록되어있는 송장번호에요.")
            user_data.append(
                {
                    "code": data['code'],
                    "company": data['company'],
                    'stat': data['stat']
                }
            )
            dump_delivery_caching(user_data)
        except KeyError:
            new_data = {}
            new_data[str(ctx.author.id)] = [
                {
                    "code": data['code'],
                    "company": data['company'],
                    'stat': data['stat']
                }
            ]
            dump_delivery_caching(new_data)
        except TypeError:
            new_data = {}
            new_data[str(ctx.author.id)] = [
                {
                    "code": data['code'],
                    "company": data['company'],
                    'stat': data['stat']
                }
            ]
            dump_delivery_caching(new_data)
        await interaction.respond(content="성공적으로 등록하였어요! 이제부터 배송상태가 바뀔때마다 알려드릴게요!")

    @group(name="배송조회", aliases=["택배조회", "택배", "송장조회", "송장"], invoke_without_command=True)
    async def search_delivery(self, ctx, code: int):
        em = discord.Embed(color=ctx.author.color)
        em.title = "배송사를 선택해주세요."
        em.description = f"입력한 송장번호 (`{code}`)의 배송사를 선택해주세요."
        compamy_msg = await ctx.reply(embed=em, components=[
            Select(options=[
                SelectOption(label=i['name'], value=i['id']) for i in Tracking().get_company_list()
            ])
        ])
        try:
            interaction: Interaction = await self.bot.wait_for("select_option",
                                                               check=lambda i: i.user.id == ctx.author.id
                                                                               and i.message.id == compamy_msg.id,
                                                               timeout=60)
            value = interaction.values[0]
            # await interaction.respond(type=6)
            await compamy_msg.disable_components()
            resp = await Tracking(value, code).get_info()
            return await self.send_delivery_embed(ctx, resp, interaction)
        except asyncio.TimeoutError:
            await compamy_msg.disable_components()

    @search_delivery.command(name="등록")
    async def add_search_delivery(self, ctx, code: int):
        em = discord.Embed(color=ctx.author.color)
        em.title = "배송사를 선택해주세요."
        em.description = f"입력한 송장번호 (`{code}`)의 배송사를 선택해주세요."
        compamy_msg = await ctx.reply(embed=em, components=[
            Select(options=[
                SelectOption(label=i['name'], value=i['id']) for i in Tracking().get_company_list()
            ])
        ])
        try:
            interaction: Interaction = await self.bot.wait_for("select_option",
                                                               check=lambda i: i.user.id == ctx.author.id
                                                                               and i.message.id == compamy_msg.id,
                                                               timeout=60)
            value = interaction.values[0]
            await interaction.respond(type=6)
            await compamy_msg.disable_components()
            resp = await Tracking(value, code).get_info()
            data = {'code': code, 'company': value, "stat": resp['data']['state']}
            return await self.add_delivery_data(ctx, data, interaction)
        except asyncio.TimeoutError:
            await compamy_msg.disable_components()

    async def tracker_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            data = delivery_caching()
            for key in data.keys():
                print(key)
                for i in data[key]:
                    print(i)
                    resp = await Tracking(i['company'], i['code']).get_info()
                    resp_data = resp['data']
                    if resp['status'] != 200:
                        break
                    print(resp_data['state']['id'], i['stat']['id'], resp_data['state']['id'] != i['stat']['id'])
                    if resp_data['state']['id'] != i['stat']['id']:
                        em = discord.Embed(
                            title="택배알림 DM 도착!",
                            description=f"송장번호: {i['code']}\n배송사: {resp_data['carrier']['name']}\n보내시는분: {resp_data['from']['name']}\n받으시는분: {resp_data['to']['name']}"
                        )
                        em.add_field(
                            name="배송상태",
                            value=f"```yml\n{i['stat']['text']} ⏩ {resp_data['progresses'][-1]['status']['text']}({self.convert_strftime(resp_data['progresses'][-1]['time'])})\n```",
                            inline=False
                        )
                        em.add_field(
                            name="배송메시지",
                            value=f"```\n{resp_data['progresses'][-1]['description']}\n```",
                            inline=False
                        )
                        data[str(key)].remove(i)
                        data[str(key)].append(
                            {
                                "code": i['code'],
                                "company": i['company'],
                                'stat': resp_data['state']
                            }
                        )
                        dump_delivery_caching(data)
                        try:
                            await (await self.bot.fetch_user(int(key))).send(embed=em)
                        except discord.Forbidden:
                            pass
            await asyncio.sleep(2)

    def cog_unload(self):
        self.delivery_notify_loop.cancel()


def setup(bot):
    bot.add_cog(ExampleCog(bot))
