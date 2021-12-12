import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import command, Cog
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)
from tools.database_tool import economy_caching,dump_economy_caching,challenge_caching,dump_challenge_caching
from tools.execption import PermError
from bot import MyBot
from random import choices,randint

#economy_cach = economy_caching()







class FishingGame:
    def __init__(self,bot:MyBot,ctx:commands.Context,data:dict):
        self.bot = bot
        self.ctx = ctx
        self.data = data
        self.fish = ['cod', 'salmon', 'tropical', 'pufferfish', 'squid', 'glow_squid']
        self.fish_name = {
            "cod":f"{self.bot.get_emoji(916994060215001098)}대구",
            "tropical":f"{self.bot.get_emoji(916994060026257472)}열대어",
            "pufferfish":f"{self.bot.get_emoji(916994060315689020)}복어",
            "squid":f"{self.bot.get_emoji(917756503174307850)}오징어",
            "glow_squid":f"{self.bot.get_emoji(916994060223402004)}발광오징어",
            "salmon":f"{self.bot.get_emoji(916994060227608596)}연어"
        }

    async def Start(self):
        self.data[str(self.ctx.author.id)]['items'].remove("silverfish")
        em = discord.Embed(
            title="낚시중",
            description="낚싯대를 바다로 던졌다",
            color=self.ctx.author.color
        )
        msg = await self.ctx.reply(embed=em)
        await asyncio.sleep(randint(3,6))
        em.description = "앗! 낚싯대가 요동을 친다!\n아래 낚아채기버튼을 누르자!"
        await msg.delete()
        fishing_msg = await self.ctx.reply(embed=em, components=[
            Button(label="낚아채기", style=ButtonStyle.green, custom_id=(choices(["fail", "success"]))[0])])
        try:
            interaction:Interaction = await self.bot.wait_for("button_click",check=lambda i:i.message.id == fishing_msg.id and i.user.id == self.ctx.author.id,timeout=10)
            value = interaction.custom_id
            await interaction.respond(type=6)
            await fishing_msg.disable_components()
            if value == "fail":
                desc = choices(["앗..물고기가 미끼만 먹고 도망쳐버렸다.","물고기의 엄청난 힘에 못이겨 낚싯대를 놓쳐버렸다.","쓰레기가 잡혀버렸다."])[0]
                if desc == "물고기의 엄청난 힘에 못이겨 낚싯대를 놓쳐버렸다.":
                    self.data[str(self.ctx.author.id)]['items'].remove("default_fishing_rod")
                em.description = desc
            else:
                population = [0, 1, 2, 3, 4, 5]
                weights = [0.11, 0.96, 0.94,0.90, 0.85, 0.75]
                resp = choices(population,weights)
                self.data[str(self.ctx.author.id)]['items'].append(self.fish[resp[0]])
                em.description = f"{self.fish_name[self.fish[resp[0]]]}를 낚았다!"
            await fishing_msg.edit(embed=em)
            dump_economy_caching(self.data)
        except asyncio.TimeoutError:
            await fishing_msg.disable_components()
            em.description = "낚싯대를 낚아채지않아 물고기가 도망가버렸다."
            await fishing_msg.edit(embed=em)
            dump_economy_caching(self.data)



