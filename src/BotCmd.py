import asyncio
import logging

import discord
from discord import Color, Embed
from discord.ext import commands
from mysql.connector import connect
from revChatGPT.V1 import AsyncChatbot

from Prompt import Prompt


def set_command(client: commands.Bot, db: connect, chatbot: AsyncChatbot, bot_name: str):
    tree = client.tree
    prompt = Prompt(chatbot)

    # ping command
    @tree.command(name="ping", description="Check bot latency")
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def ping(interaction: discord.Interaction):
        logging.info(f"{interaction.user} pinged {client.user}")
        await interaction.response.send_message(f"Pong! {round(client.latency * 1000)}ms", ephemeral=True)

    # Set Enable or Disable reply all message in channel
    @tree.command(name="reply-this", description=f"Set Enable or Disable {bot_name} reply all message in this channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, send_messages=True, use_external_emojis=True,
                                  add_reactions=True)
    async def reply_this(interaction: discord.Interaction):
        logging.info(f"{interaction.user} set {interaction.guild} reply all message in {interaction.channel}")
        await interaction.response.defer(ephemeral=True)

        cursor = db.cursor()
        cursor.execute("SELECT * FROM ReplyThis WHERE Guild_ID = %s AND channel_ID = %s",
                       (interaction.guild.id, interaction.channel.id,))
        result = cursor.fetchone()

        if result is None:
            # start conversation
            conversation = await prompt.start_new_conversation(interaction.channel.name)
            await asyncio.sleep(3)

            # add into database
            cursor.execute("INSERT INTO ReplyThis VALUES (%s, %s, %s, FALSE)",
                           (interaction.guild.id, interaction.channel.id, conversation))
            db.commit()
            await interaction.followup.send(f"🟢 {client.user} will reply all message in this channel. "
                                            f"The channel will have its own conversation.")

        else:
            # stop conversation
            if result[2] is not None:
                await prompt.stop_conversation(result[2])

            # remove from database
            cursor.execute("DELETE FROM ReplyThis WHERE Guild_ID = %s AND channel_ID = %s",
                           (interaction.guild.id, interaction.channel.id))
            db.commit()
            await interaction.followup.send(f"🔴 {client.user} will not reply all message in this channel")

    # Set Enable or Disable reply @mentions message in server
    @tree.command(name="reply-at", description=f"Set Enable or Disable {bot_name} reply @{bot_name} message")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, send_messages=True, use_external_emojis=True,
                                  add_reactions=True)
    async def reply_at(interaction: discord.Interaction):
        logging.info(f"{interaction.user} set {interaction.guild} reply @{client.user} message")
        await interaction.response.defer(ephemeral=True)

        cursor = db.cursor()
        cursor.execute("SELECT * FROM Guild WHERE Guild_ID = %s AND replyAt = TRUE", (interaction.guild.id,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("UPDATE Guild SET replyAt = TRUE WHERE Guild_ID = %s", (interaction.guild.id,))
            db.commit()
            await interaction.followup.send(f"🟢 {client.user} will reply <@{client.user.id}> message. "
                                            f"Each user will have its own conversation.")
        else:
            # stop conversation
            cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = %s", (interaction.guild.id,))
            result = cursor.fetchall()
            for row in result:
                if row[2] is not None:
                    await prompt.stop_conversation(row[2])

            # remove from database
            cursor.execute("DELETE FROM ReplyAt WHERE Guild_ID = %s", (interaction.guild.id,))
            db.commit()
            cursor.execute("UPDATE Guild SET replyAt = FALSE WHERE Guild_ID = %s", (interaction.guild.id,))
            db.commit()

            await interaction.followup.send(f"🔴 {client.user} will not reply <@{client.user.id}> message")

    # Start DM message
    @tree.command(name="dm-chat", description=f"Start chat with {bot_name} in DM")
    @commands.guild_only()
    async def dm_chat(interaction: discord.Interaction):
        logging.info(f"{interaction.user} start chat with {client.user} in DM")

        try:
            await interaction.user.send(
                f"Hello, I'm {client.user}, I can chat with you. Just send me message and I will reply it.")
            await interaction.response.send_message(f"📨 {client.user} will send you message in DM", ephemeral=True)
        except Exception as e:
            if isinstance(e, discord.Forbidden):
                await interaction.response.send_message(f"❌ {client.user} can't send you message in DM. "
                                                        f"Make sure you have private messages enabled.",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message("🔥 Oh no! Something went wrong. Please try again later.")

    # Reset all conversation in server
    @tree.command(name="reset", description=f"Reset all conversation in this server")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.bot_has_permissions(read_message_history=True, send_messages=True, use_external_emojis=True,
                                  add_reactions=True)
    async def reset(interaction: discord.Interaction):
        logging.info(f"{interaction.user} reset all conversation in {interaction.guild}")
        await interaction.response.defer(ephemeral=True)
        cursor = db.cursor()

        # stop all conversation
        cursor.execute("SELECT * FROM ReplyThis WHERE Guild_ID = %s", (interaction.guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

            conversation = await prompt.start_new_conversation()
            cursor.execute("UPDATE ReplyThis SET conversation = %s WHERE Guild_ID = %s",
                           (conversation, interaction.guild.id,))
            db.commit()

        cursor.execute("SELECT * FROM ReplyAt WHERE Guild_ID = %s", (interaction.guild.id,))
        result = cursor.fetchall()
        for row in result:
            if row[2] is not None:
                await prompt.stop_conversation(row[2])

        cursor.execute("DELETE FROM ReplyAt WHERE Guild_ID = %s", (interaction.guild.id,))
        db.commit()

        await interaction.followup.send(f"🔄 {client.user} has reset all conversation in this server",
                                        ephemeral=True)

    # reset DM conversation
    @tree.command(name="reset-dm", description=f"Reset conversation in DM")
    @commands.bot_has_permissions(send_messages=True)
    @commands.dm_only()
    async def reset_dm(interaction: discord.Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(f"❌ This command only can be used in DM", ephemeral=True)
            return

        logging.info(f"{interaction.user} reset conversation in DM")
        await interaction.response.defer(ephemeral=True)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM DM WHERE User = %s", (interaction.user.id,))
        result = cursor.fetchone()

        # stop conversation
        if result is not None:
            if result[1] is not None:
                await prompt.stop_conversation(result[1])

            # reset conversation
            conversation = await prompt.start_new_conversation()
            cursor.execute("UPDATE DM SET conversation = %s WHERE User = %s",
                           (conversation, interaction.user.id,))
            db.commit()

        await interaction.followup.send(f"🔄 {client.user} has reset conversation in DM")

    # command help
    @tree.command(name="help", description=f"Show {bot_name} help menu")
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def help(interaction: discord.Interaction):
        logging.info(f"{interaction.user} show help menu")
        await interaction.response.defer()
        cursor = db.cursor()

        # Get all reply channel
        cursor.execute("SELECT channel_ID FROM ReplyThis WHERE Guild_ID = %s", (interaction.guild.id,))
        result = cursor.fetchall()

        ReplyThis = ""
        for row in result:
            ReplyThis += f"<#{row[0]}>, "

        # Get @mention is enabled or not
        cursor.execute("SELECT replyAt FROM Guild WHERE Guild_ID = %s", (interaction.guild.id,))
        result = cursor.fetchone()

        ReplyAt = "Disabled"
        if result[0] is True:
            ReplyAt = "Enabled"

        # Print help menu
        help_embed = Embed(title=f"{client.user} | Help menu", color=Color.yellow())
        help_embed.set_author(icon_url=client.user.avatar.url, name=client.user)
        help_embed.add_field(name="</help:1114586386465574912>", value=f"Show {client.user} help menu", inline=False)
        help_embed.add_field(name="</dm-chat:1112076933291835443>", value=f"Start DM chat with {client.user}", inline=False)
        help_embed.add_field(name="</reply-this:1112069656178610266>", value=f"Set {client.user} reply all message in {interaction.channel.mention} *(Administrator only)*", inline=False)
        help_embed.add_field(name="</reply-at:1112076933291835442>", value=f"Set {client.user} reply @mention message in this server *(Administrator only)*", inline=False)
        help_embed.add_field(name="</reset:1112663618811600916>", value=f"Reset {client.user} all conversation in this server *(Administrator only)*", inline=False)
        help_embed.add_field(name="</reset-dm:1112775422862700615>", value=f"Reset {client.user} DM conversation *(DM only)*", inline=False)
        help_embed.add_field(name="", value="", inline=False)
        help_embed.add_field(name="The server's current settings", value="", inline=False)
        help_embed.add_field(name="reply-this", value=ReplyThis, inline=True)
        help_embed.add_field(name="reply-at", value=f"`{ReplyAt}`", inline=True)

        await interaction.followup.send(ephemeral=True, embed=help_embed)

    # join voice channel
    @tree.command(name="join", description=f"Join voice channel")
    @commands.guild_only()
    @commands.bot_has_permissions(connect=True, speak=True)
    async def join(interaction: discord.Interaction):
        logging.info(f"{interaction.user} join voice channel")
        await interaction.response.defer()
        if interaction.author.voice is None:
            await interaction.followup.send(f"❌ You are not in any voice channel", ephemeral=True)
            return

        await interaction.author.voice.channel.connect()
        await interaction.followup.send(f"🔊 {client.user} has joined {interaction.author.voice.channel.mention}")

    # leave voice channel
    @tree.command(name="leave", description=f"Leave voice channel")
    @commands.guild_only()
    @commands.bot_has_permissions(connect=True, speak=True)
    async def leave(interaction: discord.Interaction):
        logging.info(f"{interaction.user} leave voice channel")
        await interaction.response.defer()
        if interaction.guild.voice_client is None:
            await interaction.followup.send(f"❌ I'm not in any voice channel", ephemeral=True)
            return

        await interaction.guild.voice_client.disconnect()
        await interaction.followup.send(f"🔊 {client.user} has left {interaction.guild.voice_client.channel.mention}")