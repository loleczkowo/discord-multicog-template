from discord import Interaction
from discord import app_commands
from globals import Globals as G


class AppNotOwner(app_commands.CheckFailure):
    pass


async def app_is_owner(interaction: Interaction) -> bool:
    if await G.bot.is_owner(interaction.user):
        return True
    raise AppNotOwner
