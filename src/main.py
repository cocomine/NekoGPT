import logging
import os
import signal

import discord
from discord.ext import commands

from mysql.connector import connect
from dotenv import load_dotenv
from revChatGPT.V1 import AsyncChatbot

from BotEvent import set_event_lister
from BotCmd import set_command


# starting bot
def start(bot_name="ChatGPT"):
    logging.basicConfig(level=logging.DEBUG)  # set logging level
    handler = logging.FileHandler(filename='../bot.log', encoding='utf-8', mode='w')  # create log file handler
    logging.info(f"{bot_name} Discord Bot is starting... (v0.1.6)")

    # create ChatGPT chatbot
    chatbot = AsyncChatbot(config={
        "access_token": os.getenv("CHATGPT_TOKEN")
    })
    logging.info(f"{bot_name} ChatGPT is connected.")

    # create mysql connection
    mydb = connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    logging.info(f"{bot_name} MySQL is connected.")

    # create intents
    intents = discord.Intents.default()
    intents.message_content = True

    client = commands.Bot(command_prefix="!", intents=intents)  # create bot
    set_event_lister(client, mydb, chatbot, bot_name)  # set event listener
    set_command(client, mydb, chatbot, bot_name)  # set command listener

    client.run(os.getenv("DISCORD_TOKEN"), log_handler=handler, log_level=logging.INFO)  # run bot


# run bot
if __name__ == "__main__":
    load_dotenv()  # load .env file
    start(os.getenv("BOT_NAME"))
