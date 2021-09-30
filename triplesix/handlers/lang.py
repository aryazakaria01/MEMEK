#     Video Stream Bot, by Abdul
#     Copyright (C) 2021  Shohih Abdul
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as published
#     by the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.


from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from dB.getlang import get_message, kode
from dB.lang_db import set_lang, lang_flags
from triplesix.functions import command, authorized_users_only


@Client.on_message(command("lang"))
@authorized_users_only
async def change_lang(_, message: Message):
    try:
        lang = message.command[1]
    except IndexError:
        lang = ""
    if len(lang) > 2 or len(lang) == 1:
        await message.reply("Use the international format (2 characters)")
        return
    if not lang:
        temp = []
        keyboard = []

        for i, j in enumerate(kode, start=1):
            temp.append(InlineKeyboardButton(f"{lang_flags[j]}", callback_data=f"set_lang_{j}"))
            if i % 2 == 0:
                keyboard.append(temp)
                temp = []
            if i == len(kode):
                keyboard.append(temp)
        await message.reply(
            "this is all language that supported with this bot",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    if len(lang) == 2:
        if lang in kode:
            set_lang(message.chat.id, lang)
            await message.reply(get_message(message.chat.id, "lang_changed").format(lang))
        else:
            await message.reply("this lang is not supported")


