import discord
from discord.ext.commands import Context as CTX
from discord.ext import commands
from discord import app_commands
from core import log, format_traceback
from .check_permission import AppNotOwner
from config import ERROR, events, EV_STARTUP
from globals import Globals as G


@events.on_event(EV_STARTUP)
async def setup():
    @G.bot.event
    async def on_command_error(ctx: CTX, error: discord.DiscordException):
        cause, message = check_error(error, False, ctx)
        if not cause:
            return
        await ctx.reply(embed=discord.Embed(title=cause,
                        description=message, color=discord.Color.red()), ephemeral=True)

    @G.bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        cause, message = check_error(error, True, interaction)
        if not cause:
            return
        await interaction.response.send_message(
            embed=discord.Embed(title=cause, description=message,
                                color=discord.Color.red()), ephemeral=True)


def check_error(error: discord.DiscordException,
                is_app_command: bool, context: CTX | discord.Interaction):
    cmd_name = context.invoked_with if not is_app_command else context.command.name
    author_id = context.author.id if not is_app_command else context.user.id

    if isinstance(error, (commands.CommandNotFound, app_commands.CommandNotFound)):
        if is_app_command:
            return "Command not found.", "This might be due to your client being out of date.\n"\
                    "Try reloading the discord with `Ctrl+R` (or `Cmd+R` on macOS) and try again."
        return False, None
    if isinstance(error, (commands.BotMissingPermissions, app_commands.BotMissingPermissions)):
        log(ERROR(to_discord=True, ping=True), f"Bot missing permissions for command '{cmd_name}' error; {error}")
        return "I do not have the permissions to execute this command.", \
               "Please contact an administrator to fix this!"
    if isinstance(error, (commands.MissingRole, app_commands.MissingRole)):
        return "You do not have the required role to use this command.", \
                f"This command requires the role `{error.missing_role}`"
    if isinstance(error, (commands.MissingPermissions, app_commands.MissingPermissions)):
        return "You do not have the permissions to use this command.", \
                "To use this command, you need the following permissions: "\
                "`"+'`, `'.join(error.missing_permissions)+"`"
    if isinstance(error, (commands.NotOwner, AppNotOwner)):
        return "Only the bot owner can use this command.", \
                "Yup this command can be used only by me, "\
                "the one who wrote this error message"
    if isinstance(error, (commands.CommandOnCooldown, app_commands.CommandOnCooldown)):
        return "This command is on cooldown.", \
                f"Try again in {round(error.retry_after, 2)} seconds."
    if not is_app_command:
        # TODO add these for app commands as well
        if isinstance(error, commands.NSFWChannelRequired):
            return "This command can only be used in NSFW channels.", None
        if isinstance(error, commands.PrivateMessageOnly):
            return "This command can only be used in private messages.", \
                    "Please use this command in a private chat with the bot."
        if isinstance(error, commands.NoPrivateMessage):
            return "This command cannot be used in private messages.", \
                    "Please use this command in a server channel."
        if isinstance(error, commands.MaxConcurrencyReached):
            return "This command is currently being used by too many people.", "Please try again later."
        if isinstance(error, commands.DisabledCommand):
            return "This command is currently disabled.", "Please try again later."
        # impossible for app commands
        # user input error
        if isinstance(error, commands.MissingRequiredAttachment):
            return "Missing required attachment.", \
                  f"Please attach the required file `{error.param.name}` and try again."
        if isinstance(error, commands.BadArgument):
            return "Invalid argument provided.", str(error)
        if isinstance(error, commands.MissingRequiredArgument):
            return "Missing required argument.", \
                   "missing argument: "+error.param.name
        if isinstance(error, commands.TooManyArguments):
            return "Too many arguments provided.", "Please check the command usage and try again."
        if isinstance(error, commands.ArgumentParsingError):
            return "Error parsing arguments.", str(error)
        if isinstance(error, commands.BadUnionArgument):
            return "Invalid argument provided.", str(error)
        if isinstance(error, commands.BadLiteralArgument):
            return "Invalid argument provided.", \
                    f"Argument '{error.argument}' does not match any of the valid options."
        if isinstance(error, commands.UserInputError):
            return "Invalid input.", str(error)

    # command error
    if not isinstance(error, (commands.CommandError, app_commands.AppCommandError)):
        log(ERROR(to_discord=True, ping=True), f"Unexpected error for command "
            f"'{cmd_name}' by `{author_id}` error; {error}")
        return "An unexpected error occurred while processing the command.", \
               "(you were supposed to get a more specific error message, "\
               "but something went wrong while, whoops!)"
    formatted_error_lines = '\n'.join(format_traceback(error))
    log(ERROR(to_discord=True, newline_formatting=False, ping=True),
        f"Command `{cmd_name}` failed: `{error}`\n```{formatted_error_lines}```")
    return "An unexpected error occurred while processing the command.", \
           "uhoh! command error! admins are on their way to fix this!"
