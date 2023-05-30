import asyncio

import discord
from discord import Forbidden
from discord.ext import commands
from mysql.connector import connect
from revChatGPT.V1 import AsyncChatbot

from Prompt import Prompt


def set_event_lister(client: commands.Bot, db: connect, chatbot: AsyncChatbot, bot_name: str):
    prompt = Prompt(chatbot)

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
        try:
            synced = await client.tree.sync()
            print(f"Synced {synced} commands")
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                    name=f"@{bot_name} chat with me!"))
        except Exception as e:
            print(e)

    # add into server
    @client.event
    async def on_guild_join(guild: discord.Guild):
        print(f"Joined {guild.name} server. ({guild.id})")

        # add into database
        cursor = db.cursor()
        cursor.execute("INSERT INTO Guild (Guild_ID) VALUES (%s)", (guild.id,))
        db.commit()

    # remove from server
    @client.event
    async def on_guild_remove(guild: discord.Guild):
        print(f"Left {guild.name} server. ({guild.id})")
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT * FROM ReplyThis WHERE Guild_ID = %s", (guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = %s", (guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        # remove from database
        cursor.execute("DELETE FROM Guild WHERE Guild_ID = %s", (guild.id,))
        db.commit()

    @client.event
    async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT * FROM ReplyThis WHERE Channel_ID = %s AND Guild_ID = %s", (channel.id, channel.guild.id))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        cursor.execute("DELETE FROM ReplyThis WHERE channel_ID = %s AND Guild_ID = %s", (channel.id, channel.guild.id))
        db.commit()

    # when message is sent
    @client.event
    async def on_message(message: discord.Message):
        print(f"Message from {message.author} ({message.author.id}): {message.content}")
        cursor = db.cursor()
        if message.author == client.user:
            return

        # check if message is sent in DM
        if isinstance(message.channel, discord.DMChannel):
            try:
                # add loading reaction
                await message.add_reaction("<a:loading:1112646025090445354>")
                msg = await message.reply("<a:loading:1112646025090445354>")

                # check if conversation is started?
                cursor.execute("SELECT * FROM DM WHERE User = %s", (message.author.id,))
                result = cursor.fetchone()

                # start conversation if not started
                if result is None:
                    conversation = await prompt.start_new_conversation(message.author.name)
                    cursor.execute("INSERT INTO DM (User, conversation) VALUES (%s, %s)",
                                   (message.author.id, conversation))
                    db.commit()
                    await asyncio.sleep(1)
                else:
                    conversation = result[1]

                # check if bot is replying
                cursor.execute("SELECT * FROM DM WHERE User = %s AND replying != TRUE",
                               (message.author.id,))
                result = cursor.fetchone()

                # reply message
                if result is not None:
                    # set is replying
                    cursor.execute("UPDATE DM SET replying = TRUE WHERE User = %s",
                                   (message.author.id,))
                    db.commit()

                    await prompt.ask(conversation, msg, message.content)
                    await message.add_reaction("✅")

            except Exception as e:
                print(e)
                # add error reaction
                await message.add_reaction("❌")
                await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

            finally:
                # set is not replying
                cursor.execute("UPDATE DM SET replying = FALSE WHERE User = %s", (message.author.id,))
                db.commit()

                # remove loading reaction
                await message.remove_reaction("<a:loading:1112646025090445354>", client.user)

            return

        # check if message is @mention bot
        if client.user.mentioned_in(message):
            # check replyAt is enabled
            cursor.execute("SELECT * FROM Guild WHERE Guild_ID = %s AND replyAt = TRUE", (message.guild.id,))
            result = cursor.fetchone()

            if result is not None:
                try:
                    # add loading reaction
                    await message.add_reaction("<a:loading:1112646025090445354>")
                    msg = await message.reply("<a:loading:1112646025090445354>")

                    # check if conversation is started?
                    cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = %s AND user = %s",
                                   (message.guild.id, message.author.id))
                    result = cursor.fetchone()

                    # start conversation if not started
                    if result is None:
                        conversation = await prompt.start_new_conversation()
                        cursor.execute("INSERT INTO ReplyAt (Guild_ID, user, conversation) VALUES (%s, %s, %s)",
                                       (message.guild.id, message.author.id, conversation))
                        db.commit()
                        await asyncio.sleep(1)
                    else:
                        conversation = result[2]

                    # check if bot is replying
                    cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = %s AND user = %s AND replying != TRUE",
                                   (message.guild.id, message.author.id))
                    result = cursor.fetchone()

                    # reply message
                    if result is not None:
                        # set is replying
                        cursor.execute("UPDATE ReplyAt SET replying = TRUE WHERE Guild_ID = %s AND user = %s",
                                       (message.guild.id, message.author.id))
                        db.commit()

                        await prompt.ask(conversation, msg, message.content)
                        await message.add_reaction("✅")

                except Exception as e:
                    print(e)
                    # add error reaction
                    await message.add_reaction("❌")
                    if isinstance(e, Forbidden):
                        await message.channel.send("🔥 Sorry, I can't reply message in this channel. "
                                                   f"Please check my permission. Details: `{Forbidden}`")
                    else:
                        await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

                finally:
                    # set is not replying
                    cursor.execute("UPDATE ReplyAt SET replying = FALSE WHERE Guild_ID = %s AND user = %s",
                                   (message.guild.id, message.author.id))
                    db.commit()

                    # remove loading reaction
                    await message.remove_reaction("<a:loading:1112646025090445354>", client.user)
            return

        # check if message is sent in set channel
        cursor.execute("SELECT * FROM ReplyThis WHERE Guild_ID = %s AND channel_ID = %s AND replying != TRUE",
                       (message.guild.id, message.channel.id))
        result = cursor.fetchone()

        if result is not None:
            # set is replying
            cursor.execute("UPDATE ReplyThis SET replying = TRUE WHERE Guild_ID = %s AND channel_ID = %s",
                           (message.guild.id, message.channel.id))
            db.commit()
            conversation = result[2]

            # reply message
            try:
                # add loading reaction
                await message.add_reaction("<a:loading:1112646025090445354>")
                msg = await message.reply("<a:loading:1112646025090445354>")

                await prompt.ask(conversation, msg, message.content)
                await message.add_reaction("✅")

            except Exception as e:
                print(e)
                # add error reaction
                await message.add_reaction("❌")
                if isinstance(e, Forbidden):
                    await message.channel.send("🔥 Sorry, I can't reply message in this channel. "
                                               f"Please check my permission. Details: `{Forbidden}`")
                else:
                    await message.channel.send("🔥 Oh no! Something went wrong. Please try again later.")

            finally:
                # set is not replying
                cursor.execute("UPDATE ReplyThis SET replying = FALSE WHERE Guild_ID = %s AND channel_ID = %s",
                               (message.guild.id, message.channel.id))
                db.commit()

                # remove loading reaction
                await message.remove_reaction("<a:loading:1112646025090445354>", client.user)
