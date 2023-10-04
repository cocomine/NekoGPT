import asyncio
import logging
import os
import re
import sqlite3

import discord
from discord import Color, Forbidden
from discord.ext import commands
from revChatGPT.V1 import AsyncChatbot

import Mp3ToMp4
from GenAudioBtn import GenAudioBtn
from Prompt import Prompt
from ReGenBtn import ReGenBtn
from STT import STT
from TTS import TTS


class Reply:
    replying_dm = []
    replying_mention = []
    replying_channel = []

    def __init__(self, db: sqlite3.Connection, chatbot: AsyncChatbot, client: commands.Bot):
        self.db = db
        self.prompt = Prompt(chatbot)
        self.client = client
        self.stt = STT(os.environ["SPEECH_KEY"], os.environ["SPEECH_REGION"])
        self.tts = TTS(os.environ["SPEECH_KEY"], os.environ["SPEECH_REGION"])

    # Generate reply
    async def reply(self, message: discord.Message, conversation: str, msg: discord.Message) -> list[discord.Message]:
        ask = message.content
        # check if message is voice message
        if ask == "" and message.attachments[0] is not None:
            attachments = message.attachments[0]

            if attachments.is_voice_message():
                # convert voice message to text
                ask = await self.stt.speech_to_text(await attachments.read())
                logging.info(f"Voice message {message.author}: {ask}")

                # show original text
                embed = discord.Embed(title=f"Detected content", description=ask,
                                      color=Color.blue(),
                                      type="article")
                embed.set_author(name=f"{message.author}", icon_url=message.author.avatar.url)
                await msg.edit(content="<a:loading:1112646025090445354>", embed=embed)

        # reply
        reply, message_obj_list = await self.prompt.ask(conversation, msg, ask)
        msg = message_obj_list[len(message_obj_list) - 1]

        # convert reply to voice message
        if reply != "":
            # add Generating voice message button
            btn = GenAudioBtn()
            await msg.edit(view=btn)

            # insert ',' after '喵~' or 'meow~'
            p = re.compile(r"(meow|喵)~(?!！|。|，|？|!|,|\?|\.)")
            speech_text = p.sub(r'\1~~ ,', reply)
            print(speech_text)

            # convert text to voice message
            await self.tts.text_to_speech_file(speech_text, f"voice-message_{conversation}.mp3")

            # convert voice message to mp4
            Mp3ToMp4.convert(f"voice-message_{conversation}.mp3", f"voice-message_{conversation}.mp4")

            # upload voice message to discord
            with open(f"voice-message_{conversation}.mp4", "rb") as file:
                await msg.edit(attachments=[discord.File(file, filename=f"voice-message_{conversation}.mp4")])

            # remove Generating voice message button
            await msg.edit(view=None)

            # remove mp4
            os.remove(f"voice-message_{conversation}.mp4")

            # convert text to voice message(old method)
            # voice = await self.tts.text_to_speech_bytes(reply)
            # await msg.edit(attachments=[discord.File(io.BytesIO(voice), filename="voice-message.mp3")])

        await message.add_reaction("✅")  # add check mark

        return message_obj_list  # return message obj list

    # DM
    async def dm(self, message: discord.Message):
        cursor = self.db.cursor()

        # check if bot is replying
        try:
            self.replying_dm.index(message.author.id)
        except ValueError:
            self.replying_dm.append(message.author.id)  # set is replying
        else:
            # is replying
            await message.reply(
                content="⛔ In progress on the previous reply, please wait for moment.")
            return

        try:
            # add loading reaction
            await message.remove_reaction("✅", self.client.user)
            await message.add_reaction("<a:loading:1112646025090445354>")
            msg = await message.reply("<a:loading:1112646025090445354>")

            # check if conversation is started?
            cursor.execute("SELECT conversation FROM DM WHERE User = ?", (message.author.id,))
            result = cursor.fetchone()

            # start conversation if not started
            if result is None:
                conversation = await self.prompt.start_new_conversation()
                cursor.execute("INSERT INTO DM (User, conversation) VALUES (?, ?)",
                               (message.author.id, conversation))
                self.db.commit()
                await asyncio.sleep(1)
            else:
                conversation = result[0]

            # reply message
            message_obj_list = await self.reply(message, conversation, msg)
            msg = message_obj_list[len(message_obj_list) - 1]

            # add regenerate button
            async def callback():
                await self.dm(message)

            btn = ReGenBtn(callback, message_obj_list)
            await msg.edit(view=btn)

        except Exception as e:
            logging.error(e)
            # add error reaction
            await message.add_reaction("❌")
            await message.reply("🔥 Oh no! Something went wrong. Please try again later.")

        finally:
            # set is not replying
            self.replying_dm.remove(message.author.id)

            # remove loading reaction
            await message.remove_reaction("<a:loading:1112646025090445354>", self.client.user)

    # @mention bot
    async def mention(self, message: discord.Message):
        cursor = self.db.cursor()

        # check replyAt is enabled
        await message.remove_reaction("✅", self.client.user)
        cursor.execute("SELECT * FROM Guild WHERE Guild_ID = ? AND replyAt = TRUE", (message.guild.id,))
        result = cursor.fetchone()

        # is not enabled
        if result is None:
            await message.reply("🔥 Sorry, This server is not enabled **@mention** feature.")
            return

        # check if bot is replying
        try:
            self.replying_mention.index(message.author.id)
        except ValueError:
            self.replying_mention.append(message.author.id)  # set is replying
        else:
            # is replying
            await message.reply(
                content="⛔ In progress on the previous reply, please wait for moment.")
            return

        try:
            # add loading reaction
            await message.add_reaction("<a:loading:1112646025090445354>")
            msg = await message.reply("<a:loading:1112646025090445354>")

            # check if conversation is started?
            cursor.execute("SELECT conversation FROM ReplyAt WHERE Guild_ID = ? AND user = ?",
                           (message.guild.id, message.author.id))
            result = cursor.fetchone()

            # start conversation if not started
            if result is None:
                conversation = await self.prompt.start_new_conversation()
                cursor.execute("INSERT INTO ReplyAt (Guild_ID, user, conversation) VALUES (?, ?, ?)",
                               (message.guild.id, message.author.id, conversation))
                self.db.commit()
                await asyncio.sleep(1)
            else:
                conversation = result[0]

            # reply message
            message_obj_list = await self.reply(message, conversation, msg)
            msg = message_obj_list[len(message_obj_list) - 1]

            # add regenerate button
            async def callback():
                await self.dm(message)

            btn = ReGenBtn(callback, message_obj_list)
            await msg.edit(view=btn)

        except Exception as e:
            logging.error(e)

            # add error reaction
            await message.add_reaction("❌")
            if isinstance(e, Forbidden):
                await message.reply("🔥 Sorry, I can't reply message in this channel. "
                                           f"Please check my permission. Details: `{Forbidden}`")
            else:
                await message.reply("🔥 Oh no! Something went wrong. Please try again later.")

        finally:
            # set is not replying
            self.replying_mention.remove(message.author.id)

            # remove loading reaction
            await message.remove_reaction("<a:loading:1112646025090445354>", self.client.user)

    # channel message
    async def channel(self, message: discord.Message):
        cursor = self.db.cursor()

        # get conversation
        cursor.execute("SELECT conversation FROM ReplyThis WHERE Guild_ID = ? AND channel_ID = ?",
                       (message.guild.id, message.channel.id))
        result = cursor.fetchone()

        # check have conversation
        if result is not None:
            # check if bot is replying
            try:
                self.replying_channel.index((message.guild.id, message.channel.id))
            except ValueError:
                self.replying_channel.append((message.guild.id, message.channel.id))  # set is replying
            else:
                # is replying
                await message.reply(
                    content="⛔ In progress on the previous reply, please wait for moment.")
                return

            try:
                conversation = result[0]

                # add loading reaction
                await message.remove_reaction("✅", self.client.user)
                await message.add_reaction("<a:loading:1112646025090445354>")
                msg = await message.reply("<a:loading:1112646025090445354>")

                # reply message
                message_obj_list = await self.reply(message, conversation, msg)
                msg = message_obj_list[len(message_obj_list) - 1]

                # add regenerate button
                async def callback():
                    await self.dm(message)

                btn = ReGenBtn(callback, message_obj_list)
                await msg.edit(view=btn)

            except Exception as e:
                logging.error(e)

                # add error reaction
                await message.add_reaction("❌")
                if isinstance(e, Forbidden):
                    await message.channel.send("🔥 Sorry, I can't reply message in this channel. "
                                               f"Please check my permission. Details: `{Forbidden}`")
                else:
                    await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

            finally:
                # set is not replying
                self.replying_channel.remove((message.guild.id, message.channel.id))

                # remove loading reaction
                await message.remove_reaction("<a:loading:1112646025090445354>", self.client.user)
