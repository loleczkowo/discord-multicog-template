import discord
from discord import app_commands
from discord.ext import commands
from config import categories, COMMAND_PREFIX


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Returns all commands")
    @app_commands.describe(specify="Get the description of a command")
    async def apphelp(self, interaction: discord.Interaction, specify: str = None):
        embed = await self._help(specify)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="help", description="Returns all commands")
    async def help(self, ctx: commands.Context, *, specify: str = None):
        embed = await self._help(specify)
        await ctx.send(embed=embed)

    async def _help(self, specify: str):
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
            if not specify.startswith("/") and clean_spec in cmds:
                desc = cmds[clean_spec].description
                if desc is None:
                    desc = "MISSING"
                embed.description = f"`/{specify}`: '{desc}'"
            elif clean_spec in app_cmds:
                desc = app_cmds[clean_spec].description
                embed.description = f"`/{specify}`: '{desc}'"
            else:
                embed.description = f"command `{specify}` not found"
            return embed

        embed = discord.Embed(color=discord.Color.blue(), title="Commands")
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
        return embed
