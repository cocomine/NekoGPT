from sqlite3 import Connection

from redis.asyncio import Redis
from revChatGPT.V1 import AsyncChatbot

sql_conn: Connection
redis_conn: Redis
chatbot_conn: AsyncChatbot
