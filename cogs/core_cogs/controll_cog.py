import discord
from discord import app_commands, Embed, Color
from discord.ext import commands
from core import log, app_is_owner
from config import INFO, events
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
        await interaction.response.send_message(embed=embed)
        # TODO make it so it updates the message!
        G.restarting = True
        await events.close_all_shutdown_functions()
        G.connected = False
        await self.bot.close()

    @app_commands.command(name="shutdown", description="(*owner) Shut the bot down.")
    @app_commands.check(app_is_owner)
    async def shutdown(self, interaction: discord.Interaction):
        log(INFO(to_discord=True), f"Shutdown command invoked by {interaction.user}")
        embed = Embed(color=Color.yellow(), title="Shutting down",
                      description="`Shutting down . . .`")
        await interaction.response.send_message(embed=embed)
        await events.close_all_shutdown_functions()
        G.connected = False
        await self.bot.close()
