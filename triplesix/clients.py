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
        self.client = {}
        self.playlist: dict[int, list[dict[str, str]]] = {}

    async def _stream(self, mode: str, message: Message, source: str, y, query: Optional[str] = ""):
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
            self.client[chat_id] = call
            return
        if mode == "local":
            playlist[chat_id] = [{"query": query, "mode": mode}]
            await y.edit(get_message(chat_id, "localstream"))
            await call.join_group_call(
                chat_id,
                AudioVideoPiped(source),
                stream_type=StreamType().pulse_stream
            )
            self.client[chat_id] = call
            return

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
        try:
            await self._stream("yt", message, url, y, query)
        except FloodWait as fw:
            await message.reply(f"Getting floodwait {fw.x} second, bot sleeping")
            await asyncio.sleep(fw.x)
            await self._stream("yt", message, url, y, query)
        except NoActiveGroupCall:
            try:
                await user.send(
                    CreateGroupCall(
                        peer=await user.resolve_peer(chat_id),
                        random_id=random.randint(10000, 999999999),
                    )
                )
                await self._stream("yt", message, url, y, query)
            except Exception as ex:
                await y.edit(
                    f"{type(ex).__name__}: {ex.with_traceback(ex.__traceback__)}"
                )
                del playlist[chat_id]
        except Exception as ex:
            await y.edit(f"{type(ex).__name__}: {ex.with_traceback(ex.__traceback__)}")
            del playlist[chat_id]

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
        try:
            await self._stream("local", message, query, y)
        except FloodWait as fw:
            await message.reply(f"Getting floodwait {fw.x} second, bot sleeping")
            await asyncio.sleep(fw.x)
            await self._stream("local", message, query, y)
        except NoActiveGroupCall:
            try:
                await user.send(
                    CreateGroupCall(
                        peer=await user.resolve_peer(chat_id),
                        random_id=random.randint(10000, 999999999),
                    )
                )
                await self._stream("local", message, query, y)
            except Exception as ex:
                await y.edit(
                    f"{type(ex).__name__}: {ex.with_traceback(ex.__traceback__)}"
                )
                del playlist[chat_id]
        except Exception as ex:
            await y.edit(f"{type(ex).__name__}: {ex.with_traceback(ex.__traceback__)}")
            del playlist[chat_id]

    async def start_stream(self, mode: str, message: Message, query: Optional[str] = ""):
        if mode == "yt":
            await self._start_stream_via_yt(query, message)
        if mode == "local":
            await self._start_stream_via_local(message)

    async def start_stream_via_callback(self, query: str, callback: CallbackQuery):
        message = callback.message
        await self._start_stream_via_yt(query, message)

    async def change_stream(self, message: Message):
        playlist = self.playlist
        client = self.client
        chat_id = message.chat.id
        if len(playlist[chat_id]) > 1:
            playlist[chat_id].pop(0)
            query = playlist[chat_id][0]["query"]
            url = await get_youtube_stream(query)
            await asyncio.sleep(3)
            await client[chat_id].change_stream(
                chat_id,
                AudioVideoPiped(url, MediumQualityAudio(), MediumQualityVideo()),
            )
            await asyncio.sleep(3)
            await message.reply(f"Skipped track, and playing {query}")
            return
        await message.reply("No playlist")

    async def end_stream(self, message: Message):
        chat_id = message.chat.id
        playlist = self.playlist
        client = self.client
        try:
            try:
                if client[chat_id].get_call(chat_id):
                    await client[chat_id].leave_group_call(chat_id)
                    del playlist[chat_id]
                    await message.reply("ended")
            except KeyError:
                await message.reply("you never streaming anything")
        except GroupCallNotFound:
            await message.reply("not streaming")

    async def change_stream_status(self, status: str, message: Message):
        if status == "pause":
            client = self.client
            chat_id = message.chat.id
            if client[chat_id].get_call(chat_id):
                await client[chat_id].pause_stream(chat_id)
                await message.reply("Bot paused")
                return
            return
        if status == "resume":
            client = self.client
            chat_id = message.chat.id
            if client[chat_id].get_call(chat_id):
                await client[chat_id].resume_stream(chat_id)
                await message.reply("Bot resume")
                await asyncio.sleep(5)
                await message.delete()
                return
            return

    async def change_vol(self, message: Message):
        vol = int("".join(message.command[1]))
        client = self.client
        chat_id = message.chat.id
        if client[chat_id].get_call(chat_id):
            await client[chat_id].change_volume_call(chat_id, vol)
            await message.reply(f"Volume changed to {vol}%")


player = Player(PyTgCalls(user))


@player.call.on_stream_end()
async def stream_ended(pytgcalls: PyTgCalls, update: Update):
    playlist = player.playlist
    chat_id = update.chat_id
    client = player.client
    print(pytgcalls)
    if len(playlist[chat_id]) > 1:
        playlist[chat_id].pop(0)
        if playlist[chat_id][0]["mode"] == "yt":
            query = playlist[chat_id][0]["query"]
            url = await get_youtube_stream(query)
            await asyncio.sleep(3)
            await client[chat_id].change_stream(
                chat_id,
                AudioVideoPiped(url, MediumQualityAudio(), MediumQualityVideo()),
            )
            await asyncio.sleep(3)
            return
        if playlist[chat_id][0]["mode"] == "local":
            source = playlist[chat_id][0]["query"]
            await asyncio.sleep(3)
            await client[chat_id].change_stream(
                chat_id,
                AudioVideoPiped(source)
            )
            await asyncio.sleep(3)
            return
        return
    del playlist[chat_id]
    await client[chat_id].leave_group_call(chat_id)
    await asyncio.sleep(5)
