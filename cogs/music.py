import traceback
from typing import Optional

import aiosqlite
import discord
from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager
from tools.database_tool import DataBaseTool
import datetime
from bot import MyBot
from py_cord_components import (
    Button,
    Interaction
)
# Custom Check Error
class NoVoiceConncted(commands.CheckFailure):
    pass


class BotAlreadyConncted(commands.CheckFailure):
    pass


class InvalidIndex(commands.CheckFailure):
    pass


# Custom Checks
def ensure_voice_state():
    async def predicate(ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.NoVoiceConncted()

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.BotAlreadyConncted()

        return True

    return commands.check(predicate)


# Format view count
def parse_count(count):
    original_count = count

    count = float("{:.3g}".format(count))
    magnitude = 0
    matches = ["", "K", "M", "B", "T", "Qua", "Qui"]

    while abs(count) >= 1000:
        if magnitude >= 5:
            break

        magnitude += 1
        count /= 1000.0

    try:
        return "{}{}".format(
            "{:f}".format(count).rstrip("0").rstrip("."), matches[magnitude]
        )
    except IndexError:
        return original_count


# Index converter/validator
def indexer(index: int):
    if index <= 0:
        raise InvalidIndex

    return index - 1


# Music commands
class Music(commands.Cog, discordSuperUtils.CogManager.Cog, name="Music"):
    """
    뮤직관련 소스
    """
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.music_stat = {}
        # self.client_secret = "" # spotify client_secret
        # self.client_id = "" # spotify client_id

        # Get your's from here https://developer.spotify.com/

        self.MusicManager = MusicManager(self.bot, spotify_support=False)

        # self.MusicManager = MusicManager(bot,
        #                                  client_id=self.client_id,
        #                                  client_secret=self.client_secret,
        #                                  spotify_support=True)

        # If using spotify support use this instead ^^^

        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()

    async def queue(self, ctx):
        try:
            if queue := await self.MusicManager.get_queue(ctx):
                if len(queue.queue) == 1:
                    return ["대기열 비어있음"]
                return [
                    f"{x.title} Requester: {x.requester.display_name if x.requester else 'Autoplay'}"for x in queue.queue
                ]

        except discordSuperUtils.QueueEmpty:
            return ["대기열 비어있음"]

    # Play function
    async def play_cmd(self, ctx, query):
        db = await aiosqlite.connect("db/db.db")
        conn = await db.execute("SELECT * FROM music WHERE guild = ?", (ctx.guild.id,))
        resp = await conn.fetchone()
        async with ctx.typing():
            player = await self.MusicManager.create_player(query, ctx.author)

        if player:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                await self.MusicManager.join(ctx)

            await self.MusicManager.queue_add(players=player, ctx=ctx)

            if not await self.MusicManager.play(ctx):
                queue_resp = await self.queue(ctx)
                try:
                    queue_res = "\n".join(queue_resp)
                except:
                    queue_res = "대기열 없음"
                msg = await ctx.channel.fetch_message(resp[2])
                await msg.edit(
                    content=f'** **\n**__대기열 목록__**:\n{queue_res}',
                    embed=msg.embeds[0],
                )
                await ctx.send(f"`{player[0].title}`(을)를 대기열에 추가했어요.",delete_after=5)
            else:
                await ctx.send("✅",delete_after=5)
        else:
            await ctx.send("Query not found.",delete_after=5)

    def default_music_embed(self):
        em = discord.Embed(
            title="현재 아무 곡도 재생 중이지 않아요.",
            description="[초대](https://koreanbots.dev/bots/893841721958469703/invite) | [하트주기](https://koreanbots.dev/bots/893841721958469703/vote) | [지원서버](https://discord.gg/294KSUxcz2) | [깃허브](https://github.com/spacedev-official/harin)",
            colour=discord.Colour.dark_purple()
        )
        em.set_image(url="https://media.discordapp.net/attachments/889514827905630290/914160536709636096/9dac48ccd1fc3509.png")
        em.set_footer(text="아래 버튼을 통해 조작하실 수 있어요!")
        em.add_field(name="루프모드",value="-",inline=False)
        em.add_field(name="셔플모드",value="-",inline=False)
        return em

    async def set_default(self,ctx=None):
        db = await aiosqlite.connect("db/db.db")
        conn = await db.execute("SELECT * FROM music WHERE guild = ?", (ctx.guild.id,))
        resp = await conn.fetchone()
        msg = await (self.bot.get_channel(resp[1])).fetch_message(resp[2])
        await msg.edit(
            content="** **\n**__대기열 목록__**:\n음성채널에 접속한뒤 이 채널에 제목이나 URL을 입력해주세요.",
            embed=self.default_music_embed(),
            components=[
                [
                    Button(emoji="⏯", custom_id="music_pr"),
                    Button(emoji="⏹", custom_id="music_stop"),
                    Button(emoji="⏮", custom_id="music_previous"),
                    Button(emoji="⏭", custom_id="music_skip"),
                    Button(emoji="🔀", custom_id="music_shuffle")
                ],
                [
                    Button(emoji="🔉", custom_id="music_volumedown"),
                    Button(label="10%", emoji="🔈", disabled=True),
                    Button(emoji="🔊", custom_id="music_volumeup"),
                    Button(emoji="🔁", custom_id="music_queueloop"),
                    Button(emoji="🔂", custom_id="music_oneloop")
                ],
                [
                    Button(emoji=self.bot.get_emoji(914490775742586960), custom_id="music_auto"),
                    Button(emoji="📥", custom_id="music_join"),
                    Button(emoji="❎", custom_id="music_cancel", style=4)
                ]
            ]
        )


    # DSU Error handler
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        # sourcery skip: remove-redundant-fstring
        errors = {
            discordSuperUtils.NotPlaying: "지금 아무 음악도 재생중이지 않아요...",
            discordSuperUtils.NotConnected: f"저는 보이스채널에 접속해있지않아요!",
            discordSuperUtils.NotPaused: "음악이 멈추어져있지않아요!",
            discordSuperUtils.QueueEmpty: "대기열이 비어있어요!",
            discordSuperUtils.AlreadyConnected: "이미 보이스채널에 접속해있어요!",
            discordSuperUtils.SkipError: "스킵할 곡이 없어요!",
            discordSuperUtils.UserNotConnected: "요청자님이 음성채널에 접속해있지않아요!",
            discordSuperUtils.InvalidSkipIndex: "스킵될 값을 사용할수없어요!",
        }

        for error_type, response in errors.items():
            if isinstance(error, error_type):
                await ctx.send(response,delete_after=5)
                break

        print("unexpected error")
        raise error


    # On music play event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):  # This returns a player object
        db = await aiosqlite.connect("db/db.db")
        conn = await db.execute("SELECT * FROM music WHERE guild = ?", (ctx.guild.id,))
        resp = await conn.fetchone()
        # Extracting useful data from player object
        self.music_stat[ctx.guild.id] = "resume"
        thumbnail = player.data["videoDetails"]["thumbnail"]["thumbnails"][-1]["url"]
        uploader = player.data["videoDetails"]["author"]
        requester = player.requester.mention if player.requester else "Autoplay"

        embed = discord.Embed(
            color=discord.Color.from_rgb(255, 255, 0),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            description="[초대](https://koreanbots.dev/bots/893841721958469703/invite) | [하트주기](https://koreanbots.dev/bots/893841721958469703/vote) | [지원서버](https://discord.gg/294KSUxcz2) | [깃허브](https://github.com/spacedev-official/harin)",
        )
        embed.set_author(name=f"{player.title} upload by {uploader}",url=player.url)
        embed.add_field(name="Requested by", value=requester)
        loop = (await self.MusicManager.get_queue(ctx)).loop
        if loop == discordSuperUtils.Loops.LOOP:
            loop_status = "<:activ:896255701641474068> 단일곡 루프."
        elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
            loop_status = "<:activ:896255701641474068> 대기열 루프."
        else:
            loop_status = "-"
        embed.add_field(name="루프모드", value=loop_status)
        shuffle = (await self.MusicManager.get_queue(ctx)).shuffle
        shuffle_status = "<:activ:896255701641474068>" if shuffle else "-"
        embed.add_field(name="셔플모드", value=shuffle_status)
        embed.set_image(url=thumbnail)
        queue_resp = await self.queue(ctx)
        queue_res = "\n".join(queue_resp)
        await (
            await ctx.channel.fetch_message(resp[2])
        ).edit(
            content=f'** **\n**__대기열 목록__**:\n{queue_res}',
            embed=embed,
        )

    # On queue end event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_queue_end(self, ctx):
        print(f"The queue has ended in {ctx}")
        await self.set_default(ctx)
        self.music_stat[ctx.guild.id] = None
        # You could wait and check activity, etc...

    # On inactivity disconnect event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_inactivity_disconnect(self, ctx):
        print(f"I have left {ctx} due to inactivity")


    async def pause_resume(self, ctx):
        if self.music_stat[ctx.guild.id] == "pause":
            if await self.MusicManager.resume(ctx):
                self.music_stat[ctx.guild.id] = "resume"
                return {"type":True,"stat":"resume"}
        elif await self.MusicManager.pause(ctx):
            self.music_stat[ctx.guild.id] = "pause"
            return {"type":True,"stat":"pause"}


    async def volume(self, ctx, interaction:Interaction,type):
        if current_volume := await self.MusicManager.volume(ctx):
            if type == "down":
                volume = int(current_volume) - 5
                if int(current_volume) == 5:
                    return await interaction.send(content="최소 볼륨으로 더이상 낮출수없어요.",ephemeral=False,delete_after=5)
            else:
                volume = int(current_volume) + 5
            if await self.MusicManager.volume(ctx, volume):
                await interaction.edit_origin(
                    components=[
                                       [
                                            Button(emoji="⏯",custom_id="music_pr"),
                                            Button(emoji="⏹", custom_id="music_stop"),
                                            Button(emoji="⏮", custom_id="music_previous"),
                                            Button(emoji="⏭", custom_id="music_skip"),
                                            Button(emoji="🔀", custom_id="music_shuffle")
                                       ],
                                       [
                                           Button(emoji="🔉", custom_id="music_volumedown"),
                                           Button(label=f"{volume}%",emoji="🔈", custom_id="music_volumestat",disabled=True),
                                           Button(emoji="🔊", custom_id="music_volumeup"),
                                           Button(emoji="🔁", custom_id="music_queueloop"),
                                           Button(emoji="🔂", custom_id="music_oneloop")
                                       ],
                                       [
                                           Button(emoji=self.bot.get_emoji(914490775742586960), custom_id="music_auto"),
                                           Button(emoji="📥", custom_id="music_join"),
                                           Button(emoji="❎", custom_id="music_cancel",style=4)
                                       ]
                                   ]
                )
            await interaction.send(content=f"다음 볼륨으로 설정했어요 - {current_volume}%",ephemeral=False,delete_after=5)

    async def loop(self, ctx,interaction:Interaction):
        is_loop = await self.MusicManager.loop(ctx)

        if is_loop is not None:
            await interaction.send(content=f"단일곡 루프모드를 {'<:activ:896255701641474068> 활성화' if is_loop else '<:disactiv:896388083816218654> 비활성화'}했어요.\n임베드에 반영되기까지 시간이 조금 걸려요.",ephemeral=False,delete_after=5)

    async def queueloop(self, ctx,interaction:Interaction):
        is_loop = await self.MusicManager.queueloop(ctx)

        if is_loop is not None:
            await interaction.send(content=f"대기열 루프모드를 {'<:activ:896255701641474068> 활성화' if is_loop else '<:disactiv:896388083816218654> 비활성화'}했어요.\n임베드에 반영되기까지 시간이 조금 걸려요.",ephemeral=False,delete_after=5)

    async def skip(self, ctx,interaction:Interaction, index: int = None):
        if queue := (await self.MusicManager.get_queue(ctx)):

            requester = (await self.MusicManager.now_playing(ctx)).requester

            # Checking if the song is autoplayed
            if requester is None:
                await interaction.send(content="자동재생중인 음악을 스킵했어요.",ephemeral=False,delete_after=5)
                await self.MusicManager.skip(ctx, index)
            # Checking if queue is empty and autoplay is disabled
            if not queue.queue and not queue.autoplay:
                await interaction.send(content="대기열의 마지막곡이여서 스킵할수없어요.",ephemeral=False,delete_after=5)

            else:
                skipped_player = await self.MusicManager.skip(ctx, index)

                await interaction.send(content="성공적으로 스킵했어요!",ephemeral=False,delete_after=5)
                if not skipped_player.requester:
                    await ctx.send("Autoplaying next song.")
    async def previous(self, ctx,interaction:Interaction, index: int = None):

        if previous_player := await self.MusicManager.previous(
                ctx, index, no_autoplay=True
        ):
            await interaction.send(content=f"`{previous_player[0].title}`로 되돌렸어요!",ephemeral=False,delete_after=5)

    async def autoplay(self, ctx,interaction:Interaction):
        is_autoplay = await self.MusicManager.autoplay(ctx)

        if is_autoplay is not None:
            await interaction.send(content=f"대기열 자동재생 모드를 {'<:activ:896255701641474068> 활성화' if is_autoplay else '<:disactiv:896388083816218654> 비활성화'}했어요.\n임베드에 반영되기까지 시간이 조금 걸려요.",ephemeral=False,delete_after=5)

    async def shuffle(self, ctx,interaction:Interaction):
        is_shuffle = await self.MusicManager.shuffle(ctx)

        if is_shuffle is not None:
            await interaction.send(content=f"셔플모드를 {'<:activ:896255701641474068> 활성화' if is_shuffle else '<:disactiv:896388083816218654> 비활성화'}했어요.\n임베드에 반영되기까지 시간이 조금 걸려요.",ephemeral=False,delete_after=5)

    async def join(self, interaction:Interaction):
        try:
            user = self.bot.get_guild(interaction.guild_id).get_member(interaction.user.id)
            await user.voice.channel.connect()
            await interaction.send("정상적으로 채널에 접속했어요.",ephemeral=False,delete_after=5)
        except:
            print(str(traceback.format_exc()))
            await interaction.send("이미 접속된 상태에요.",ephemeral=False,delete_after=5)

    # async def playlists(self, interaction:Interaction):
    #     user = interaction.user
    #     user_playlists = await MusicManager.get_user_playlists(user)
    #
    #     if not user_playlists:
    #         await interaction.send(f"{user.mention}님의 즐겨찾기목록을 찾지 못했어요.",ephemeral=False,delete_after=5)
    #         return
    #
    #     formatted_playlists = [
    #         f"""**Title:** '{user_playlist.playlist.title}'
    #         Total Songs: {len(user_playlist.playlist.songs)}
    #         ID: `{user_playlist.id}`"""
    #         for user_playlist in user_playlists
    #     ]
    #
    #     embeds = discordSuperUtils.generate_embeds(
    #         formatted_playlists,
    #         f"{user}님의 즐겨찾기목록",
    #         f"{user.mention}님의 즐겨찾기 목록을 보여드려요.",
    #         15,
    #         string_format="{}",
    #     )
    #
    #     for embed in embeds:
    #         embed.timestamp = datetime.datetime.utcnow()
    #
    #     try:
    #         await user.send(embed=embeds)
    #     except discord.Forbidden:
    #         await interaction.respond(content="개인DM이 차단되어있어 보내지 못했어요. DM차단을 해제해주세요.")

    # async def add(self, ctx, interaction:Interaction):
    #     if player := await self.MusicManager.now_playing(ctx):
    #         added_playlist = await MusicManager.add_playlist(ctx.author, player.url)
    #
    #         if not added_playlist:
    #             await interaction.respond("URL을 찾지못했어요.")
    #             return
    #
    #         await interaction.respond(f"다음 ID로 즐겨찾기를 등록했어요. `{added_playlist.id}`")



    topic = """
⏯ 일시정지/이어재생
⏹ 정지.
⏮ 이전곡.
⏭ 스킵.
🔁 대기열 루프모드.
🔂 단일곡 루프모드.
🔀 셔플모드.
❎ 대기열 초기화 및 음성채널 접속해제.
🔉 볼륨 다운.
🔊 볼륨 업.
<:robot:914490775742586960> 대기열 자동재생.
📥 봇 접속.
    """


    @commands.command(name="msetup")
    async def msetup(self,ctx):
        db = await aiosqlite.connect("db/db.db")
        music_check = await DataBaseTool(db).check_db_music(ctx.guild)
        if not music_check:
            return await ctx.reply("❎ 이미 설정되어있는것같아요!")
        channel = await ctx.guild.create_text_channel(name="music-test", topic=self.topic)
        await channel.send(
            "https://media.discordapp.net/attachments/889514827905630290/896359450544308244/37cae031dc5a6c40.png")
        msg = await channel.send(content="** **\n**__대기열 목록__**:\n음성채널에 접속한뒤 이 채널에 제목이나 URL을 입력해주세요.",
                                 embed=self.default_music_embed(),
                                 components=[
                                     [
                                         Button(emoji="⏯", custom_id="music_pr"),
                                         Button(emoji="⏹", custom_id="music_stop"),
                                         Button(emoji="⏮", custom_id="music_previous"),
                                         Button(emoji="⏭", custom_id="music_skip"),
                                         Button(emoji="🔀", custom_id="music_shuffle")
                                     ],
                                     [
                                         Button(emoji="🔉", custom_id="music_volumedown"),
                                         Button(label="10%", emoji="🔈", disabled=True),
                                         Button(emoji="🔊", custom_id="music_volumeup"),
                                         Button(emoji="🔁", custom_id="music_queueloop"),
                                         Button(emoji="🔂", custom_id="music_oneloop")
                                     ],
                                     [
                                         Button(emoji=self.bot.get_emoji(914490775742586960), custom_id="music_auto"),
                                         Button(emoji="📥", custom_id="music_join"),
                                         Button(emoji="❎", custom_id="music_cancel", style=4)
                                     ]
                                 ]
                                 )
        db = await aiosqlite.connect("db/db.db")
        await DataBaseTool(db).add_music_data(ctx.guild,channel,msg)
        await ctx.send(
            f"<a:check:893674152672776222> 성공적으로 뮤직채널({channel.mention})을 만들었어요!\n해당 채널의 이름과 위치는 마음껏 커스터마이징이 가능하답니다!")

    @commands.Cog.listener("on_message")
    async def music_message(self,message):
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        db = await aiosqlite.connect("db/db.db")
        conn = await db.execute("SELECT * FROM music WHERE guild = ?",(message.guild.id,))
        resp = await conn.fetchone()
        if not resp == None:
            if message.channel.id == resp[1]:
                await message.delete()
                await Music.play_cmd(self, ctx, message.content)


    @commands.Cog.listener(name="on_button_click")
    async def music_button_control(self,interaction:Interaction):
        ctx = await self.bot.get_context(interaction.message)
        db = await aiosqlite.connect("db/db.db")
        conn = await db.execute("SELECT * FROM music WHERE guild = ?", (interaction.guild_id,))
        resp = await conn.fetchone()
        if interaction.custom_id.startswith("music_") and interaction.message.id == resp[2]:
            if not interaction.user.voice or not interaction.user.voice.channel:
                return await interaction.send("음성채널에 접속해있지않아요!",ephemeral=False,delete_after=5)
            if interaction.custom_id == "music_cancel":
                if await self.MusicManager.leave(ctx):
                    await self.set_default(ctx)
                    await interaction.send(content="대기열을 초기화하고 접속을 해제했어요!",ephemeral=False,delete_after=5)
            elif interaction.custom_id == "music_pr":
                resp = await self.pause_resume(ctx)
                if resp['type']:
                    if resp['stat'] == "resume":
                        await interaction.send(content="이어서 재생할게요!",ephemeral=False,delete_after=5)
                    else:
                        await interaction.send(content="음악을 일시정지했어요.",ephemeral=False,delete_after=5)
            elif interaction.custom_id == "music_stop":
                await self.MusicManager.cleanup(voice_client=None, guild=ctx.guild)
                ctx.voice_client.stop()
                await interaction.send("음악을 정지했어요.",ephemeral=False,delete_after=5)
            elif interaction.custom_id == "music_skip":
                await self.skip(ctx,interaction)
            elif interaction.custom_id == "music_shuffle":
                await self.shuffle(ctx,interaction)
            elif interaction.custom_id == "music_volumedown":
                await self.volume(ctx,interaction,type="down")
            elif interaction.custom_id == "music_volumeup":
                await self.volume(ctx,interaction,type="up")
            elif interaction.custom_id == "music_queueloop":
                await self.queueloop(ctx,interaction)
            elif interaction.custom_id == "music_oneloop":
                await self.loop(ctx,interaction)
            elif interaction.custom_id == "music_previous":
                await self.previous(ctx,interaction)
            elif interaction.custom_id == "music_auto":
                await self.autoplay(ctx,interaction)
            elif interaction.custom_id == "music_join":
                await self.join(interaction)



def setup(bot):
    bot.add_cog(Music(bot))