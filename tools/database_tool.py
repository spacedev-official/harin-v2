import json

import aiosqlite
import discord

def temporary_caching():
    with open("tools/temporary_json/temporary.json", "r") as json_file:
        return json.load(json_file)

def dump_temporary_caching(data):
    with open("tools/temporary_json/temporary.json", 'w') as outfile:
        json.dump(data, outfile, indent=4)
        return True


def economy_caching():
    with open("tools/economy_json/economy.json", "r") as json_file:
        return json.load(json_file)

def dump_economy_caching(data):
    with open("tools/economy_json/economy.json", 'w') as outfile:
        return json.dump(data, outfile, indent=4)


def challenge_caching():
    with open("tools/economy_json/challenge.json", "r") as json_file:
        return json.load(json_file)

def dump_challenge_caching(data):
    with open("tools/economy_json/challenge.json", 'w') as outfile:
        return json.dump(data, outfile, indent=4)


class DataBaseTool:
    def __init__(self,db):
        self.db = db
        super(DataBaseTool, self).__init__()

    async def check_db_music(self, guild:discord.Guild):
        conn = await self.db.execute("SELECT * FROM music WHERE guild = ?", (guild.id,))
        cur = await conn.fetchone()
        if cur == None:
            return True
        return False

    async def check_db_temporary(self, guild:discord.Guild):
        conn = await self.db.execute("SELECT * FROM temporary WHERE guild = ?", (guild.id,))
        cur = await conn.fetchone()
        if cur == None:
            return True
        return False

    async def add_music_data(self,guild:discord.Guild,channel:discord.TextChannel,message:discord.Message):
        ch_ = await self.check_db_music(guild)
        if not ch_:
            return
        await self.db.execute("INSERT INTO music(guild, channel, message) VALUES (?, ?, ?)",(guild.id, channel.id, message.id))
        await self.db.commit()

    async def add_temporary_data(self,guild:discord.Guild,voice_channel:discord.TextChannel,category_channel:discord.CategoryChannel):
        ch_ = await self.check_db_temporary(guild)
        if not ch_:
            return
        await self.db.execute("INSERT INTO temporary(guild, channel, category) VALUES (?, ?, ?)",(guild.id, voice_channel.id, category_channel.id))
        await self.db.commit()
