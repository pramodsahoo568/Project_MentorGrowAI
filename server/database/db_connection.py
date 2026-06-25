import psycopg2
import os

'''
bash commands run on server:
export DB_HOST=192.168.1.10
export DB_NAME=prod_db
export DB_USER=admin
export DB_PASSWORD=securepass
'''
## we use environment variables DB_HOST   so that rhe user name and db password does not get stored in Github

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DSN = os.getenv("POSTGRES_CONNECTION")

def get_connection():

    if not POSTGRES_DSN:
        raise Exception(
            "POSTGRES_DSN missing in .env"
        )
    try:
        conn = psycopg2.connect(
            POSTGRES_DSN
        )
        print("✅ PostgreSQL Connected")
        return conn
    except Exception as e:
        print(
            f" PostgreSQL Connection Error: {e}"
        )
        raise