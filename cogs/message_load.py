import discord
from discord.ext.commands import Cog
import aiosqlite
class message_load(Cog):
    "메세지 로드"
    def __init__(self, bot):
        super().__init__()
        self.bot = bot



    @Cog.listener(name="on_message")
    async def message_load(self,message:discord.Message):
        db = await aiosqlite.connect("db/db.sqlite")
        conn = await db.execute("SELECT * FROM message_load WHERE message_url = ?",(str(message.jump_url).replace('https://canary.discord.com','https://discord.com'),))
        resp = await conn.fetchone()
        if resp is not None:
            if resp[3] == "none" and resp[5] == "none":
                return
            user = await self.bot.fetch_user(resp[2])
            em = discord.Embed(
                title="메세지를 불러왔어요!",
                description=f"[[바로가기]({message.content})]",
                colour=discord.Colour.random()
            )
            em.add_field(
                name="채널",
                value=f"<#{resp[4]}>",
                inline=False
            )
            if resp[3] == "none" and resp[5] != "none":
                em.add_field(
                    name="메세지 내용",
                    value="메세지 내용이 없어요😥",
                    inline=False
                )
                em.set_image(
                    url=resp[5]
                )
            elif resp[3] != "none" and resp[5] == "none":
                em.add_field(
                    name="메세지 내용",
                    value=resp[3],
                    inline=False
                )
            else:
                em.add_field(
                    name="메세지 내용",
                    value=resp[3]
                )
                em.set_image(
                    url=resp[5]
                )
            em.set_author(
                name=user,
                icon_url=user.avatar_url
            )
            await message.reply(embed=em)
        else:
            if not bool(message.content) and not message.attachments:
                return
            msg_content = "none" if not bool(message.content) else message.content
            try:
                if message.attachments:
                    await db.execute("INSERT INTO message_load(guild, message_url, user, message_content, channel, attachment_url) VALUES (?, ?, ?, ?, ?, ?)",
                                     (message.guild.id, str(message.jump_url).replace('https://canary.discord.com','https://discord.com'), message.author.id, msg_content, message.channel.id, message.attachments[0].url))
                    await db.commit()
                if not message.attachments:
                    await db.execute(
                        "INSERT INTO message_load(guild, message_url, user, message_content, channel, attachment_url) VALUES (?, ?, ?, ?, ?, ?)",
                        (message.guild.id, str(message.jump_url).replace('https://canary.discord.com','https://discord.com'), message.author.id, msg_content, message.channel.id,
                         "none"))
                    await db.commit()
            except Exception:
                pass

    @Cog.listener(name="on_message_delete")
    async def detect_message_delete(self,message:discord.Message):
        db = await aiosqlite.connect("db/db.sqlite")
        conn = await db.execute("SELECT * FROM message_load WHERE message_url = ?",(str(message.jump_url).replace('https://canary.discord.com','https://discord.com'),))
        resp = await conn.fetchone()
        if resp is not None:
            await db.execute("DELETE FROM message_load WHERE message_url = ?",(str(message.jump_url).replace('https://canary.discord.com','https://discord.com'),))
            await db.commit()
        else:
            return

    @Cog.listener(name="on_guild_channel_delete")
    async def detect_channel_delete(self, channel: discord.GroupChannel):
        if type(channel) != discord.TextChannel:
            return
        db = await aiosqlite.connect("db/db.sqlite")
        conn = await db.execute("SELECT * FROM message_load WHERE channel = ?", (channel.id,))
        resp = await conn.fetchone()
        if resp is not None:
            await db.execute("DELETE FROM message_load WHERE channel = ?", (channel.id,))
            await db.commit()
        else:
            return

    @Cog.listener(name='on_message_edit')
    async def detect_message_edit(self,before:discord.Message, after:discord.Message):
        db = await aiosqlite.connect("db/db.sqlite")
        conn = await db.execute("SELECT * FROM message_load WHERE message_url = ?", (str(after.jump_url).replace('https://canary.discord.com','https://discord.com'),))
        resp = await conn.fetchone()
        if resp is not None:
            await db.execute("UPDATE message_load SET message_content = ? WHERE message_url = ?", (str(after.content),str(after.jump_url)))
            await db.commit()
        else:
            return

def setup(bot):
    bot.add_cog(message_load(bot))