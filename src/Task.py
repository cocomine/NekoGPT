import logging

from discord.ext import commands, tasks
from mysql.connector import connect


class Task(commands.Cog):
    def __init__(self, bot: commands.Bot, db: connect):
        self.bot = bot
        self.db = db
        self.db_reconnect.start()

    def cog_unload(self):
        self.db_reconnect.cancel()

    @tasks.loop(hours=2, count=None)
    async def db_reconnect(self):
        if not self.db.is_connected():
            logging.info(f"{self.bot.user} Reconnecting to MySQL...")
            self.db.reconnect(attempts=5, delay=1)
            logging.info(f"{self.bot.user} Reconnected to MySQL.")

    @db_reconnect.before_loop
    async def before_db_reconnect(self):
        await self.bot.wait_until_ready()
        logging.info(f"{self.bot.user} task is setup.")
