from typing import Optional

import discord
from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager

import datetime
from bot import MyBot
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
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
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.skip_votes = {}  # Skip vote counter dictionary
        self.music_channel = {}
        self.channel = 0
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
        async with ctx.typing():
            player = await self.MusicManager.create_player(query, ctx.author)

        if player:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                await self.MusicManager.join(ctx)

            await self.MusicManager.queue_add(players=player, ctx=ctx)

            if not await self.MusicManager.play(ctx):
                queue_resp = await self.queue(ctx)
                queue_res = "\n".join(queue_resp)
                msg = await ctx.channel.fetch_message(self.music_channel[ctx.channel.id])
                await msg.edit(
                    content=f'** **\n**__대기열 목록__**:\n{queue_res}',
                    embed=msg.embeds[0],
                )
                await ctx.send(f"`{player[0].title}`(을)를 대기열에 추가했어요.",delete_after=5)
            else:
                await ctx.send("✅",delete_after=5)
        else:
            await ctx.send("Query not found.",delete_after=5)

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
                return

        print("unexpected error")
        raise error


    # On music play event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):  # This returns a player object

        # Extracting useful data from player object
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
        embed.set_image(url=thumbnail)
        queue_resp = await self.queue(ctx)
        queue_res = "\n".join(queue_resp)
        await (
            await ctx.channel.fetch_message(self.music_channel[ctx.channel.id])
        ).edit(
            content=f'** **\n**__대기열 목록__**:\n{queue_res}',
            embed=embed,
        )

        # Clearing skip votes for each song
        if self.skip_votes.get(ctx.guild.id):
            self.skip_votes.pop(ctx.guild.id)

    # On queue end event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_queue_end(self, ctx):
        print(f"The queue has ended in {ctx}")
        await ctx.send("Queue ended")
        # You could wait and check activity, etc...

    # On inactivity disconnect event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_inactivity_disconnect(self, ctx):
        print(f"I have left {ctx} due to inactivity")
        await ctx.send("Left Music Channel due to inactivity")


    # You can add this to your existing on_ready function

    # Leave command
    """async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.send("👋",delete_after=5)
            # Or
            # await message.add_reaction("👋")"""


    # Pause command
    @commands.command()
    async def pause(self, ctx):
        if await self.MusicManager.pause(ctx):
            await ctx.send("Paused")

    # Resume command
    @commands.command()
    async def resume(self, ctx):
        if await self.MusicManager.resume(ctx):
            await ctx.send("Resumed")

    # Volume command
    @commands.command()
    async def volume(self, ctx, volume: int = None):
        if volume:
            if volume < 0:
                await ctx.send("Invalid volume")
                return

            if await self.MusicManager.volume(ctx, volume):
                await ctx.send(f"Volume set to {volume}%")
                return

        if current_volume := await self.MusicManager.volume(ctx):
            await ctx.send(f"Current volume: {current_volume}")

    # Song loop command
    @commands.command()
    async def loop(self, ctx):
        is_loop = await self.MusicManager.loop(ctx)

        if is_loop is not None:
            await ctx.send(f"Looping {'Enabled' if is_loop else 'Disabled'}")

    # Queue loop command
    @commands.command()
    async def queueloop(self, ctx):
        is_loop = await self.MusicManager.queueloop(ctx)

        if is_loop is not None:
            await ctx.send(f"Queue Looping {'Enabled' if is_loop else 'Disabled'}")

    # Stop command
    @commands.command()
    async def stop(self, ctx):
        await self.MusicManager.cleanup(voice_client=None, guild=ctx.guild)
        ctx.voice_client.stop()
        await ctx.send("⏹️")

    # Skip command with voting
    @commands.command()
    async def skip(self, ctx, index: int = None):
        if queue := (await self.MusicManager.get_queue(ctx)):

            requester = (await self.MusicManager.now_playing(ctx)).requester

            # Checking if the song is autoplayed
            if requester is None:
                await ctx.send("Skipped autoplayed song")
                await self.MusicManager.skip(ctx, index)

            # Checking if queue is empty and autoplay is disabled
            elif not queue.queue and not queue.autoplay:
                await ctx.send("Can't skip the last song of queue.")

            else:
                # Checking if guild id list is in skip votes dictionary
                if not self.skip_votes.get(ctx.guild.id):
                    self.skip_votes[ctx.guild.id] = []

                # Checking the voter
                voter = ctx.author

                # If voter is requester than skips automatically
                if voter == (await self.MusicManager.now_playing(ctx)).requester:
                    skipped_player = await self.MusicManager.skip(ctx, index)

                    await ctx.send("Skipped by requester")

                    if not skipped_player.requester:
                        await ctx.send("Autoplaying next song.")

                    # clearing the skip votes
                    self.skip_votes.pop(ctx.guild.id)

                # Voting
                elif (
                    voter.id not in self.skip_votes[ctx.guild.id]
                ):  # Checking if someone already voted
                    # Adding the voter id to skip votes
                    self.skip_votes[ctx.guild.id].append(voter.id)

                    # Calculating total votes
                    total_votes = len(self.skip_votes[ctx.guild.id])

                    # If total votes >=3 then it will skip
                    if total_votes >= 3:
                        skipped_player = await self.MusicManager.skip(ctx, index)

                        await ctx.send("Skipped on vote")

                        if not skipped_player.requester:
                            await ctx.send("Autoplaying next song.")

                        # Clearing skip votes of the guild
                        self.skip_votes.pop(ctx.guild.id)

                    # Shows voting status
                    else:
                        await ctx.send(
                            f"Skip vote added, currently at **{total_votes}/3**"
                        )

                # If someone uses vote command twice
                else:
                    await ctx.send("You have already voted to skip this song.")


    # Shuffle command
    @commands.command()
    async def shuffle(self, ctx):
        is_shuffle = await self.MusicManager.shuffle(ctx)

        if is_shuffle is not None:
            await ctx.send(f"Shuffle toggled to {is_shuffle}")


