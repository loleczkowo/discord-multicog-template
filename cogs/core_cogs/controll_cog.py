import subprocess
import discord
from discord import app_commands, Embed, Color
from discord.ext import commands
import aiohttp
from core import log, app_is_owner, run_shutdown, Memory
from config import (INFO, EV_STARTUP, events, COMMAND_PREFIX,
                    DIR, BOT_VERSION, TEMPLATE_VERSION)
from cogs.cogscore import reload_cogs
from globals import Globals as G
from config import categories, CT_BOT_OWNER


# Cog by loleczkowo :D  - feel free to edit/copy anything

@categories.set_cog_category(CT_BOT_OWNER)
class ControllCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # If you dont have a git repo for your bot just remove this :)
    @app_commands.command(name="_gitpull", description="(*owner) gitpull.")
    @app_commands.check(app_is_owner)
    async def gitpull(self, interaction: discord.Interaction):
        embed = Embed(color=Color.blue(), title="Git Pull", description="`running...`")
        await interaction.response.send_message(embed=embed)
        result = subprocess.run(["git", "-C", DIR, "pull"], capture_output=True,
                                text=True, check=False,)
        embed.description = "`finished`"
        embed.add_field(name="Result", value=f"`{result.stdout}`")
        embed.add_field(name="Code", value=f"`{result.returncode}`")
        if result.returncode == 0:
            embed.color = Color.green()
        else:
            embed.color = Color.red()
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="_reload_cogs", description="(*owner) Reload bot cogs")
    @app_commands.check(app_is_owner)
    async def reload_cogs(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), "CogReload command invoked by ", interaction.user)
        embed = Embed(color=Color.yellow(), title="Reloading Cogs",
                      description="`Reloading . . .`")
        await interaction.response.send_message(embed=embed)
        failed = await reload_cogs(self.bot, G.cog_list)
        if failed == 0:
            embed.description = "`Cogs reloaded`"
            embed.color = Color.green()
        else:
            embed.description = \
                f"`Cogs reloaded`\n**FAILED TO LOAD {failed} COG**"+"S"*(failed > 1)
            embed.color = Color.red()
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="_sync_commands", description="(*owner) Sync commands")
    @app_commands.check(app_is_owner)
    async def sync_commands(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), "SyncCommands command invoked by ", interaction.user)
        embed = Embed(color=Color.yellow(), title="Syncing Commands",
                      description="`Syncing . . .`")
        await interaction.response.send_message(embed=embed)
        app_cmds_list = await self.bot.tree.fetch_commands()
        bef_sync_cmds = [command.name for command in app_cmds_list]
        await self.bot.tree.sync()
        app_cmds_list = await self.bot.tree.fetch_commands()
        sync_cmds = [command.name for command in app_cmds_list]
        all_cmds = [command.qualified_name for command in self.bot.tree.get_commands()]
        not_reg_cmds = [cmd for cmd in all_cmds if cmd not in sync_cmds]
        new_commands = [cmd for cmd in sync_cmds if cmd not in bef_sync_cmds]
        new_cmds = len(new_commands)
        if len(not_reg_cmds):
            embed.description = "`Commands synced`\n**FAILED: "\
                f"{len(all_cmds)-len(sync_cmds)} COMMANDS NOT SYNCED**\n" \
                "unsynced commands: `/"+"` `/".join(not_reg_cmds)+"`"
            embed.color = Color.orange()
        elif new_cmds == 0:
            embed.description = "`Commands synced` 0 new commands, command list;\n`" \
                "/"+"` `/".join(all_cmds)+"`"
            embed.color = Color.yellow()
        else:
            embed.description = f"`Commands synced` {new_cmds} new commands;\n`/" \
                + "` `/".join(new_commands)+"`"\
                "\n\ncommand list;\n`/"+"` `/".join(all_cmds)+"`"
            embed.color = Color.green()
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="_restart", description="(*owner) Hard-restart the bot")
    @app_commands.check(app_is_owner)
    async def restart(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), "Restart command invoked by ", interaction.user)
        embed = Embed(color=Color.yellow(), title="Restarting Bot",
                      description="`Restarting . . .`")
        rs_update_app_id = Memory("rs_update_app_id", default=None, cog_local=self)
        rs_update_token = Memory("rs_update_token", default=None, cog_local=self)
        rs_update_token.mem = interaction.token
        rs_update_app_id.mem = interaction.application_id
        rs_update_app_id.close()
        rs_update_token.close()
        await interaction.response.send_message(embed=embed)
        G.restarting = True
        await run_shutdown(self.bot)

    @events.cog_on_event(EV_STARTUP)
    async def _restart_msg(self):
        try:
            rs_update_app_id = Memory("rs_update_app_id", default=None, cog_local=self)
            rs_update_token = Memory("rs_update_token", default=None, cog_local=self)
            if rs_update_app_id.mem is not None:
                embed = Embed(color=Color.green(), title="Restarting Bot",
                              description="`Bot restarted successfully!`")
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.partial(
                        rs_update_app_id.mem, rs_update_token.mem,
                        session=session,)
                    await webhook.edit_message("@original", embed=embed,)
                rs_update_app_id.mem = None
                rs_update_token.mem = None
                rs_update_app_id.close()
                rs_update_token.close()
        except Exception:
            pass

    @app_commands.command(name="_shutdown", description="(*owner) Shut the bot down.")
    @app_commands.check(app_is_owner)
    async def shutdown(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), "Shutdown command invoked by ", interaction.user)
        embed = Embed(color=Color.yellow(), title="Shutting down",
                      description="`Shutting down . . .`")
        await interaction.response.send_message(embed=embed)
        await run_shutdown(self.bot)

    @app_commands.command(name="_botstatus", description="Get the bot status.")
    async def botstatus(self, interaction: discord.Interaction):
        embed = Embed(color=Color.blue(), title="Bot Status")
        embed.description = f"BOT `V{BOT_VERSION}`, TEMPLATE `V{TEMPLATE_VERSION}`"
        embed.add_field(name="**COGS**", value="", inline=False)
        for cog in G.cog_list:
            if cog.__name__ in self.bot.cogs:
                status = ":green_square: *Online*"
            else:
                status = ":red_square: *Offline*"
            embed.add_field(name=cog.__name__, value=status)

        app_cmds = [command.qualified_name for command in self.bot.tree.get_commands()]
        cmds = [command.name for command in self.bot.commands]
        text = "`/"+"`, `/".join(app_cmds)+"`"
        embed.add_field(name="**APP COMMANDS**", value=text, inline=False)
        text = "`"+COMMAND_PREFIX+f"` `{COMMAND_PREFIX}".join(cmds)+"`"
        embed.add_field(name="**PREFIX COMMANDS**", value=text, inline=False)
        await interaction.response.send_message(embed=embed)
