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

    # Play function
    async def play_cmd(self, ctx, query):
        async with ctx.typing():
            player = await self.MusicManager.create_player(query, ctx.author)

        if player:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                await self.MusicManager.join(ctx)

            await self.MusicManager.queue_add(players=player, ctx=ctx)

            if not await self.MusicManager.play(ctx):
                await ctx.send(f"Added {player[0].title} to song queue.")
            else:
                await ctx.send("✅")
        else:
            await ctx.send("Query not found.")

    # DSU Error handler
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        # sourcery skip: remove-redundant-fstring
        errors = {
            discordSuperUtils.NotPlaying: "Not playing any music right now...",
            discordSuperUtils.NotConnected: f"Bot not connected to a voice channel!",
            discordSuperUtils.NotPaused: "Player is not paused!",
            discordSuperUtils.QueueEmpty: "The queue is empty!",
            discordSuperUtils.AlreadyConnected: "Already connected to voice channel!",
            discordSuperUtils.QueueError: "There has been a queue error!",
            discordSuperUtils.SkipError: "There is no song to skip to!",
            discordSuperUtils.UserNotConnected: "User is not connected to a voice channel!",
            discordSuperUtils.InvalidSkipIndex: "That skip index is invalid!",
        }

        for error_type, response in errors.items():
            if isinstance(error, error_type):
                await ctx.send(response)
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
            title="Now Playing",
            color=discord.Color.from_rgb(255, 255, 0),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            description=f"[**{player.title}**]({player.url}) by **{uploader}**",
        )
        embed.add_field(name="Requested by", value=requester)
        embed.set_thumbnail(url=thumbnail)

        await ctx.send(embed=embed)
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
    @commands.command()
    async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.send("👋")
            # Or
            # await message.add_reaction("👋")

    # Lyrics command
    @commands.command()
    async def lyrics(self, ctx, *, query=None):
        if response := await self.MusicManager.lyrics(ctx, query):
            # If lyrics are found
            title, author, query_lyrics = response
            # Formatting the lyrics
            splitted = query_lyrics.split("\n")
            res = []
            current = ""
            for i, split in enumerate(splitted):
                if len(splitted) <= i + 1 or len(current) + len(splitted[i + 1]) > 1024:
                    res.append(current)
                    current = ""
                    continue
                current += split + "\n"
            # Creating embeds list for PageManager
            embeds = [
                discord.Embed(
                    title=f"Lyrics for '{title}' by '{author}', (Page {i + 1}/{len(res)})",
                    description=x,
                )
                for i, x in enumerate(res)
            ]
            # editing the embeds
            for embed in embeds:
                embed.timestamp = datetime.datetime.utcnow()

            page_manager = discordSuperUtils.PageManager(
                ctx,
                embeds,
                public=True,
            )

            await page_manager.run()

        else:
            await ctx.send("No lyrics were found for the song")

    # Now playing command
    @commands.command()
    async def now_playing(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            # Played duration
            duration_played = await self.MusicManager.get_player_played_duration(
                ctx, player
            )

            # Loop status
            loop = (await self.MusicManager.get_queue(ctx)).loop
            if loop == discordSuperUtils.Loops.LOOP:
                loop_status = "Looping enabled."
            elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
                loop_status = "Queue looping enabled."
            else:
                loop_status = "Looping Disabled"

            # Fecthing other details
            thumbnail = player.data["videoDetails"]["thumbnail"]["thumbnails"][-1][
                "url"
            ]
            title = player.title
            url = player.url
            uploader = player.data["videoDetails"]["author"]
            views = player.data["videoDetails"]["viewCount"]
            rating = player.data["videoDetails"]["averageRating"]
            requester = player.requester.mention if player.requester else "Autoplay"

            embed = discord.Embed(
                title="Now playing",
                description=f"**{title}**",
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.from_rgb(0, 255, 255),
            )
            embed.add_field(
                name="Played",
                value=self.MusicManager.parse_duration(
                    duration=duration_played, hour_format=False
                ),
            )
            embed.add_field(
                name="Duration",
                value=self.MusicManager.parse_duration(
                    duration=player.duration, hour_format=False
                ),
            )
            embed.add_field(name="Loop", value=loop_status)
            embed.add_field(name="Requested by", value=requester)
            embed.add_field(name="Uploader", value=uploader)
            embed.add_field(name="URL", value=f"[Click]({url})")
            embed.add_field(name="Views", value=parse_count(int(views)))
            embed.add_field(name="Rating", value=rating)
            embed.set_thumbnail(url=thumbnail)
            embed.set_image(url=r"https://i.imgur.com/ufxvZ0j.gif")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            await ctx.send(embed=embed)

    # Join voice channel command
    @commands.command()
    @ensure_voice_state()
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.send("Joined Voice Channel")

    # Play song command
    @commands.command()
    @ensure_voice_state()
    async def play(self, ctx, *, query: str):
        # Calling the play function
        await Music.play_cmd(self, ctx, query)

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

    # History command
    @commands.command()
    async def history(self, ctx, songs_per_page: int = 15):
        if queue := (await self.MusicManager.get_queue(ctx)):
            formatted_history = [
                f"""**Title:** [{x.title}]({x.url})
                Requester: {x.requester.mention if x.requester else 'Autoplay'}"""
                for x in queue.history
            ]

            embeds = discordSuperUtils.generate_embeds(
                formatted_history,
                "Song History",
                "Shows all played songs",
                songs_per_page,
                string_format="{}",
            )

            for embed in embeds:
                embed.timestamp = datetime.datetime.utcnow()

            await discordSuperUtils.PageManager(ctx, embeds, public=True).run()

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

    # Queue command
    @commands.command()
    async def queue(self, ctx, songs_per_page: int = 10):
        if queue := await self.MusicManager.get_queue(ctx):
            formatted_queue = [
                f"""**Title:** [{x.title}]({x.url})
                Requester: {x.requester.mention if x.requester else 'Autoplay'}"""
                for x in queue.queue
            ]

            player = await self.MusicManager.now_playing(ctx)
            uploader = player.data["videoDetails"]["author"]
            thumbnail = player.data["videoDetails"]["thumbnail"]["thumbnails"][-1][
                "url"
            ]

            embeds = discordSuperUtils.generate_embeds(
                formatted_queue,
                "Queue",  # Title of embed
                f"""**Now Playing:
                [{player.title}]({player.url})** by **{uploader}**""",
                songs_per_page,  # Number of rows in one pane
                color=11658814,  # Color of embed in decimal color
                string_format="{}",
            )

            embeds[0].set_thumbnail(url=thumbnail)
            for embed in embeds:
                embed.timestamp = datetime.datetime.utcnow()

            await discordSuperUtils.PageManager(ctx, embeds, public=True).run()

    # Loop status command
    @commands.command()
    async def loop_check(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            loop = queue.loop
            loop_status = None

            if loop == discordSuperUtils.Loops.LOOP:
                loop_status = "Looping enabled."

            elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
                loop_status = "Queue looping enabled."

            elif loop == discordSuperUtils.Loops.NO_LOOP:
                loop_status = "No loop enabled."

            if loop_status:
                embed = discord.Embed(
                    title=loop_status,
                    color=0x00FF00,
                    timestamp=datetime.datetime.utcnow(),
                )

                await ctx.send(embed=embed)

    # Autoplay command
    @commands.command()
    async def autoplay(self, ctx):
        is_autoplay = await self.MusicManager.autoplay(ctx)

        if is_autoplay is not None:
            await ctx.send(f"Autoplay toggled to {is_autoplay}")

    # Shuffle command
    @commands.command()
    async def shuffle(self, ctx):
        is_shuffle = await self.MusicManager.shuffle(ctx)

        if is_shuffle is not None:
            await ctx.send(f"Shuffle toggled to {is_shuffle}")

    # Previous/Rewind command
    @commands.command()
    async def previous(self, ctx, index: int = None):

        if previous_player := await self.MusicManager.previous(
            ctx, index, no_autoplay=True
        ):
            await ctx.send(f"Rewinding from {previous_player[0].title}")

    # Playlist command
    @commands.group(invoke_without_command=True)
    async def playlists(self, ctx, user: discord.user = None):
        user = user or ctx.author
        user_playlists = await MusicManager.get_user_playlists(user)

        if not user_playlists:
            await ctx.send(f"No playlists of {user.mention} were found.")
            return

        formatted_playlists = [
            f"""**Title:** '{user_playlist.playlist.title}'
            Total Songs: {len(user_playlist.playlist.songs)}
            ID: `{user_playlist.id}`"""
            for user_playlist in user_playlists
        ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_playlists,
            f"Playlists of {user}",
            f"Showing {user.mention}'s playlists.",
            15,
            string_format="{}",
        )

        for embed in embeds:
            embed.timestamp = datetime.datetime.utcnow()

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()

    # Playlist add command
    @playlists.command()
    async def add(self, ctx, url: str):
        added_playlist = await MusicManager.add_playlist(ctx.author, url)

        if not added_playlist:
            await ctx.send("Playlist URL not found!")
            return

        await ctx.send(f"Playlist added with ID `{added_playlist.id}`")

    @playlists.command()
    @ensure_voice_state()
    async def play(self, ctx, index: int, user: discord.member = None):
        # Checking valid index
        index = indexer(index)

        index -= 1
        user = user or ctx.author

        # Fetching user's playlists
        playlists = await self.MusicManager.get_user_playlists(user, partial=True)

        if not playlists:
            await ctx.send(f"No playlists of {user.mention} were found.")
            return

        # Fetching the playlist at index
        playlist = playlists[index]

        if not playlist:
            await ctx.send("No playlist at this index.")
            return

        # Fetching full playlist
        user_playlist = await self.MusicManager.get_playlist(ctx.author, playlist.id)

        # Playing the playlist
        async with ctx.typing():
            players = await MusicManager.create_playlist_players(
                user_playlist.playlist, ctx.author
            )

            if players:
                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    await self.MusicManager.join(ctx)

                if await self.MusicManager.queue_add(
                    players=players, ctx=ctx
                ) and not await self.MusicManager.play(ctx):
                    await ctx.send(f"Added playlist {playlist.playlist.title}")
                else:
                    await ctx.send("✅")

            else:
                await ctx.send("Query not found.")


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
⭐ 플레이리스트 추가.
❌ 대기열 초기화 및 음성채널 접속해제.
    """
    def default_music_embed(self):
        em = discord.Embed(
            title="현재 아무 곡도 재생 중이지 않아요.",
            description="[초대](https://koreanbots.dev/bots/893841721958469703/invite) | [하트주기](https://koreanbots.dev/bots/893841721958469703/vote) | [지원서버](https://discord.gg/294KSUxcz2) | [깃허브](https://github.com/spacedev-official/harin)",
            colour=discord.Colour.dark_purple()
        )
        em.set_image(url="https://media.discordapp.net/attachments/889514827905630290/914160536709636096/9dac48ccd1fc3509.png")
        em.set_footer(text="아래 버튼을 통해 조작하실 수 있어요!")
        return em
    @commands.Cog.listener("on_message")
    async def music_message(self,message):
        if message.author.bot:
            return
        if message.author.id != 281566165699002379:
            return await message.channel.send("테스트봇은 오너만 조작이 가능해요.")
        ctx = await self.bot.get_context(message)
        if message.content == "~setup":
            channel = await message.guild.create_text_channel(name="music-test",topic=self.topic)
            await channel.send("https://media.discordapp.net/attachments/889514827905630290/896359450544308244/37cae031dc5a6c40.png")
            await channel.send(content="** **\n**__대기열 목록__**:\n음성채널에 접속한뒤 이 채널에 제목이나 URL을 입력해주세요.",
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
                                       Button(emoji="⭐", custom_id="music_addplaylist"),
                                       Button(emoji="❌", custom_id="music_cancel")
                                   ]
                               ]
                               )
            await message.channel.send(f"<a:check:893674152672776222> 성공적으로 뮤직채널({channel.mention})을 만들었어요!\n해당 채널의 이름과 위치는 마음껏 커스터마이징이 가능하답니다!")

def setup(bot):
    bot.add_cog(Music(bot))