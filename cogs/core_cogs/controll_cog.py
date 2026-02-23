import discord
from discord import app_commands, Embed, Color
from discord.ext import commands
import aiohttp
from core import log, app_is_owner, run_shutdown, Memory
from config import INFO, EV_STARTUP, events
from cogs.cogscore import reload_cogs
from globals import Globals as G


class ControllCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reload_cogs", description="(*owner) Reload bot cogs")
    @app_commands.check(app_is_owner)
    async def reload_cogs(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), f"CogReload command invoked by {interaction.user}")
        embed = Embed(color=Color.yellow(), title="Reloading Cogs",
                      description="`Reloading . . .`")
        await interaction.response.send_message(embed=embed)
        failed = await reload_cogs(self.bot, G.cog_list)
        if failed == 0:
            embed.description = "`Cogs reloaded`"
            embed.color = Color.green()
        else:
            embed.description = \
                f"`Cogs reloaded`\n**FAILED TO LOAD {failed} COG"+"S"*(failed > 1)
            embed.color = Color.red()
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="restart", description="(*owner) Hard-restart the bot")
    @app_commands.check(app_is_owner)
    async def restart(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), f"Restart command invoked by {interaction.user}")
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
        rs_update_app_id = Memory("rs_update_app_id", default=None, cog_local=self)
        rs_update_token = Memory("rs_update_token", default=None, cog_local=self)
        if rs_update_app_id.mem is not None:
            embed = Embed(color=Color.green(), title="Restarting Bot",
                          description="`Bot restarted successfully!`")
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.partial(
                    rs_update_app_id.mem,
                    rs_update_token.mem,
                    session=session,
                )
                await webhook.edit_message(
                    "@original",
                    embed=embed,
                )
            rs_update_app_id.mem = None
            rs_update_token.mem = None
            rs_update_app_id.close()
            rs_update_token.close()

    @app_commands.command(name="shutdown", description="(*owner) Shut the bot down.")
    @app_commands.check(app_is_owner)
    async def shutdown(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), f"Shutdown command invoked by {interaction.user}")
        embed = Embed(color=Color.yellow(), title="Shutting down",
                      description="`Shutting down . . .`")
        await interaction.response.send_message(embed=embed)
        await run_shutdown(self.bot)
