import logging

import discord
from discord.ext import commands

import share_var
from Prompt import Prompt
from Reply import Reply


# set event listener
def set_event_lister(client: commands.Bot, bot_name: str):
    """
    Set event listener
    :param client: Discord bot client
    :param bot_name: Bot name
    """

    db = share_var.sql_conn  # get database connection
    r = share_var.redis_conn  # get redis connection
    prompt = Prompt(share_var.chatbot_conn)  # create prompt object
    reply = Reply(client)  # create reply object

    @client.event
    async def setup_hook():
        """
        Setup hook
        """
        await r.flushdb()
        logging.info(f"{bot_name} Redis cache is cleared.")

    @client.event
    async def on_ready():
        """
        When bot is ready
        """
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
        """
        When bot is added into server
        :param guild: Discord server(Guild) object
        """
        logging.info(f"Joined {guild.name} server. ({guild.id})")

        # add into database
        cursor = db.cursor()
        await r.hset("Guild.replyAt", str(guild.id), "1")
        cursor.execute("INSERT INTO Guild (Guild_ID) VALUES (?)", (guild.id,))
        db.commit()

    # remove from server
    @client.event
    async def on_guild_remove(guild: discord.Guild):
        """
        When bot is removed from server
        :param guild: Discord server(Guild) object
        """
        logging.info(f"Left {guild.name} server. ({guild.id})")
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT conversation, channel_ID FROM ReplyThis WHERE Guild_ID = ?", (guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[0] is not None:
                try:
                    await r.hdel("ReplyThis", f"{guild.id}.{row[1]}")  # set into redis
                    await prompt.stop_conversation(row[0])
                except Exception as e:
                    logging.warning(e)

        # stop @mention conversation
        cursor.execute("SELECT conversation, user FROM ReplyAt WHERE Guild_ID = ?", (guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[0] is not None:
                try:
                    await r.hdel("ReplyAt", f"{guild.id}.{row[1]}")  # remove from redis
                    await prompt.stop_conversation(row[0])
                except Exception as e:
                    logging.warning(e)

        # remove from database
        await r.hdel("Guild.replyAt", str(guild.id))  # remove from redis
        cursor.execute("DELETE FROM Guild WHERE Guild_ID = ?", (guild.id,))
        db.commit()

    @client.event
    async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
        """
        When channel is deleted
        :param channel: Discord channel object
        """
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT conversation FROM ReplyThis WHERE Channel_ID = ? AND Guild_ID = ?",
                       (channel.id, channel.guild.id))
        result = cursor.fetchall()
        for row in result:
            if row[0] is not None:
                await r.hdel("ReplyThis", f"{channel.guild.id}.{channel.id}")  # set into redis
                await prompt.stop_conversation(row[0])

        cursor.execute("DELETE FROM ReplyThis WHERE channel_ID = ? AND Guild_ID = ?", (channel.id, channel.guild.id))
        db.commit()

    # when message is sent
    @client.event
    async def on_message(message: discord.Message):
        """
        When message is sent
        :param message: Discord message object
        """
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
