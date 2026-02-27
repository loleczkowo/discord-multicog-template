from discord.ext.commands import Bot
from discord import Message, Embed, Color, MessageReference, File
from typing import List, Tuple
from globals import Globals as G
from config import events, EV_SHUTDOWN, INFO, QINFO, DISCORD_EMBED_LIMIT
from .logs import log, discord_log
# high lever utils to prevend loop imports


async def run_shutdown(bot: Bot):
    if G.controlled_shutdown:
        return  # already in shutdown process, ignore
    log(INFO, "Running shutdown process")
    G.controlled_shutdown = True
    if bot.is_closed():
        G.connected = False
    if G.connected:
        discord_log(INFO, "## BOT SHUTDOWN")
    log(QINFO, "Calling shutdown events")
    events.call(EV_SHUTDOWN)
    log(QINFO, "Closing events")
    await events.close_all_shutdown_functions()
    log(QINFO, "Closing bot connection")
    if not bot.is_closed():
        G.connected = False
        await bot.close()


async def embed_from_message(
        message: Message, color: Color, reference: MessageReference = None
        ) -> Tuple[List[Embed], List[Embed], List[Embed], List[File]]:
    to_start = []
    attach = []
    embed = Embed(color=color, description=message.content)
    icon = message.author.avatar.url if message.author.avatar else None
    if reference == -1:
        embed.set_author(name="Replying to "+message.author.name, icon_url=icon)
    else:
        embed.set_author(name=message.author.name, icon_url=icon)
        if reference is not None:
            try:
                ref = await message.channel.fetch_message(reference.message_id)
                l, m, r, a = await embed_from_message(ref, Color.light_gray(),
                                                      reference=-1)
                to_start += l+[m]+r
                attach += a
            except Exception:
                to_start.append(Embed(
                    color=Color.light_gray(), description="`Message lost`"))
    embed.timestamp = message.created_at
    added_img = False
    add_to_end = []
    for att in message.attachments:
        if att.content_type:
            if att.content_type.startswith("image"):
                if not added_img:
                    added_img = True
                    embed.set_image(url=att.url)
                else:
                    e = Embed(color=color)
                    e.set_image(url=att.url)
                    add_to_end.append(e)
                continue
        attach.append(await att.to_file())
    for emd in message.embeds:
        emd.color = color
        add_to_end.append(emd)

    while len(to_start)+1+len(add_to_end) > DISCORD_EMBED_LIMIT:
        if len(to_start) > 1:
            to_start.pop()
        else:
            add_to_end.pop()
    return to_start, embed, add_to_end, attach
