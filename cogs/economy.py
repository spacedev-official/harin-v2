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
from tools.database_tool import economy_caching,dump_economy_caching
from tools.execption import PermError
from bot import MyBot


#economy_cach = economy_caching()

def register_check():
    async def predicate(ctx):
        if str(ctx.author.id) in economy_caching().keys():
            em = discord.Embed(title="이미 가입되어있음.",description="<a:cross:893675768880726017> 이미 가입되어있어요.",color=ctx.author.color)
            await ctx.reply(embed=em)
            raise PermError.AlreadyRegisterUser
        else:
            return True

    return commands.check(predicate)

def unregister_check():
    async def predicate(ctx):
        if str(ctx.author.id) not in economy_caching().keys():
            em = discord.Embed(title="가입되어있지않음.",description="<a:cross:893675768880726017> 가입되어있지않아요.",color=ctx.author.color)
            await ctx.reply(embed=em)
            raise PermError.NotRegisterUser
        else:
            return True

    return commands.check(predicate)

def require_register():
    async def predicate(ctx):
        if str(ctx.author.id) not in economy_caching().keys():
            em = discord.Embed(title="가입되어있지않음.",description="<a:cross:893675768880726017> 가입되어있지않아요.",color=ctx.author.color)
            await ctx.reply(embed=em)
            raise PermError.NotRegisterUser
        else:
            return True

    return commands.check(predicate)

class economy(Cog):
    def __init__(self, bot:MyBot):
        self.bot = bot
        self.data = economy_caching()
        self.register_cooldown = []
        super().__init__()

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
                dump_economy_caching(self.data)
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
                dump_economy_caching(self.data)
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
            value="\n".join(data) if data['items'] != [] else "소지한 아이템이 하나도 없어요.",
        )
        em.add_field(
            name="배지",
            value="\n".join(data) if data['badge'] != [] else "소지한 배지가 하나도 없어요."
        )
        em.add_field(
            name="주식",
            value="\n".join(data) if data['stocks'] != [] else "소지한 주식이 하나도 없어요."
        )
        em.add_field(
            name="완료한 도전과제",
            value="\n".join(data) if data['clear_challenge'] != [] else "완료한 도전과제가 하나도 없어요."
        )
        await ctx.reply(embed=em)

def setup(bot):
    bot.add_cog(economy(bot))
