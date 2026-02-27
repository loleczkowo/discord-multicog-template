import discord
from discord import app_commands
from discord.ext import commands, tasks
from core import Memory, embed_from_message, log
from config import categories, CT_ADMIN, INFO, events, EV_SHUTDOWN

STAR = "⭐"
STR_MESSAGE = f"{STAR} **{{stars}}** | {{mention}}"
# for discord rate-limits
FREESH_MESSAGE_UPDATE = 2  # 2 seconds for each <1h starboard message update
OLD_MESSAGE_UPDATE = 10  # 10 seconds for each >1h starboard message update


# Cog by loleczkowo :D  - feel free to edit/copy anything

@categories.set_cog_category(CT_ADMIN)
class StarboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel = Memory("channel", False, self, save_on_change=True)
        self.default_stars = Memory("def_stars", -1, self, save_on_change=True)
        self.chan_stars = Memory("chan_stars", {}, self, save_on_change=True)
        self.messages = Memory("msgs", {}, self)
        # {message.id: (bot_chan.id, bot_msg.id)}
        self.bot_messages = Memory("bot_msgs", {}, self)
        # {bot_chan.id+bot_msg.id: {
        # "ori_id":, "ori_chan__id":, "users": [user.id, user.id]} }
        self.ignore_removal = set()  # (channelid, messageid, userid)

        self.update_olds: list = []  # starboard messages to update
        self.update_news: list = []  # [(id, message, original_message)]
        self._oldupdate_loop.start()
        self._freshupdate_loop.start()

    @app_commands.command(name="_starboard_set_channel",
                          description="sets starboard channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction,
                          channel: discord.TextChannel | None,
                          default_stars: int | None):
        if channel is None:
            if default_stars is not None:
                self.default_stars.mem = default_stars
                await interaction.response.send_message(
                    f"Starboard default stars set to {default_stars}", ephemeral=True)
                return
            self.channel.mem = False
            await interaction.response.send_message(
                "Starboard Channel set to nothing", ephemeral=True)
            return
        if default_stars is not None:
            self.default_stars.mem = default_stars
        elif self.default_stars.mem == -1:
            raise commands.BadArgument(
                "default_stars must be provided when setup for first time")
        self.channel.mem = channel.id
        await interaction.response.send_message(
            f"Starboard Channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(
        name="_starboard_set_perchan_stars",
        description="Sets how much stars are needed to starboard a message per channel")
    @app_commands.describe(stars="Number of stars (0 = starboard disabled)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel_stars(self, interaction: discord.Interaction,
                                channel: discord.TextChannel, stars: int):
        self.chan_stars.mem[str(channel.id)] = stars
        self.chan_stars.touch()
        await interaction.response.send_message(
            f"Channel {channel.mention} stars to starboard set to {stars}",
            ephemeral=True
        )

    @app_commands.command(name="_starboard_remove_perchan",
                          description="Removes perchannel channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_channel_stars(self, interaction: discord.Interaction,
                                   channel: discord.TextChannel):
        if str(channel.id) not in self.chan_stars.mem:
            raise commands.BadArgument("Channel already has no setting")
        del self.chan_stars.mem[str(channel.id)]
        self.chan_stars.touch()
        await interaction.response.send_message(
            f"Channel {channel.mention} stars to starboard set to default " +
            str(self.default_stars.mem),
            ephemeral=True
        )

    @app_commands.command(name="_starboard_status", description="get starboard status")
    async def starboard_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=discord.Color.yellow(), title="Starboard Status",
            description=f"{len(self.bot_messages.mem.keys())} messages on board")
        if self.channel.mem:
            try:
                chan = await self.bot.fetch_channel(self.channel.mem)
                embed.add_field(
                    name="Starboard channel", inline=False,
                    value=f"{chan.mention} - default stars `{self.default_stars.mem}`")
            except Exception:
                pass
        for perchan, stars in self.chan_stars.mem.items():
            if stars == 0:
                stars = "Disabled"
            try:
                chan = await self.bot.fetch_channel(perchan)
                embed.add_field(
                    name=f"{chan.mention}-stars", value=stars)
            except Exception:
                pass
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _bot_msg_id(self, chanid, messageid):
        return f"{chanid}_{messageid}"

    async def _update_starmessage(self, id: str, message=False, original_message=False):
        if not message:
            t = id.split("_")
            chanid, messid = int(t[0]), int(t[1])
            try:
                chan = await self.bot.fetch_channel(chanid)
                message = await chan.fetch_message(messid)
            except discord.NotFound:
                log(INFO(to_discord=True), "Lost message from starboard; removing data")
                del self.messages.mem[str(self.bot_messages.mem[id]["ori_id"])]
                del self.bot_messages.mem[id]
                self.messages.touch()
                self.bot_messages.touch()
                return
        toup = [id, message, original_message]
        if toup in self.update_olds or toup in self.update_news:
            return  # already in queue to be updated
        if (discord.utils.utcnow() - message.created_at).total_seconds() > 3600:
            self.update_olds.append(toup)
        else:
            self.update_news.append(toup)

    async def _message_true_update(
            self, id, message: discord.Message, original_message):
        stars = len(self.bot_messages.mem[id]["users"])
        if not original_message:
            try:
                ori_chan = await self.bot.fetch_channel(
                    self.bot_messages.mem[id]["ori_chan_id"])
                original_message = await ori_chan.fetch_message(
                    self.bot_messages.mem[id]["ori_id"])
            except discord.NotFound:
                await message.edit(
                    content=STR_MESSAGE.format(stars=stars, mention="None"),
                    embed=discord.Embed(color=discord.Color.gold(),
                                        description="`Message lost`"))
                return
        l, e, r, a = await embed_from_message(
            original_message, discord.Color.gold(), original_message.reference)
        await message.edit(
            content=STR_MESSAGE.format(stars=stars, mention=original_message.jump_url),
            embeds=l + [e] + r, attachments=a)

    @events.cog_on_event(EV_SHUTDOWN)
    def cog_unload(self):
        self._oldupdate_loop.cancel()
        self._freshupdate_loop.cancel()

    @tasks.loop(seconds=OLD_MESSAGE_UPDATE, reconnect=True)
    async def _oldupdate_loop(self):
        if not self.update_olds:
            return
        msgs = self.update_olds.pop(0)
        id, message, original_message = msgs[0], msgs[1], msgs[2]
        print("slower edit")
        await self._message_true_update(id, message, original_message)

    @tasks.loop(seconds=FREESH_MESSAGE_UPDATE, reconnect=True)
    async def _freshupdate_loop(self):
        if not self.update_news:
            return
        msgs = self.update_news.pop(0)
        id, message, original_message = msgs[0], msgs[1], msgs[2]
        print("faster edit")
        await self._message_true_update(id, message, original_message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        user = payload.member or await self.bot.fetch_user(payload.user_id)
        emoji = payload.emoji
        if user.bot or emoji.name != STAR:
            return
        channel_id = payload.channel_id
        message_id = payload.message_id
        bot_msg_id = self._bot_msg_id(channel_id, message_id)
        if bot_msg_id in self.bot_messages.mem:
            try:
                ori_chan = await self.bot.fetch_channel(
                    self.bot_messages.mem[bot_msg_id]["ori_chan_id"])
                ori_mess = await ori_chan.fetch_message(
                    self.bot_messages.mem[bot_msg_id]["ori_id"])
            except discord.NotFound:
                ori_mess = False
            if user.id in self.bot_messages.mem[bot_msg_id]["users"]:
                self.ignore_removal.add((ori_chan.id, ori_mess.id, user.id))
                try:
                    if ori_mess:
                        await ori_mess.remove_reaction(STAR, user)
                except discord.NotFound:
                    self.ignore_removal.remove((ori_chan.id, ori_mess.id, user.id))
                return  # user already reacted
            self.bot_messages.mem[bot_msg_id]["users"].append(user.id)
            self.bot_messages.touch()
            await self._update_starmessage(bot_msg_id, original_message=ori_mess)
            return
        if str(message_id) in self.messages.mem:
            bot_msg_id = self._bot_msg_id(self.messages.mem[str(message_id)][0],
                                          self.messages.mem[str(message_id)][1])
            try:
                obot_chan = await self.bot.fetch_channel(
                    self.messages.mem[str(message_id)][0])
                obot_mess = await obot_chan.fetch_message(
                    self.messages.mem[str(message_id)][1])
            except discord.NotFound:
                await self._update_starmessage(bot_msg_id)
                return
            if user.id in self.bot_messages.mem[bot_msg_id]["users"]:
                self.ignore_removal.add((obot_chan.id, obot_mess.id, user.id))
                try:
                    await obot_mess.remove_reaction(STAR, user)
                except discord.NotFound:
                    self.ignore_removal.remove((ori_chan.id, ori_mess.id, user.id))
                return
            self.bot_messages.mem[bot_msg_id]["users"].append(user.id)
            self.bot_messages.touch()
            await self._update_starmessage(bot_msg_id, obot_mess)
            return
        ori_chan = await self.bot.fetch_channel(channel_id)
        message = await ori_chan.fetch_message(message_id)
        if str(channel_id) in self.chan_stars.mem:
            limit = self.chan_stars.mem[str(channel_id)]
        else:
            limit = self.default_stars.mem
        if limit == 0:
            return  # starboard disabled
        if not self.channel.mem:
            return
        users = []
        for reac in message.reactions:
            if reac.emoji == STAR:
                async for user in reac.users(limit=limit+5):
                    users.append(user.id)
                break
        if len(users) < limit:
            return
        channel = await self.bot.fetch_channel(self.channel.mem)
        l, e, r, a = await embed_from_message(
            message, discord.Color.gold(), message.reference)
        send_message = await channel.send(
            content=STR_MESSAGE.format(stars=len(users), mention=message.jump_url),
            embeds=l + [e] + r, files=a)
        await send_message.add_reaction(STAR)

        self.messages.mem[str(message_id)] = [self.channel.mem, send_message.id]
        self.bot_messages.mem[self._bot_msg_id(self.channel.mem, send_message.id)] = {
            "ori_id": message_id, "ori_chan_id": payload.channel_id, "users": users
        }
        self.messages.touch()
        self.bot_messages.touch()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        user = payload.member or await self.bot.fetch_user(payload.user_id)
        emoji = payload.emoji
        if user.bot or emoji.name != STAR:
            return
        message_id = payload.message_id
        channel_id = payload.channel_id
        if (channel_id, message_id, user.id) in self.ignore_removal:
            self.ignore_removal.remove((channel_id, message_id, user.id))
            return  # controlled removal
        bot_msg_id = self._bot_msg_id(channel_id, message_id)
        if bot_msg_id in self.bot_messages.mem:
            if user.id not in self.bot_messages.mem[bot_msg_id]["users"]:
                return  # user already unreacted
            self.bot_messages.mem[bot_msg_id]["users"].remove(user.id)
            self.bot_messages.touch()
            await self._update_starmessage(bot_msg_id)
        elif str(message_id) in self.messages.mem:
            bot_msg_id = self._bot_msg_id(self.messages.mem[str(message_id)][0],
                                          self.messages.mem[str(message_id)][1])
            if user.id not in self.bot_messages.mem[bot_msg_id]["users"]:
                return  # user already unreacted
            self.bot_messages.mem[bot_msg_id]["users"].remove(user.id)
            self.bot_messages.touch()
            await self._update_starmessage(bot_msg_id)
        # user unreacted to a message that's not on starboard
