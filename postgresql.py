import os
import psycopg2

class database(object):
    def connect(self):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            self.con = psycopg2.connect(DATABASE_URL, sllmode='require')
        except:
            self.con = psycopg2.connect(database=os.getenv('DATABASE'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
        self.cur = self.con.cursor()
        return

    def close(self):
        self.con.commit()
        self.cur.close()
        self.con.close()
        return