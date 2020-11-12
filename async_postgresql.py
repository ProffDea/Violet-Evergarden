import asyncpg
import os

class async_database(object):

    # Status: Unfinished

    # Connecting to postgresql database asynchronously
    # Credentials that must be filled are as follows:
    # DB_HOST
    # DB_USER
    # DB_PASSWORD
    # DATABASE

    async def connect(self):
        self.con = await asyncpg.connect(host=os.getenv('DB_HOST'),
                                        user=os.getenv('DB_USER'),
                                        password=os.getenv('DB_PASSWORD'),
                                        database=os.getenv('DATABASE'))

    async def close(self):
        await self.con.close()