# Bot error handler
    """@bot.event
    async def on_command_error(self,ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Invalid command.")

        elif isinstance(error, commands.NoVoiceConncted):
            await ctx.send("You are not connected to any voice channel.")

        elif isinstance(error, commands.BotAlreadyConncted):
            await ctx.send(
                f"Bot is already in a voice channel <#{ctx.voice_client.channel.id}>"
            )

        elif isinstance(error, InvalidIndex):
            await ctx.send(f"Invalid Index")

        else:
            print("unexpected err")
            raise error"""
    topic = """
⏯ 일시정지/이어재생
⏹ 정지.
⏭ 스킵.
🔁 루프모드.
🔀 셔플모드.
❌ 대기열 초기화 및 음성채널 접속해제.
🔉 볼륨 다운
🔊 볼륨 업
    """
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
    @commands.Cog.listener("on_message")
    async def music_message(self,message):
        if message.author.bot:
            return
        if message.author.id != 281566165699002379:
            return
        ctx = await self.bot.get_context(message)
        if message.content == "~setup":
            channel = await message.guild.create_text_channel(name="music-test",topic=self.topic)
            await channel.send("https://media.discordapp.net/attachments/889514827905630290/896359450544308244/37cae031dc5a6c40.png")
            msg = await channel.send(content="** **\n**__대기열 목록__**:\n음성채널에 접속한뒤 이 채널에 제목이나 URL을 입력해주세요.",
                               embed=self.default_music_embed(),
                               components=[
                                   [
                                        Button(emoji="⏯",custom_id="music_pr"),
                                        Button(emoji="⏹", custom_id="music_stop"),
                                        Button(emoji="⏭", custom_id="music_skip"),
                                        Button(emoji="🔁", custom_id="music_loop"),
                                        Button(emoji="🔀", custom_id="music_shuffle")
                                   ],
                                   [
                                       Button(emoji="🔉", custom_id="music_volumedown"),
                                       Button(label="50%",emoji="🔈", custom_id="music_volumestat",disabled=True),
                                       Button(emoji="🔊", custom_id="music_volumeup")
                                   ],
                                   [
                                       Button(emoji="❌", custom_id="music_cancel")
                                   ]
                               ]
                               )
            self.music_channel[channel.id] = msg.id
            self.channel = channel.id
            await message.channel.send(f"<a:check:893674152672776222> 성공적으로 뮤직채널({channel.mention})을 만들었어요!\n해당 채널의 이름과 위치는 마음껏 커스터마이징이 가능하답니다!")
        if message.channel.id == self.channel:
            await Music.play_cmd(self, ctx, message.content)
            await message.delete()

    @commands.Cog.listener(name="on_button_click")
    async def music_button_control(self,interaction:Interaction):
        ctx = await self.bot.get_context(interaction.message)
        if interaction.custom_id == "music_cancel":
            await (
                await interaction.channel.fetch_message(
                    self.music_channel[interaction.channel_id]
                )
            ).edit(
                content='** **\n**__대기열 목록__**:\n음성채널에 접속한뒤 이 채널에 제목이나 URL을 입력해주세요.',
                embed=self.default_music_embed(),
            )
            if await self.MusicManager.leave(ctx):
                await interaction.send(content="대기열을 초기화하고 접속을 해제했어요!",ephemeral=False,delete_after=5)
def setup(bot):
    bot.add_cog(Music(bot))