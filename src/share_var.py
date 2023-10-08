from sqlite3 import Connection

from redis.asyncio import Redis
from revChatGPT.V1 import AsyncChatbot

sql_conn: Connection = None
redis_conn: Redis = None
chatbot_conn: AsyncChatbot = None