class economy(Cog):
    def __init__(self, bot:MyBot):
        self.bot = bot
        self.data = economy_caching()
        self.challenge = challenge_caching()
        self.challenge_dict = {
            "buy_items": "내 인생 첫 아이템 구매",
            "deal_items": "점상과의 거래",
            "first_fishing": "낚시인생의 시작!",
            "first_stock": "일개미인생 시작!",
            "bankruptcy": "파산됐지만 처음부터 하나씩 다시시작!",
            "first_gambling": "내 인생 첫 도박",
            "item_enhancement":"발전하는 아이템!",
            "loans":"마이너스 인생의 시작!"
        }
        self.challenge_max_dict = {
            "buy_items": 1,
            "deal_items": 5,
            "first_fishing": 1,
            "first_stock": 1,
            "bankruptcy": 1,
            "first_gambling": 1,
            "item_enhancement":3,
            "loans":1
        }
        self.item_price = {
            "default_fishing_rod":5000,
            "bucket":2000,
            "silverfish":2000
        }
        self.item_name = {
            "default_fishing_rod": f"{self.bot.get_emoji(916994059954978877)}평범한 낚싯대",
            "bucket": f"{self.bot.get_emoji(917212624997974056)}양동이",
            "silverfish":f"{self.bot.get_emoji(917225134220259378)}미끼용 벌레",
            "cod": f"{self.bot.get_emoji(916994060215001098)}대구",
            "tropical": f"{self.bot.get_emoji(916994060026257472)}열대어",
            "pufferfish": f"{self.bot.get_emoji(916994060315689020)}복어",
            "squid": f"{self.bot.get_emoji(917756503174307850)}오징어",
            "glow_squid": f"{self.bot.get_emoji(916994060223402004)}발광오징어",
            "salmon": f"{self.bot.get_emoji(916994060227608596)}연어"
        }
        self.register_cooldown = []
        super().__init__()

    async def cog_before_invoke(self, ctx: commands.Context):
        self.data = economy_caching()
        self.challenge = challenge_caching()

    @staticmethod
    def get_kor_amount_string(num_amount, ndigits_round=0, str_suffix='원'):
        """숫자를 자릿수 한글단위와 함께 리턴한다 """
        assert isinstance(num_amount, int) and isinstance(ndigits_round, int)
        assert num_amount >= 1, '최소 1원 이상 입력되어야 합니다'
        ## 일, 십, 백, 천, 만, 십, 백, 천, 억, ... 단위 리스트를 만든다.
        maj_units = ['만', '억', '조', '경', '해', '자', '양', '구', '간', '정', '재', '극']  # 10000 단위
        units = [' ']  # 시작은 일의자리로 공백으로하고 이후 십, 백, 천, 만...
        for mm in maj_units:
            units.extend(['십', '백', '천'])  # 중간 십,백,천 단위
            units.append(mm)

        list_amount = list(str(round(num_amount, ndigits_round)))  # 라운딩한 숫자를 리스트로 바꾼다
        list_amount.reverse()  # 일, 십 순서로 읽기 위해 순서를 뒤집는다

        str_result = ''  # 결과
        num_len_list_amount = len(list_amount)

        for i in range(num_len_list_amount):
            str_num = list_amount[i]
            # 만, 억, 조 단위에 천, 백, 십, 일이 모두 0000 일때는 생략
            if num_len_list_amount >= 9 and i >= 4 and i % 4 == 0 and ''.join(list_amount[i:i + 4]) == '0000':
                continue
            if str_num == '0':  # 0일 때
                if i % 4 == 0:  # 4번째자리일 때(만, 억, 조...)
                    str_result = units[i] + str_result  # 단위만 붙인다
            elif str_num == '1':  # 1일 때
                if i % 4 == 0:  # 4번째자리일 때(만, 억, 조...)
                    str_result = str_num + units[i] + str_result  # 숫자와 단위를 붙인다
                else:  # 나머지자리일 때
                    str_result = units[i] + str_result  # 단위만 붙인다
            else:  # 2~9일 때
                str_result = str_num + units[i] + str_result  # 숫자와 단위를 붙인다
        str_result = str_result.strip()  # 문자열 앞뒤 공백을 제거한다
        if len(str_result) == 0:
            return None
        if not str_result[0].isnumeric():  # 앞이 숫자가 아닌 문자인 경우
            str_result = '1' + str_result  # 1을 붙인다
        return str_result + str_suffix  # 접미사를 붙인다

    def get_kor_amount_string_no_change(self,num_amount, ndigits_keep=5):
        """잔돈은 자르고 숫자를 자릿수 한글단위와 함께 리턴한다 """
        return self.get_kor_amount_string(num_amount, -(len(str(num_amount)) - ndigits_keep))


    async def process_challenge(self,ctx,challenge):
        data = self.challenge[str(ctx.author.id)][challenge]
        resp = data + 1
        if resp > self.challenge_max_dict[challenge]:
            return
        self.challenge[str(ctx.author.id)][challenge] = resp
        if self.challenge_max_dict[challenge] == resp:
            self.data[str(ctx.author.id)]['clear_challenge'].append(challenge)
            self.data[str(ctx.author.id)]['money'] += 500
            em = discord.Embed(
                title="인생경제시스템 도전과제 달성!",
                description=f"🎉 축하드립니다! {ctx.author.display_name}님!\n`{self.challenge_dict[challenge]}` 도전과제를 완수하셨어요! 보상으로 500원 적립해드렸습니다!",
                color=ctx.author.color
            )
            await ctx.reply(embed=em)
        dump_challenge_caching(self.challenge)
        dump_economy_caching(self.data)



    @command(name="가입")
    @register_check()
    async def register(self,ctx):
        if ctx.author.id in self.register_cooldown:
            return await ctx.reply("탈퇴한지 얼마 지나지않아 가입이 불가능해요. 탈퇴일로부터 1일후에 가입이 가능해요.")
        em = discord.Embed(
            title="인생경제시스템",
            description="현실의 경제가 최대한 제현되어있어 마치 인생게임같은 느낌을 주는 `인생경제시스템`!\n이 시스템을 이용하실려면 최초 가입이 필요해요. 가입하시겠어요?",
            color=ctx.author.color
        )
        msg = await ctx.reply(embed=em,components=[
            [Button(emoji="✅",custom_id="yes",style=ButtonStyle.green),Button(emoji="❎",custom_id="no",style=ButtonStyle.red)]
        ])
        try:
            interaction: Interaction = await self.bot.wait_for("button_click",check=lambda i:i.user.id == ctx.author.id and i.message.id == msg.id,timeout=60)
            value = interaction.custom_id
            await interaction.respond(type=6)
            await msg.disable_components()
            if value == "yes":
                self.data[ctx.author.id] = {
                    "money" : 50000,
                    "items":[],
                    "badge":[],
                    "stocks":[],
                    "clear_challenge":[]
                }
                self.challenge[ctx.author.id] = {
                    "buy_items":0,
                    "deal_items":0,
                    "first_fishing":0,
                    "first_stock":0,
                    "bankruptcy":0,
                    "first_gambling":0,
                    "item_enhancement":0,
                    "loans":0
                }
                dump_economy_caching(self.data)
                dump_challenge_caching(self.challenge)
                em.title = "인생경제시스템에 가입되신것을 축하드립니다!"
                em.description=f"{self.bot.get_emoji(893674152672776222)} 성공적으로 가입되었어요! 초기 지원금으로 50,000원을 지급해드렸습니다.\n\n이제부터 마음껏 낚시를 하고 시세를 고려하여 판매도하고 주식과 점상과 거래를 하며 부를 키워보세요!\n건투를 빕니다!"
            else:
                em.title = "인생경제시스템에 가입을 거부하셨어요."
                em.description = '가입거부를 하셨어요.. 무언가 마음에 드시지않는건가요..?😥\n다음에는 꼭 가입해주세요!'
            return await interaction.message.edit(embed=em)
        except asyncio.TimeoutError:
            await msg.disable_components()
            em.title = "인생경제시스템에 가입이 취소되었어요."
            em.description = '시간초과로 가입이 되지않았어요.'
            return await msg.edit(embed=em)

    @command(name="탈퇴")
    @unregister_check()
    async def delete_account(self,ctx):
        em = discord.Embed(
            title="인생경제시스템",
            description="탈퇴를 요청하셨어요. 탈퇴를 하시면 모든 정보가 삭제가 되며 복구할수없고 하루동안 재가입이 불가능해요.\n탈퇴하실건가요?",
            color=ctx.author.color
        )
        msg = await ctx.reply(embed=em, components=[
            [Button(emoji="✅", custom_id="yes", style=ButtonStyle.green),
             Button(emoji="❎", custom_id="no", style=ButtonStyle.red)]
        ])
        try:
            interaction: Interaction = await self.bot.wait_for("button_click", check=lambda
                i: i.user.id == ctx.author.id and i.message.id == msg.id, timeout=60)
            value = interaction.custom_id
            await interaction.respond(type=6)
            await msg.disable_components()
            if value == "yes":
                del self.data[str(ctx.author.id)]
                del self.challenge[str(ctx.author.id)]
                dump_economy_caching(self.data)
                dump_challenge_caching(self.challenge)
                em.title = "인생경제시스템에서 탈퇴처리되었어요."
                em.description = f"{self.bot.get_emoji(893674152672776222)} 성공적으로 탈퇴처리되었어요!"
                await interaction.message.edit(embed=em)
                self.register_cooldown.append(ctx.author.id)
                await asyncio.sleep(86400)
                self.register_cooldown.remove(ctx.author.id)
                return
            else:
                em.title = "인생경제시스템에서 탈퇴처리를 거부하셨어요."
                em.description = '탈퇴처리를 거부하셨어요.'
            return await interaction.message.edit(embed=em)
        except asyncio.TimeoutError:
            await msg.disable_components()
            em.title = "인생경제시스템에서 탈퇴처리가 취소되었어요."
            em.description = '시간초과로 탈퇴처리가 진행되지않았어요.'
            return await msg.edit(embed=em)

    @command(name="현황")
    @require_register()
    async def show_myinfo(self,ctx):
        data = self.data[str(ctx.author.id)]
        em = discord.Embed(
            title=f"{ctx.author.display_name}님의 경제현황!",
            color=ctx.author.color
        )
        em.add_field(
            name="자금",
            value=self.get_kor_amount_string_no_change(data['money'],7)
        )
        em.add_field(
            name="아이템",
            value="\n".join(f"> {self.item_name[j]} X {data['items'].count(j)}" for j in list(set(data['items']))) if data['items'] != [] else "소지한 아이템이 하나도 없어요."
        )
        em.add_field(
            name="배지",
            value="\n".join(data['badge']) if data['badge'] != [] else "소지한 배지가 하나도 없어요."
        )
        em.add_field(
            name="주식",
            value="\n".join(data['stocks']) if data['stocks'] != [] else "소지한 주식이 하나도 없어요."
        )
        em.add_field(
            name="완료한 도전과제",
            value="\n\n".join(f"> {self.challenge_dict[i]}" for i in data['clear_challenge'])
            if data['clear_challenge'] != []
            else "완료한 도전과제가 하나도 없어요.",
        )
        li = [
            f"> {self.challenge_dict[key]} | {value}/{self.challenge_max_dict[key]}"
            for key, value in self.challenge[str(ctx.author.id)].items()
            if value == 0
        ]

        if li == []:
            li.append("진행중인 도전과제가 없어요.")
        em.add_field(
            name="남은 도전과제",
            value="\n\n".join(li)
        )
        await ctx.reply(embed=em)

    @command(name="상점")
    @require_register()
    async def shop(self, ctx):
        em = discord.Embed(
            title="인생경제시스템 - 상점",
            description="상점에 오신것을 환영해요.\n아래에서 구매하고싶은 아이템을 골라 구매해보세요.",
            color=ctx.author.color
        )
        em.set_thumbnail(url="https://media.discordapp.net/attachments/889514827905630290/917210271494312066/shop-with-sign-we-are-open_23-2148547718.png")
        msg = await ctx.reply(embed=em, components=[
            Select(
                options=[
                    SelectOption(label="평범한 낚싯대 - 5천원",
                                 value="default_fishing_rod",
                                 emoji=self.bot.get_emoji(916994059954978877),
                                 description="평범한 낚싯대로 무난하게 낚시를 할수있다."),
                    SelectOption(label="양동이 - 2천원",
                                 value="bucket",
                                 emoji=self.bot.get_emoji(917212624997974056),
                                 description="무언가를 담을수있는 양동이, 낚시할때 유용하게 사용할 수 있을것같다."),
                    SelectOption(label="미끼용 벌레 5개 - 2천원",
                                 value="silverfish",
                                 emoji=self.bot.get_emoji(917225134220259378),
                                 description="미끼용벌레, 이 미끼를 쓰면 물고기가 몰려온다는데?")
                ]
            )
        ])
        try:
            interaction: Interaction = await self.bot.wait_for("select_option", check=lambda
                i: i.user.id == ctx.author.id and i.message.id == msg.id, timeout=60)
            value = interaction.values[0]
            await interaction.respond(type=6)
            await msg.disable_components()
            self.data[str(ctx.author.id)]['money'] -= self.item_price[value]
            if value == "silverfish":
                for i in range(5):
                    self.data[str(ctx.author.id)]['items'].append(value)
            else:
                self.data[str(ctx.author.id)]['items'].append(value)
            dump_economy_caching(self.data)
            await self.process_challenge(ctx,'buy_items')
            if self.data[str(ctx.author.id)]['money'] <= -1:
                em.description = f"{self.bot.get_emoji(893674152672776222)} 성공적으로 {self.item_name[value]}를 구매하였어요.\n자금이 모자라 자동으로 대출금으로 결제되었어요."
            else:
                em.description = f"{self.bot.get_emoji(893674152672776222)} 성공적으로 {self.item_name[value]}를 구매하였어요."
            await msg.edit(embed=em)
        except asyncio.TimeoutError:
            await msg.disable_components()
            em.description = '저기..손님.. 아무것도 안 사실거면 나가주세요..'
            await msg.edit(embed=em)

    @command(name="낚시")
    @require_register()
    @fishing_check()
    async def fishing(self,ctx):
        await self.process_challenge(ctx, 'first_fishing')
        await FishingGame(self.bot,ctx,self.data).Start()




def setup(bot):
    bot.add_cog(economy(bot))
