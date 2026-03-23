import pymysql
import time

class Database:
    def __init__(self, host, user, password, database, max_retries=3, retry_delay=2):
        self.connection = None
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connect()

    def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                print("Connected to MySQL database")
                return
            except pymysql.MySQLError as e:
                print(f"Connection failed: {e}. Retrying in {self.retry_delay} seconds...")
                retries += 1
                time.sleep(self.retry_delay)

        print("Failed to connect to the database after multiple attempts.")
        raise Exception("Could not connect to the database.")

    def execute_query(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.lastrowid  # Return last inserted ID
        except pymysql.MySQLError as e:
            print(f"Error: {e}")

    def fetch_all(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return []

    def fetch_one(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return None

    def insert(self, table, **kwargs):
        columns = ', '.join(kwargs.keys())
        placeholders = ', '.join(['%s'] * len(kwargs))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute_query(query, tuple(kwargs.values()))

    def update(self, table, id_column, id_value, **kwargs):
        set_clause = ', '.join([f"{key} = %s" for key in kwargs.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {id_column} = %s"
        return self.execute_query(query, tuple(list(kwargs.values()) + [id_value]))

    def delete(self, table, id_column, id_value):
        query = f"DELETE FROM {table} WHERE {id_column} = %s"
        return self.execute_query(query, (id_value,))

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")
