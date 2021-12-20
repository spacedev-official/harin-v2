import json
import os
import traceback

import aiohttp
import aiosqlite
import discord
import requests
import discordSuperUtils
from discord.ext import tasks
from dotenv import load_dotenv
from py_cord_components import Button
from tools.twitch_tools import add_stream_fields, channel_statues
load_dotenv(verbose=True)
def mTwitchOauth2():
    key = ''
    try:
        key = requests.post("https://id.twitch.tv/oauth2/token?client_id=" + os.getenv('TWITCH_CLIENT_ID') +
                            "&client_secret=" + os.getenv('TWITCH_CLIENT_SECRET') + "&grant_type=client_credentials")
    except requests.exceptions.Timeout as te:
        print(te)
    except requests.exceptions.ConnectionError as ce:
        print(ce)
    except requests.exceptions.HTTPError as he:
        print(he)
    # Any Error except upper exception
    except requests.exceptions.RequestException as re:
        print(re)
    return json.loads(key.text)["access_token"]

class twloops:
    def __init__(self,bot):
        self.bot = bot
        self.access_token = mTwitchOauth2()
        self.live = {}
        self.TwitchManager = discordSuperUtils.TwitchManager(bot, os.getenv('TWITCH_CLIENT_ID'), self.access_token)

    def twloop_start(self):
        self.twitch_loop.start()

    @tasks.loop(seconds=30)
    async def twitch_loop(self):
        db = await aiosqlite.connect("db/db.sqlite")
        twitch_cur = await db.execute("SELECT * FROM twitch")
        datas = await twitch_cur.fetchall()
        headers = {'Client-Id': os.getenv("TWITCH_CLIENT_ID"),
                   'Authorization': "Bearer " + self.access_token}
        for i in datas:
            url = "https://api.twitch.tv/helix/users?login=" + i[3]
            async with aiohttp.ClientSession(headers=headers) as cs2:
                async with cs2.get(url) as res2:
                    pr2 = await res2.read()
                    sid2 = pr2.decode('utf-8')
                    answer2 = json.loads(sid2)
                    try:
                        url2 = "https://api.twitch.tv/helix/search/channels?query=" + i[3]
                        jsons = await channel_statues(url2, headers)
                        for j in jsons['data']:
                            if j['display_name'] == answer2['data'][0]['display_name']:
                                if j['is_live']:
                                    try:
                                        if self.live[j['broadcaster_login']]:
                                            pass
                                        else:
                                            self.live[j['broadcaster_login']] = True
                                            status = await self.TwitchManager.get_channel_status(
                                                [j['broadcaster_login']])
                                            stream_info = next(iter(status), None)
                                            embed = discord.Embed(
                                                title=f"<:streaming:911928055197478912> '{j['display_name']}'님이 스트리밍을 시작하였어요!",
                                                color=0x00FF00)

                                            # self.loop_stream_fields(embed, j)
                                            add_stream_fields(embed, stream_info)
                                            channel = self.bot.get_channel(i[1])
                                            await channel.send(content=f"<@&{i[2]}>", embed=embed,
                                                               components=[Button(style=5,
                                                                                  url=f"https://twitch.tv/{j['broadcaster_login']}",
                                                                                  label=f"{j['display_name']}님의 방송 보러가기",
                                                                                  emoji=self.bot.get_emoji(
                                                                                      911928055197478912))])
                                    except:
                                        self.live[j['broadcaster_login']] = False
                                else:
                                    try:
                                        if self.live[j['broadcaster_login']]:
                                            embed = discord.Embed(
                                                title=f"<:Offline:911928110381953074> '{j['display_name']}'님이 스트리밍을 종료했어요!",
                                                color=0x00FF00)
                                            embed.add_field(
                                                name="채널 방문하기",
                                                value=f"[{j['display_name']}](https://twitch.tv/{j['broadcaster_login']})",
                                                inline=False,
                                            )
                                            embed.set_image(
                                                url=j["thumbnail_url"].format(height=248, width=440))
                                            channel = self.bot.get_channel(i[1])
                                            await channel.send(embed=embed, components=[Button(style=5,
                                                                                               url=f"https://twitch.tv/{j['broadcaster_login']}",
                                                                                               label=f"{j['display_name']}님의 채널 방문하기")])
                                            self.live[j['broadcaster_login']] = False
                                    except:
                                        self.live[j['broadcaster_login']] = False
                    except:
                        pass