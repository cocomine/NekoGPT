import logging

import discord
from discord.ext import commands

import share_var
from Prompt import Prompt
from Reply import Reply


# set event listener
def set_event_lister(client: commands.Bot, bot_name: str):
    db = share_var.sql_conn
    r = share_var.redis_conn
    prompt = Prompt(share_var.chatbot_conn)
    reply = Reply(db, share_var.chatbot_conn, client)

    @client.event
    async def setup_hook():
        pass

    @client.event
    async def on_ready():
        logging.info(f'{client.user} has connected to Discord!')
        try:
            synced = await client.tree.sync()
            logging.info(f"Synced {len(synced)} commands")
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                   name=f"@{bot_name} chat with me!"))
        except Exception as e:
            logging.error(e)

    # add into server
    @client.event
    async def on_guild_join(guild: discord.Guild):
        logging.info(f"Joined {guild.name} server. ({guild.id})")

        # add into database
        cursor = db.cursor()
        cursor.execute("INSERT INTO Guild (Guild_ID) VALUES (?)", (guild.id,))
        db.commit()

    # remove from server
    @client.event
    async def on_guild_remove(guild: discord.Guild):
        logging.info(f"Left {guild.name} server. ({guild.id})")
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT * FROM ReplyThis WHERE Guild_ID = ?", (guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = ?", (guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        # remove from database
        cursor.execute("DELETE FROM Guild WHERE Guild_ID = ?", (guild.id,))
        db.commit()

    @client.event
    async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT * FROM ReplyThis WHERE Channel_ID = ? AND Guild_ID = ?",
                       (channel.id, channel.guild.id))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        cursor.execute("DELETE FROM ReplyThis WHERE channel_ID = ? AND Guild_ID = ?", (channel.id, channel.guild.id))
        db.commit()

    # when message is sent
    @client.event
    async def on_message(message: discord.Message):
        logging.info(f"Message from {message.author} ({message.author.id}): {message.content}")

        if message.author == client.user:
            return

        # if message is sent in DM
        if isinstance(message.channel, discord.DMChannel):
            await reply.dm(message)
            return

        # if message is @mention bot
        if client.user.mentioned_in(message):
            await reply.mention(message)
            return

        # if message is sent in set channel
        await reply.channel(message)
