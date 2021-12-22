import asyncio
import json
import os
import re

import aiohttp
import discord
import aiosqlite
import pyyoutube
from discord.ext import tasks
from dotenv import load_dotenv
from py_cord_components import Button

from tools.youtube_tools import get_videos, crawl

load_dotenv(verbose=True)


class ytloops:
    def __init__(self, bot):
        self.bot = bot
        self.youtube_cache = {}

    def ytloop_start(self):
        self.checkforvideos.start()

    @tasks.loop(seconds=30)
    async def checkforvideos(self):
        db = await aiosqlite.connect('db/db.sqlite')
        cur = await db.execute("SELECT * FROM youtube")
        data = await cur.fetchall()
        async with aiohttp.ClientSession() as session:
            api = pyyoutube.Api(session=session,api_key=os.getenv("YT_TOKEN"))
            for i in data:
                channel = f"https://www.youtube.com/channel/{i[3]}"

                html = await crawl(channel)
                resp = await get_videos(i[3])

                try:
                    vid = re.search('(?<="videoId":").*?(?=")', html).group()
                except:
                    continue

                try:
                    if self.youtube_cache[i[3]] != vid:
                        channel_res = await api.get_channel_info(channel_id=i[3])
                        em = discord.Embed(
                            title=f"'{channel_res.items[0].snippet.title}'님이 새로운 영상을 업로드했어요!",
                            colour=discord.Colour.random()
                        )
                        if not channel_res.items[0].statistics.hiddenSubscriberCount:
                            subs = "비공개"
                        else:
                            subs = f"`{channel_res.items[0].statistics.subscriberCount}`명"
                        em.add_field(
                            name="제목",
                            value=resp[0].snippet.title
                        )
                        em.add_field(
                            name="구독자 수",
                            value=subs
                        )
                        em.add_field(
                            name="모든 영상 수",
                            value=f"`{channel_res.items[0].statistics.videoCount}`개"
                        )
                        em.add_field(
                            name="총 조회 수",
                            value=f"`{channel_res.items[0].statistics.viewCount}`회"
                        )
                        em.set_image(url=channel_res.items[0].snippet.thumbnails.high)
                        await self.bot.get_channel(i[1]).send(
                            content=f"<@&{i[2]}>",
                            embed=em,
                            components=[
                                Button(
                                    style=5,
                                    url=f"https://youtu.be/{resp[0].id}",
                                    label='영상 보러가기',
                                )
                            ],
                        )
                        self.youtube_cache[i[3]] = resp[0].id
                except:
                    self.youtube_cache[i[3]] = resp[0].id
                await asyncio.sleep(5)
