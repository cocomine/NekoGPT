import asyncio
import logging

import discord
from discord import Color, Embed
from discord.ext import commands

import share_var
from Prompt import Prompt


# set command listener
def set_command(client: commands.Bot, bot_name: str):
    tree = client.tree
    r = share_var.redis_conn
    db = share_var.sql_conn
    prompt = Prompt(share_var.chatbot_conn)

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
        cursor.execute("SELECT conversation FROM ReplyThis WHERE Guild_ID = ? AND channel_ID = ?",
                       (interaction.guild.id, interaction.channel.id,))
        result = cursor.fetchone()

        if result is None:
            # start conversation
            conversation = await prompt.start_new_conversation(interaction.channel.name)
            await asyncio.sleep(3)

            # add into database
            cursor.execute("INSERT INTO ReplyThis VALUES (?, ?, ?, FALSE)",
                           (interaction.guild.id, interaction.channel.id, conversation))
            db.commit()
            await interaction.followup.send(f"🟢 {client.user} will reply all message in this channel. "
                                            f"The channel will have its own conversation.")

        else:
            # stop conversation
            if result[0] is not None:
                try:
                    await prompt.stop_conversation(result[0])
                except Exception as e:
                    logging.warning(e)

            # remove from database
            cursor.execute("DELETE FROM ReplyThis WHERE Guild_ID = ? AND channel_ID = ?",
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
        cursor.execute("SELECT * FROM Guild WHERE Guild_ID = ? AND replyAt = TRUE", (interaction.guild.id,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("UPDATE Guild SET replyAt = TRUE WHERE Guild_ID = ?", (interaction.guild.id,))
            db.commit()
            await interaction.followup.send(f"🟢 {client.user} will reply <@{client.user.id}> message. "
                                            f"Each user will have its own conversation.")
        else:
            # stop conversation
            cursor.execute("SELECT conversation FROM ReplyAt WHERE Guild_ID = ?", (interaction.guild.id,))
            result = cursor.fetchall()
            for row in result:
                if row[2] is not None:
                    try:
                        await prompt.stop_conversation(row[0])
                    except Exception as e:
                        logging.warning(e)

            # remove from database
            cursor.execute("DELETE FROM ReplyAt WHERE Guild_ID = ?", (interaction.guild.id,))
            cursor.execute("UPDATE Guild SET replyAt = FALSE WHERE Guild_ID = ?", (interaction.guild.id,))
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

        # Restart ReplyThis conversation
        cursor.execute("SELECT conversation, channel_ID FROM ReplyThis WHERE Guild_ID = ?", (interaction.guild.id,))
        result = cursor.fetchall()

        # send process message
        followup = await interaction.followup.send(
            f"<a:loading:1112646025090445354> {client.user} resting channel conversation (0/{len(result)})",
            ephemeral=True)

        for i in range(len(result)):
            row = result[i]
            if row[0] is not None:
                try:
                    await prompt.stop_conversation(row[0])
                except Exception as e:
                    logging.warning(e)

            # start new conversation
            conversation = await prompt.start_new_conversation()
            cursor.execute("UPDATE ReplyThis SET conversation = ? WHERE Guild_ID = ? AND channel_ID = ?",
                           (conversation, interaction.guild.id, row[1],))

            await followup.edit(
                content=f"<a:loading:1112646025090445354> {client.user} resting channel conversation ({i + 1}/{len(result)})")
        db.commit()

        # Stop ReplyAt conversation
        cursor.execute("SELECT conversation FROM ReplyAt WHERE Guild_ID = ?", (interaction.guild.id,))
        result = cursor.fetchall()

        # send process message
        await followup.edit(
            content=f"<a:loading:1112646025090445354> {client.user} stopping mention conversation (0/{len(result)})")

        for i in range(len(result)):
            row = result[i]
            if row[0] is not None:
                try:
                    await prompt.stop_conversation(row[0])
                except Exception as e:
                    logging.warning(e)

            await followup.edit(
                content=f"<a:loading:1112646025090445354> {client.user} stopping mention conversation ({i + 1}/{len(result)})")

        # delete conversation
        cursor.execute("DELETE FROM ReplyAt WHERE Guild_ID = ?", (interaction.guild.id,))
        db.commit()

        await followup.edit(content=f"🔄 {client.user} has reset all conversation in this server.")

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
        cursor.execute("SELECT * FROM DM WHERE User = ?", (interaction.user.id,))
        result = cursor.fetchone()

        # stop conversation
        if result is not None:
            if result[1] is not None:
                await prompt.stop_conversation(result[1])

            # reset conversation
            conversation = await prompt.start_new_conversation()
            cursor.execute("UPDATE DM SET conversation = ? WHERE User = ?",
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
        cursor.execute("SELECT channel_ID FROM ReplyThis WHERE Guild_ID = ?", (interaction.guild.id,))
        result = cursor.fetchall()

        _reply_this = "🔴 Not set any channel"
        if len(result) != 0:
            _reply_this = ", ".join(f"<#{x[0]}>" for x in result)

        # Get @mention is enabled or not
        cursor.execute("SELECT replyAt FROM Guild WHERE Guild_ID = ?", (interaction.guild.id,))
        result = cursor.fetchone()

        _reply_at = "🔴 Disabled"
        if result[0] == 1:
            _reply_at = "🟢 Enabled"

        # Print help menu
        help_embed = Embed(title=f"{client.user} | Help menu", color=Color.yellow())
        help_embed.set_author(icon_url=client.user.avatar.url, name=client.user)
        help_embed.add_field(name="</help:1114586386465574912>", value=f"Show {client.user} help menu", inline=False)
        help_embed.add_field(name="</dm-chat:1112076933291835443>", value=f"Start DM chat with {client.user}",
                             inline=False)
        help_embed.add_field(name="</reply-this:1112069656178610266>",
                             value=f"Set {client.user} reply all message in {interaction.channel.mention} *(Administrator only)*",
                             inline=False)
        help_embed.add_field(name="</reply-at:1112076933291835442>",
                             value=f"Set {client.user} reply @mention message in this server *(Administrator only)*",
                             inline=False)
        help_embed.add_field(name="</reset:1112663618811600916>",
                             value=f"Reset {client.user} all conversation in this server *(Administrator only)*",
                             inline=False)
        help_embed.add_field(name="</reset-dm:1112775422862700615>",
                             value=f"Reset {client.user} DM conversation *(DM only)*", inline=False)
        help_embed.add_field(name="", value="", inline=False)
        help_embed.add_field(name="Current Settings", value="The server's current settings", inline=False)
        help_embed.add_field(name="reply-this", value=_reply_this, inline=True)
        help_embed.add_field(name="reply-at", value=_reply_at, inline=True)

        await interaction.followup.send(ephemeral=True, embed=help_embed)
