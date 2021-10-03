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


from pyrogram import Client, filters, emoji
from pyrogram.types import CallbackQuery

from dB import set_lang, get_message
from triplesix.clients import player
from triplesix.functions import rem
from triplesix.handlers.stream import InlineKeyboardButton, InlineKeyboardMarkup


def inline_keyboard(user_id: int):
    i = 5
    j = -1
    for _ in range(5):
        i += 1
        j += 1
        yield InlineKeyboardButton(
            f"{i}", callback_data=f"nextstream {j}|{user_id}"
        )


def inline_keyboard2(user_id: int):
    i = 0
    j = 0
    for _ in range(5):
        i += 1
        yield InlineKeyboardButton(
            f"{i}", callback_data=f"back|{user_id}"
        )
        j += 1


@Client.on_callback_query(filters.regex(pattern=r"close"))
async def close_inline(_, cb: CallbackQuery):
    callback = cb.data.split("|")
    user_id = int(callback[1])
    message = cb.message
    rem.clear()
    person = await message.chat.get_member(cb.from_user.id)
    if cb.from_user.id != user_id:
        await cb.answer("this is not for you.", show_alert=True)
        return
    if person.status in ("creator", "administrator"):
        return await message.delete()
    await message.delete()


@Client.on_callback_query(filters.regex(pattern=r"(.*)stream"))
async def play_callback(_, cb: CallbackQuery):
    match = cb.matches[0].group(1)
    callback = cb.data.split("|")
    x = int(callback[0].split(" ")[1])
    user_id = int(callback[1])
    if not match:
        if cb.from_user.id != user_id:
            await cb.answer("this is not for u.", show_alert=True)
            return
        title = rem[0][x]["title"]
        rem.clear()
        await cb.message.delete()
        await player.start_stream_via_callback(title, cb)
    elif match == "next":
        title = rem[1][x]["title"]
        rem.clear()
        await cb.message.delete()
        await player.start_stream_via_callback(title, cb)


@Client.on_callback_query(filters.regex(pattern=r"back"))
async def back_callback(_, cb: CallbackQuery):
    message = cb.message
    callback = cb.data.split("|")
    user_id = int(callback[1])
    if cb.from_user.id != user_id:
        await cb.answer("this is not for u.", show_alert=True)
        return
    temp = []
    keyboard = []
    # enumerate for keyboard
    for count, j in enumerate(list(inline_keyboard2(user_id)), start=1):
        temp.append(j)
        if count % 3 == 0:
            keyboard.append(temp)
            temp = []
        if count == len(list(inline_keyboard2(user_id))):
            keyboard.append(temp)
    rez = "\n"
    k = 0
    for i in rem[0]:
        k += 1
        rez += f"|- {k}. [{i['title'][:35]}]({i['url']})\n"
        rez += f"|- Duration - {i['duration']}\n\n"
    await message.edit(
        f"Results\n{rez}\n|- Owner @shohih_abdul2",
        reply_markup=InlineKeyboardMarkup(
            [
                keyboard[0],
                keyboard[1],
                [InlineKeyboardButton(f"Next {emoji.RIGHT_ARROW}", f"next|{user_id}")],
                [InlineKeyboardButton(f"Close {emoji.WASTEBASKET}", f"close|{user_id}")],
            ]
        ),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex(pattern=r"next"))
async def next_callback(_, cb: CallbackQuery):
    message = cb.message
    callback = cb.data.split("|")
    user_id = int(callback[1])
    if cb.from_user.id != user_id:
        await cb.answer("this is not for u.", show_alert=True)
        return
    rez = "\n"
    k = 5
    for i in rem[1]:
        k += 1
        rez += f"|- {k}. [{i['title']}]({i['url']})\n"
        rez += f"|- Duration - {i['duration']}\n\n"
    temp = []
    keyboard = []
    x = list(inline_keyboard(user_id))
    for count, j in enumerate(x, start=1):
        temp.append(j)
        if count % 3 == 0:
            keyboard.append(temp)
            temp = []
        if count == len(list(inline_keyboard(user_id))):
            keyboard.append(temp)
    await message.edit(
        f"Results\n{rez}\n|- Owner @shohih_abdul2",
        reply_markup=InlineKeyboardMarkup(
            [
                keyboard[0],
                keyboard[1],
                [InlineKeyboardButton(f"Back {emoji.LEFT_ARROW}", f"back|{user_id}")],
                [InlineKeyboardButton(f"Close {emoji.WASTEBASKET}", f"close|{user_id}")],
            ]
        ),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(filters.regex(pattern=r"set_lang_(.*)"))
async def change_language(_, cb: CallbackQuery):
    lang = cb.matches[0].group(1)
    chat = cb.message.chat
    try:
        set_lang(chat.id, lang)
        await cb.message.edit(get_message(chat.id, "lang_changed").format(lang))
    except Exception as e:
        await cb.message.edit(f"an error occured\n\n{e}")
