from sqlite3 import Connection

from redis.asyncio import Redis
from revChatGPT.V1 import AsyncChatbot

sql_conn: Connection = None  # Database connection
redis_conn: Redis = None  # Redis connection
chatbot_conn: AsyncChatbot = None  # ChatGPT connection
