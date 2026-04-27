import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "cinema"),
}
