import os
from dotenv import load_dotenv

load_dotenv()

config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': '024589',
#     'database': 'cimema'
# }
