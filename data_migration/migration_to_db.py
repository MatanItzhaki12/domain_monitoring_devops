import psycopg2

DB_PARAMS = {
    "dbname": "storedb",
    "user": "myuser",
    "password": "mypassword",
    "host": "localhost",
    "port": 5432,
}


def connect_db():
    return psycopg2.connect(**DB_PARAMS)
