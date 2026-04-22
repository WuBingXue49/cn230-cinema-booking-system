import mysql.connector
from config import config

def get_db_connection():
    return mysql.connector.connect(**config)