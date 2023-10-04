import logging
import os
import sqlite3

import discord
import redis.asyncio as redis
from discord.ext import commands
from dotenv import load_dotenv
from revChatGPT.V1 import AsyncChatbot

import DatabaseHelper
import share_var
from BotCmd import set_command
from BotEvent import set_event_lister


# starting bot
def start(bot_name="ChatGPT"):
    logging.basicConfig(level=logging.DEBUG)  # set logging level
    handler = logging.FileHandler(filename='../database/bot.log', encoding='utf-8', mode='w')  # create log file handler
    logging.info(f"{bot_name} Discord Bot is starting... (v0.2.2)")

    # create ChatGPT chatbot
    share_var.chatbot_conn = AsyncChatbot(config={"access_token": os.getenv("CHATGPT_TOKEN")})
    logging.info(f"{bot_name} ChatGPT is connected.")

    # create mysql connection
    logging.info(f"{bot_name} Connecting to MySQL...")
    share_var.sql_conn = sqlite3.connect("../database/nekogpt_database.db")
    logging.info(f"{bot_name} MySQL is connected.")

    # check database update
    logging.info(f"{bot_name} Checking database update...")
    DatabaseHelper.database_helper(share_var.sql_conn, bot_name)

    # create intents
    intents = discord.Intents.default()
    intents.message_content = True

    # create redis connection
    logging.info(f"{bot_name} Connecting to Redis...")
    share_var.redis_conn = redis.Redis(host='redis', port=6379, db=0)
    logging.info(f"{bot_name} Redis is connected.")

    client = commands.Bot(command_prefix="!", intents=intents)  # create bot
    set_event_lister(client, bot_name)  # set event listener
    set_command(client, bot_name)  # set command listener

    client.run(os.getenv("DISCORD_TOKEN"), log_handler=handler, log_level=logging.INFO)  # run bot


# run bot
if __name__ == "__main__":
    load_dotenv("../database/.env")  # load .env file
    start(os.getenv("BOT_NAME"))
