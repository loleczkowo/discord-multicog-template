from discord import Interaction, app_commands
from discord.ext import commands
from globals import Globals as G


class AppNotOwner(app_commands.CheckFailure):
    pass


class MissingReference(commands.CheckFailure):
    pass


async def app_is_owner(interaction: Interaction) -> bool:
    if await G.bot.is_owner(interaction.user):
        return True
    raise AppNotOwner


async def must_be_refering(ctx: commands.Context) -> bool:
    ref = ctx.message.reference
    if ref is not None and ref.message_id is not None:
        return True
    raise MissingReference
