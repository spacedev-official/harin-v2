import os

import aiohttp
import pyyoutube
from dotenv import load_dotenv
from youtubesearchpython import ResultMode,ChannelSearch,ChannelsSearch

load_dotenv(verbose=True)
def channelssearch(name,limit):
    channelsSearch = ChannelsSearch(name, limit=limit, region="KO")
    res: dict = channelsSearch.result()
    return res

async def get_videos(channel_id):
    async with aiohttp.ClientSession() as session:
        api = pyyoutube.Api(session=session,api_key=os.getenv("YT_TOKEN"))
        channel_res = await api.get_channel_info(channel_id=channel_id)

        playlist_id = channel_res.items[0].contentDetails.relatedPlaylists.uploads

        playlist_item_res = await api.get_playlist_items(
            playlist_id=playlist_id, count=10, limit=6
        )

        videos = []
        for item in playlist_item_res.items:
            video_id = item.contentDetails.videoId
            video_res = await api.get_video_by_id(video_id=video_id)
            videos.extend(video_res.items)
        return videos

async def crawl(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url + "/videos") as resp:
            html = await resp.text(encoding='utf-8')
            await session.close()
            return html