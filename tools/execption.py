import discord
from discord.ext import commands

from tools.database_tool import economy_caching


class PermError:
    class BlacklistedUser(commands.CheckFailure):
        def __str__(self):
            return "BlackListed User"

    class NotOwnerUser(commands.CheckFailure):
        def __str__(self):
            return "This user is not owner"

    class NotRegisterUser(commands.CheckFailure):
        def __str__(self):
            return "Not Register User"

    class AlreadyRegisterUser(commands.CheckFailure):
        def __str__(self):
            return "Already Register User"

    class NotEnoughItem(commands.CheckFailure):
        def __str__(self):
            return "Has Not Enough Item"


def register_check():
    def predicate(ctx):
        if str(ctx.author.id) in economy_caching().keys():
            raise PermError.AlreadyRegisterUser
        else:
            return True

    return commands.check(predicate)

def unregister_check():
    def predicate(ctx):
        if str(ctx.author.id) not in economy_caching().keys():
            raise PermError.NotRegisterUser
        else:
            return True

    return commands.check(predicate)

def require_register():
    def predicate(ctx):
        if str(ctx.author.id) not in economy_caching().keys():
            raise PermError.NotRegisterUser
        else:
            return True

    return commands.check(predicate)

def fishing_check():
    async def predicate(ctx):
        user_id = str(ctx.author.id)
        data = economy_caching()[user_id]['items']
        require_items = []
        if "default_fishing_rod" not in data:
            require_items.append("◎ 평범한 낚싯대")
        if "default_fishing_rod" not in data and "enchant_fishing_rod" not in data:
            require_items.append("◎ 평범한 낚싯대 혹은 강화된 낚싯대")
        if "bucket" not in data:
            require_items.append("◎ 양동이")
        if data.count('silverfish') == 0:
            require_items.append("◎ 미끼용 벌레")
        if require_items != []:
            require_items_str = '\n'.join(require_items)
            em = discord.Embed(title="아이템 부족.", description=f"<a:cross:893675768880726017> 낚시에 필요한 아이템이 부족해요.\n< 부족한 아이템 >\n{require_items_str}",
                               color=ctx.author.color)
            await ctx.reply(embed=em)
            raise PermError.NotEnoughItem
        else:
            return True

    return commands.check(predicate)

