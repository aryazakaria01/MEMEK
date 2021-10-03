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


import asyncio
import random
from typing import Optional

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message, CallbackQuery
from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import NoActiveGroupCall, GroupCallNotFound
from pytgcalls.types.input_stream import AudioVideoPiped
from pytgcalls.types.input_stream.quality import MediumQualityAudio, MediumQualityVideo
from pytgcalls.types import Update

from dB import get_message
from triplesix.configs import config
from triplesix.functions import get_youtube_stream

user = Client(config.SESSION, config.API_ID, config.API_HASH)

bot = Client(
    ":memory:",
    config.API_ID,
    config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="triplesix.handlers"),
)


class Player:
    def __init__(self, pytgcalls: PyTgCalls):
        self.call = pytgcalls
        self.playlist: dict[int, list[dict[str, str]]] = {}
    
    async def _set_stream(self, mode: str, message: Message, source: str, y, query: Optional[str] = ""):
        playlist = self.playlist
        chat_id = message.chat.id
        try:
            await self._stream(mode, message, source, y, query)
            return
        except FloodWait as fw:
            await message.reply(f"Getting floodwait {fw.x} second, bot sleeping")
            await asyncio.sleep(fw.x)
            await self._stream(mode, message, source, y, query)
        except NoActiveGroupCall:
            try:
                await user.send(
                    CreateGroupCall(
                        peer=await user.resolve_peer(chat_id),
                        random_id=random.randint(10000, 999999999),
                    )
                )
                await self._stream(mode, message, source, y, query)
            except Exception as ex:
                await y.edit(
                    f"{type(ex).__name__}: {ex.with_traceback(ex.__traceback__)}"
                )
                del playlist[chat_id]
        except Exception as ex:
            await y.edit(f"{type(ex).__name__}: {ex.with_traceback(ex.__traceback__)}")
            del playlist[chat_id]

    async def _stream(self, mode: str, message: Message, source: str, y: Message, query: Optional[str] = ""):
        chat_id = message.chat.id
        playlist = self.playlist
        call = self.call
        if mode == "yt":
            playlist[chat_id] = [{"query": query, "mode": mode}]
            await y.edit(get_message(chat_id, "stream").format(query))
            await call.join_group_call(
                chat_id,
                AudioVideoPiped(source, MediumQualityAudio(), MediumQualityVideo()),
                stream_type=StreamType().pulse_stream,
            )
        elif mode == "local":
            playlist[chat_id] = [{"query": query, "mode": mode}]
            await y.edit(get_message(chat_id, "localstream"))
            await call.join_group_call(
                chat_id,
                AudioVideoPiped(source),
                stream_type=StreamType().pulse_stream
            )

    async def _start_stream_via_yt(self, query, message: Message):
        chat_id = message.chat.id
        playlist = self.playlist
        try:
            if len(playlist[chat_id]) >= 1:
                try:
                    playlist[chat_id].extend([{"query": query, "mode": "yt"}])
                    y = await message.reply("Queued")
                    await asyncio.sleep(10)
                    await y.delete()
                    return
                except KeyError as e:
                    await message.reply(
                        f"{type(e).__name__}: {e}\nplease tell owner about this."
                    )
                    del playlist[chat_id]
                    return
        except KeyError:
            pass
        y = await message.reply(get_message(chat_id, "process"))
        url = await get_youtube_stream(query)
        await self._set_stream("yt", message, url, y, query)

    async def _start_stream_via_local(self, message: Message):
        chat_id = message.chat.id
        playlist = self.playlist
        query = await message.reply_to_message.download()
        try:
            if len(playlist[chat_id]) >= 1:
                try:
                    playlist[chat_id].extend([{"query": query, "mode": "local"}])
                    y = await message.reply("queued")
                    await asyncio.sleep(10)
                    await y.delete()
                    return
                except KeyError as e:
                    await message.reply(
                        f"Error: {e} \n please tell the owner about this"
                    )
                    del playlist[chat_id]
                    return
        except KeyError:
            pass
        y = await message.reply(get_message(chat_id, "process"))
        await self._set_stream("local", message, query, y)

    async def start_stream(self, mode: str, message: Message, query: Optional[str] = ""):
        if mode == "yt":
            await self._start_stream_via_yt(query, message)
        if mode == "local":
            await self._start_stream_via_local(message)

    async def start_stream_via_callback(self, query: str, callback: CallbackQuery):
        message = callback.message
        await self._start_stream_via_yt(query, message)

    async def stream_change(self, mode: str, chat_id: int, query: str):
        call = self.call
        if mode == "yt":
            url = await get_youtube_stream(query)
            await call.change_stream(
                chat_id,
                AudioVideoPiped(url, MediumQualityAudio(), MediumQualityVideo()),
            )
        elif mode == "local":
            await call.change_stream(
                chat_id,
                AudioVideoPiped(query)
            )

    async def change_stream(self, message: Message):
        playlist = self.playlist
        chat_id = message.chat.id
        query = playlist[chat_id][0]["query"]
        mode = playlist[chat_id][0]["mode"]
        try:
            if len(playlist[chat_id]) > 1:
                playlist[chat_id].pop(0)
                await self.stream_change(mode, chat_id, query)
                await asyncio.sleep(3)
                await message.reply(f"Skipped track, and playing {query}")
                return
            await message.reply("No playlist")
            return
        except KeyError:
            await message.reply("No playlist")

    async def end_stream(self, message: Message):
        chat_id = message.chat.id
        playlist = self.playlist
        call = self.call
        try:
            if call.get_call(chat_id):
                await call.leave_group_call(chat_id)
                del playlist[chat_id]
                await message.reply("ended")
                return
            await message.reply("you never stream anything")
        except GroupCallNotFound:
            await message.reply("not streaming")

    async def change_stream_status(self, status: str, message: Message):
        if status == "pause":
            call = self.call
            chat_id = message.chat.id
            if call.get_call(chat_id):
                await call.pause_stream(chat_id)
                await message.reply("Bot paused")
                return
            return
        if status == "resume":
            call = self.call
            chat_id = message.chat.id
            if call.get_call(chat_id):
                await call.resume_stream(chat_id)
                await message.reply("Bot resume")
                await asyncio.sleep(5)
                await message.delete()
                return
            return

    async def change_vol(self, message: Message):
        vol = int("".join(message.command[1]))
        call = self.call
        chat_id = message.chat.id
        if call.get_call(chat_id):
            await call.change_volume_call(chat_id, vol)
            await message.reply(f"Volume changed to {vol}%")


player = Player(PyTgCalls(user))


@player.call.on_stream_end()
async def stream_ended(pytgcalls: PyTgCalls, update: Update):
    playlist = player.playlist
    chat_id = update.chat_id
    call = player.call
    if len(playlist[chat_id]) > 1:
        playlist[chat_id].pop(0)
        query = playlist[chat_id][0]["query"]
        mode = playlist[chat_id][0]["mode"]
        await player.stream_change(mode, chat_id, query)
        return
    del playlist[chat_id]
    await call.leave_group_call(chat_id)
    await asyncio.sleep(5)
