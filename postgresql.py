import os
import psycopg2

class database(object):

    # Status: Finished

    # Connecting to postgresql database
    # Credentials that must be filled are as follows:
    # DATABASE
    # DB_USER
    # DB_PASSWORD

    def connect(self):

        # Attempts connection if running on heroku otherwise, connects locally with credentials
        # https://dashboard.heroku.com/apps
        
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