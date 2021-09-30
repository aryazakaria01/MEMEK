from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant, UserAlreadyParticipant
from triplesix.clients import user
from triplesix.functions import command, authorized_users_only, admins_only


@Client.on_message(command("joinchat"))
@authorized_users_only
async def invite_userbot(client: Client, message: Message):
    chat_id = message.chat.id
    invite_link = await client.export_chat_invite_link(chat_id)
    user_id = (await user.get_me()).id
    try:
        await user.join_chat(invite_link)
        await user.send_message(chat_id, "hi, what can I do for you?")
        await client.promote_chat_member(
            chat_id,
            user_id,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_delete_messages=True,
            can_manage_voice_chats=True,
        )
    except UserAlreadyParticipant:
        await user.send_message(chat_id, "hello? can I help you?", reply_to_message_id=message.message_id)


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
