import asyncio
import io
import logging
import os
import sqlite3

import discord
from discord import Color, Forbidden
from discord.ext import commands
from revChatGPT.V1 import AsyncChatbot

from Prompt import Prompt
from ReGenBtn import ReGenBtn
from STT import STT
from TTS import TTS


class Reply:
    def __init__(self, db: sqlite3.Connection, chatbot: AsyncChatbot, client: commands.Bot):
        self.db = db
        self.prompt = Prompt(chatbot)
        self.client = client
        self.stt = STT(os.environ["SPEECH_KEY"], os.environ["SPEECH_REGION"])
        self.tts = TTS(os.environ["SPEECH_KEY"], os.environ["SPEECH_REGION"])

    # Generate reply
    async def reply(self, message: discord.Message, conversation: str, msg: discord.Message):
        ask = message.content
        print(message)
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
        reply = await self.prompt.ask(conversation, msg, ask)

        # convert reply to voice message
        if reply != "":
            voice = await self.tts.text_to_speech(reply)
            await msg.edit(attachments=[discord.File(io.BytesIO(voice), filename="voice-message.ogg")])

        await message.add_reaction("✅") # add check mark

    # DM
    async def dm(self, message: discord.Message):
        cursor = self.db.cursor()

        try:
            # add loading reaction
            await message.remove_reaction("✅", self.client.user)
            await message.add_reaction("<a:loading:1112646025090445354>")
            msg = await message.reply("<a:loading:1112646025090445354>")

            # check if conversation is started?
            cursor.execute("SELECT * FROM DM WHERE User = ?", (message.author.id,))
            result = cursor.fetchone()

            # start conversation if not started
            if result is None:
                conversation = await self.prompt.start_new_conversation(message.author.name)
                cursor.execute("INSERT INTO DM (User, conversation) VALUES (?, ?)",
                               (message.author.id, conversation))
                self.db.commit()
                await asyncio.sleep(1)
            else:
                conversation = result[1]

            # check if bot is replying
            cursor.execute("SELECT * FROM DM WHERE User = ? AND replying != TRUE",
                           (message.author.id,))
            result = cursor.fetchone()

            # reply message
            if result is not None:
                # set is replying
                cursor.execute("UPDATE DM SET replying = TRUE WHERE User = ?",
                               (message.author.id,))
                self.db.commit()
                await self.reply(message, conversation, msg)

                # add regenerate button
                async def callback():
                    await self.dm(message)

                btn = ReGenBtn(callback)
                await msg.edit(view=btn)

        except Exception as e:
            logging.debug(e)
            # add error reaction
            await message.add_reaction("❌")
            await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

        finally:
            # set is not replying
            cursor.execute("UPDATE DM SET replying = FALSE WHERE User = ?", (message.author.id,))
            self.db.commit()

            # remove loading reaction
            await message.remove_reaction("<a:loading:1112646025090445354>", self.client.user)

    # @mention bot
    async def mention(self, message: discord.Message):
        cursor = self.db.cursor()

        # check replyAt is enabled
        await message.remove_reaction("✅", self.client.user)
        cursor.execute("SELECT * FROM Guild WHERE Guild_ID = ? AND replyAt = TRUE", (message.guild.id,))
        result = cursor.fetchone()

        if result is not None:
            try:
                # add loading reaction
                await message.add_reaction("<a:loading:1112646025090445354>")
                msg = await message.reply("<a:loading:1112646025090445354>")

                # check if conversation is started?
                cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = %s AND user = ?",
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
                    conversation = result[2]

                # check if bot is replying
                cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = ? AND user = ? AND replying != TRUE",
                               (message.guild.id, message.author.id))
                result = cursor.fetchone()

                # reply message
                if result is not None:
                    # set is replying
                    cursor.execute("UPDATE ReplyAt SET replying = TRUE WHERE Guild_ID = ? AND user = %s",
                                   (message.guild.id, message.author.id))
                    self.db.commit()
                    await self.reply(message, conversation, msg)

                    # add regenerate button
                    async def callback():
                        await self.dm(message)

                    btn = ReGenBtn(callback)
                    await msg.edit(view=btn)

            except Exception as e:
                logging.debug(e)
                # add error reaction
                await message.add_reaction("❌")
                if isinstance(e, Forbidden):
                    await message.channel.send("🔥 Sorry, I can't reply message in this channel. "
                                               f"Please check my permission. Details: `{Forbidden}`")
                else:
                    await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

            finally:
                # set is not replying
                cursor.execute("UPDATE ReplyAt SET replying = FALSE WHERE Guild_ID = ? AND user = ?",
                               (message.guild.id, message.author.id))
                self.db.commit()

                # remove loading reaction
                await message.remove_reaction("<a:loading:1112646025090445354>", self.client.user)

        else:
            await message.reply("🔥 Sorry, Thi server is not enabled **@mention** feature.")

    # channel message
    async def channel(self, message: discord.Message):
        cursor = self.db.cursor()

        cursor.execute("SELECT * FROM ReplyThis WHERE Guild_ID = ? AND channel_ID = ? AND replying != TRUE",
                       (message.guild.id, message.channel.id))
        result = cursor.fetchone()

        if result is not None:
            # set is replying
            cursor.execute("UPDATE ReplyThis SET replying = TRUE WHERE Guild_ID = ? AND channel_ID = ?",
                           (message.guild.id, message.channel.id))
            self.db.commit()
            conversation = result[2]

            # reply message
            try:
                # add loading reaction
                await message.remove_reaction("✅", self.client.user)
                await message.add_reaction("<a:loading:1112646025090445354>")
                msg = await message.reply("<a:loading:1112646025090445354>")

                await self.reply(message, conversation, msg)

                # add regenerate button
                async def callback():
                    await self.dm(message)

                btn = ReGenBtn(callback)
                await msg.edit(view=btn)

            except Exception as e:
                logging.debug(e)
                # add error reaction
                await message.add_reaction("❌")
                if isinstance(e, Forbidden):
                    await message.channel.send("🔥 Sorry, I can't reply message in this channel. "
                                               f"Please check my permission. Details: `{Forbidden}`")
                else:
                    await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

            finally:
                # set is not replying
                cursor.execute("UPDATE ReplyThis SET replying = FALSE WHERE Guild_ID = ? AND channel_ID = ?",
                               (message.guild.id, message.channel.id))
                self.db.commit()

                # remove loading reaction
                await message.remove_reaction("<a:loading:1112646025090445354>", self.client.user)
