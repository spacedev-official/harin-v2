import json

import aiohttp
import discord


def add_stream_fields(embed: discord.Embed, stream: dict):
    embed.add_field(
        name="Title",
        value=f"[{stream['title']}](https://twitch.tv/{stream['user_name']})",
        inline=False,
    )
    embed.add_field(name="Game", value=stream["game_name"], inline=False)
    embed.add_field(name="Viewers", value=str(stream["viewer_count"]), inline=False)
    embed.add_field(
        name="Started At", value=stream["started_at"], inline=False
    )  # You can format it.
    embed.add_field(
        name="Mature",
        value="Yes" if stream["is_mature"] else "No",
        inline=False,
    )
    embed.add_field(name="Language", value=stream["language"].upper(), inline=False)
    embed.set_image(url=stream["thumbnail_url"].format(height=248, width=440))

def loop_stream_fields(embed: discord.Embed, stream: dict):
    embed.add_field(
        name="Title",
        value=f"[{stream['title']}](https://twitch.tv/{stream['broadcaster_login']})",
        inline=False,
    )
    embed.add_field(name="Game", value=stream["game_name"], inline=False)
    embed.add_field(
        name="Started At", value=stream["started_at"], inline=False
    )  # You can format it.
    embed.add_field(name="Language", value=stream["broadcaster_language"].upper(), inline=False)
    embed.set_image(url=stream["thumbnail_url"].format(height=248, width=440))

async def channel_statues(url, headers):
    async with aiohttp.ClientSession(headers=headers) as cs2:
        async with cs2.get(url) as res2:
            pr2 = await res2.read()
            sid2 = pr2.decode('utf-8')
            return json.loads(sid2)