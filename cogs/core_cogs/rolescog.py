from discord import (
    Embed, Color, app_commands, Interaction, Emoji, HTTPException, NotFound,
    RawReactionActionEvent)
from discord.ext import commands
from core import Memory, must_be_refering, log
from core.check_permission import MissingReference
from config import (
    CT_ADMIN, categories, COMMAND_PREFIX, WARNING, events, EV_STARTUP, INFO)


@categories.set_cog_category(CT_ADMIN)
class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reg_msgs = Memory("reg_msg", {}, cog_local=self, save_on_change=True)
        # {chanid_msgid: [
        # {"emoji": emojistr, "name": name, "desc": desc, "role": roleid} ]}
        self.emoji_role = Memory("emoji_role", {}, cog_local=self, save_on_change=True)
        # {chanid_msgid_emoji: roleid}

    @events.cog_on_event(EV_STARTUP)
    async def update_all(self):
        ids = [id for id in self.reg_msgs.mem.keys()]
        for id in ids:
            await self._update(id)

    @app_commands.command(name="_rs_setup_roles", description="setups role selection")
    @app_commands.default_permissions(administrator=True)
    async def setup_roles(self, inter: Interaction):
        await inter.response.send_message((
            "To add new roles use "
            f'`{COMMAND_PREFIX}_rs_add_role ROLEID EMOJI "Role Name" "Description"` '
            "While replying to the send embed"),
            ephemeral=True)
        msg = await inter.channel.send(embed=self._gen_embed(empty=True))
        self.reg_msgs.mem[f"{msg.channel.id}_{msg.id}"] = []
        self.reg_msgs.touch()

    @app_commands.command(name="_rs_reload_roles",
                          description="reloads role selections")
    @app_commands.default_permissions(administrator=True)
    async def reload_roles(self, inter: Interaction):
        await self.update_all()
        await inter.response.send_message("Done :D", ephemeral=True)

    @commands.command(name="_rs_add_role",
                      description="adds(or replaces) a role to role selection")
    @commands.has_permissions(administrator=True)
    @commands.check(must_be_refering)
    async def add_role(self, ctx: commands.Context, role_id: int,
                       emoji: Emoji | str, role_name: str, description: str):
        chn = ctx.channel
        ref = await chn.fetch_message(ctx.message.reference.message_id)
        id = f"{chn.id}_{ref.id}"
        if id not in self.reg_msgs.mem:
            raise MissingReference
        if f"{id}_{emoji}" in self.emoji_role.mem:
            self.emoji_role.mem[f"{id}_{emoji}"] = role_id
            self.emoji_role.touch()
            for i, s in enumerate(self.reg_msgs.mem[id]):
                if s["emoji"] == str(emoji):
                    self.reg_msgs.mem[id][i] = {"emoji": str(emoji), "name": role_name,
                                                "desc": description, "role": role_id}
                    break
            self.reg_msgs.touch()
            await self._update(id)
            await ctx.message.delete()
            return
        if isinstance(emoji, str):
            try:
                await ref.add_reaction(emoji)
            except HTTPException as e:
                if e.code != 10014:
                    raise e
                raise commands.BadArgument("Bot cannot use this emoji")
        elif not emoji.is_usable():
            raise commands.BadArgument("Bot cannot use this emoji")
        else:
            await ref.add_reaction(emoji)
        self.reg_msgs.mem[id].append({
            "emoji": str(emoji), "name": role_name, "desc": description, "role": role_id
        })
        self.reg_msgs.touch()
        self.emoji_role.mem[f"{id}_{emoji}"] = role_id
        self.emoji_role.touch()
        await self._update(id)
        await ctx.message.delete()

    @commands.command(name="_rs_remove_emoji",
                      description="removes an emoji from the role selection")
    @commands.has_permissions(administrator=True)
    @commands.check(must_be_refering)
    async def remove_role(self, ctx: commands.Context, emoji: Emoji | str):
        chn = ctx.channel
        ref = await chn.fetch_message(ctx.message.reference.message_id)
        id = f"{chn.id}_{ref.id}"
        if id not in self.reg_msgs.mem:
            raise MissingReference
        if f"{id}_{emoji}" not in self.emoji_role.mem:
            raise commands.BadArgument(f"Emoji {emoji} not found in the role select")
        del self.emoji_role.mem[f"{id}_{emoji}"]
        self.emoji_role.touch()
        for i, s in enumerate(self.reg_msgs.mem[id]):
            if s["emoji"] == str(emoji):
                del self.reg_msgs.mem[id][i]
                self.reg_msgs.touch()
                await self._update(id)
                break
        await ctx.message.delete()

    def _gen_embed(self, empty=False, id=None):
        embed = Embed(
            title="Roles", color=Color.blue(),
            description="Select your roles by reacting with emojis"
        )
        if empty:
            return embed
        for s in self.reg_msgs.mem[id]:
            embed.add_field(
                name=f"{s["emoji"]} **: {s["name"]}**",
                value=f"<@&{s["role"]}> **|** {s["desc"]}\n\u200b", inline=False
            )
        return embed

    async def _update(self, id: str):
        _split = id.split("_")
        chanid, msgid = int(_split[0]), int(_split[1])
        exists = True
        try:
            chan = await self.bot.fetch_channel(chanid)
            msg = await chan.fetch_message(msgid)
        except NotFound:
            exists = False
        except Exception as e:
            log(WARNING(to_discord=True),
                f"error while getting message `{msgid}` for role selection update: {e}")
            return
        if id not in self.reg_msgs.mem:
            if exists:
                log(WARNING(to_discord=True, ping=True),
                    f"No data for role selection `{msgid}`. Removing message")
                await msg.delete()
            return
        if not exists:
            log(WARNING(to_discord=True),
                f"Message for role selection `{msgid}` was lost. Removing data")
            del self.reg_msgs.mem[id]
            self.reg_msgs.touch()
            return
        await msg.edit(embed=self._gen_embed(id=id))
        need_role_fix = False
        emojis = [str(reac.emoji) for reac in msg.reactions]
        for s in self.reg_msgs.mem[id]:
            if s["emoji"] not in emojis:
                need_role_fix = s["emoji"]
        if not need_role_fix:
            return
        log(WARNING(to_discord=True),
            f"reaction missing ({s["emoji"]}). Re-adding reaction for `{msg.id}`")
        await msg.clear_reactions()
        for s in self.reg_msgs.mem[id]:
            await msg.add_reaction(s["emoji"])

    # listeners

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        user = payload.member or await self.bot.fetch_user(payload.user_id)
        if user.bot:
            return
        main_id = f"{payload.channel_id}_{payload.message_id}_{payload.emoji}"
        if main_id not in self.emoji_role.mem:
            return
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(user.id)
        add_role = guild.get_role(self.emoji_role.mem[main_id])
        if add_role in member.roles:
            log(INFO, f"{member.name} already has the role {add_role.name}")
            return
        log(INFO, f"Giving {member.name} role {add_role.name}")
        await member.add_roles(add_role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        user = payload.member or await self.bot.fetch_user(payload.user_id)
        if user.bot:
            return
        main_id = f"{payload.channel_id}_{payload.message_id}_{payload.emoji}"
        if main_id not in self.emoji_role.mem:
            return
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(user.id)
        remove_role = guild.get_role(self.emoji_role.mem[main_id])
        if remove_role not in member.roles:
            log(INFO, f"{member.name} already has no {remove_role.name} role")
            return
        log(INFO, f"Removing role {remove_role.name} from {member.name}")
        await member.remove_roles(remove_role)
