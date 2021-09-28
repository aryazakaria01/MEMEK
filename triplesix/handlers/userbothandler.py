from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired, UserAlreadyParticipant, UserNotParticipant
from triplesix.clients import bot, user
from triplesix.functions import command, authorized_users_only, admins_only


@Client.on_message(command("joinchat"))
@authorized_users_only
async def invite_userbot(_, message: Message):
    chat_id = message.chat.id
    invite_link = ""
    try:
        invite_link += (await bot.export_chat_invite_link(chat_id)).invite_link
    except UserAlreadyParticipant:
        await message.reply("i'm here, can I help you?")
    except ChatAdminRequired:
        return await message.reply("make me as administrator")
    await user.joinchat(invite_link)
    await user.send_message(chat_id, "hello! i'm the assistant of this bot!")


@Client.on_message(command("leavechat"))
@authorized_users_only
async def leave_chats(_, message: Message):
    chat_id = message.chat.id
    try:
        await user.leave_chat(chat_id)
    except UserNotParticipant:
        await message.reply("userbot already leave from chats")


@Client.on_message(command("leaveall"))
@admins_only
async def leave_all_chats(_, message: Message):
    dialogs = await user.iter_dialogs()
    left, fail = 0, 0
    rep = await message.reply("processing...")
    for dialog in dialogs:
        chat_id = dialog.chat.id
        try:
            await user.leave_chat(chat_id)
            left += 1
        except Exception as e:
            print(type(e).__name__)
            fail += 1
    await rep.edit(f"success left {left} chats, and failed in {fail} chats")
