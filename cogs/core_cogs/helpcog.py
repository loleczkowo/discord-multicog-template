import discord
from discord import app_commands
from discord.ext import commands
from config import (
    categories, COMMAND_PREFIX, BOT_VERSION, TEMPLATE_VERSION, BOT_GITHUB_LINK)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Returns all commands")
    @app_commands.describe(specify="Get the description of a command")
    async def apphelp(self, interaction: discord.Interaction, specify: str = None):
        embed = await self._help(specify, interaction.guild, "/")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="help", description="Returns all commands")
    async def help(self, ctx: commands.Context, *, specify: str = None):
        embed = await self._help(specify, ctx.guild, COMMAND_PREFIX)
        await ctx.send(embed=embed)

    async def _help(self, specify: str, guild: discord.Guild, used: str):
        app_cmds_list = await self.bot.tree.fetch_commands()
        sync_cmds = {command.name: command for command in app_cmds_list}
        app_cmds = {command.qualified_name: command
                    for command in self.bot.tree.get_commands()}
        _sync_cmds_keys = sync_cmds.keys()
        not_reg_cmds = [cmd for cmd in app_cmds.keys() if cmd not in _sync_cmds_keys]
        cmds = {command.name: command for command in self.bot.commands}

        if specify:
            embed = discord.Embed(color=discord.Color.blue(), title="Command "+specify)
            clean_spec = specify
            if clean_spec.startswith("/"):
                clean_spec = clean_spec[1:]
            elif clean_spec.startswith(COMMAND_PREFIX):
                clean_spec = clean_spec[len(COMMAND_PREFIX):]
            if not specify.startswith("/") and clean_spec in cmds:
                desc = cmds[clean_spec].description
                if desc is None:
                    desc = "MISSING"
                embed.description = f"`/{specify}`: '{desc}'"
            elif not specify.startswith(COMMAND_PREFIX) and clean_spec in app_cmds:
                desc = app_cmds[clean_spec].description
                embed.description = f"`/{specify}`: '{desc}'"
            else:
                embed.description = f"command `{specify}` not found"
            return embed

        bot_server_name = guild.get_member(self.bot.user.id).display_name
        embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"**All commands from `{bot_server_name}`**",
            description=(
             "**Details** - To get details about a command use:\n"
             f"**`{used}help command_name`**\n\u200b"
            ))
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        if len(not_reg_cmds) > 0:
            embed.add_field(name="**WARNING**-not synced commands;",
                            value="`/"+"` `/".join(not_reg_cmds)+"`", inline=False)
        for category in categories.categories.keys():
            app_cmds_str = "`/"+"`\n`/".join(categories.categories[category][1])+"`"
            cmds_str = "`"+COMMAND_PREFIX+f"`\n`{COMMAND_PREFIX}".join(
                categories.categories[category][0])+"`"
            if len(categories.categories[category][1]) == 0:
                app_cmds_str = ""
            if len(categories.categories[category][0]) == 0:
                cmds_str = ""
            embed.add_field(
                name=category,
                value=app_cmds_str+"\n\n"+cmds_str
            )
        template_link = "https://github.com/loleczkowo/discord-multicog-template"
        github_link = ""
        if BOT_GITHUB_LINK is not None:
            github_link = f"[Github]({BOT_GITHUB_LINK})"
        embed.add_field(name="", value=(
            f"-# Bot`v{BOT_VERSION}`{github_link} - Made using *`loleczkowo`'s* "
            f"[Template]({template_link})`v{TEMPLATE_VERSION}`"), inline=False)
        return embed
