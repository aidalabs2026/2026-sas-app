import sqlite3
import os

class SysPropDao:
    def __init__(self, db_path):
        self.db_path = "esc_std_alone_sys_prop.sqlite3"#db_path
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            print("SYSPROP : Connected to SQLite database")
            self.create_table_if_not_exists()
        except sqlite3.Error as e:
            print(f"Connection error: {e}")

    def create_table_if_not_exists(self):
        """ TD_SYSTEM_PROP 테이블이 없으면 생성 """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TD_SYSTEM_PROP (
                    SKEY TEXT PRIMARY KEY,
                    VALUE TEXT
                )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def prop_list(self):
        try:
            cursor = self.connection.cursor()
            query = "SELECT SKEY, VALUE FROM TD_SYSTEM_PROP"
            cursor.execute(query)
            result = cursor.fetchall()
            return [dict(row) for row in result]
        except sqlite3.Error as e:
            print(f"Error fetching properties: {e}")
            return False

    def prop_get(self, key):
        try:
            cursor = self.connection.cursor()
            query = "SELECT VALUE FROM TD_SYSTEM_PROP WHERE SKEY = ?"
            cursor.execute(query, (key,))
            result = cursor.fetchone()
            return result['VALUE'] if result else None
        except sqlite3.Error as e:
            print(f"Error fetching property: {e}")
            return False

    def prop_update(self, key, value):
        try:
            cursor = self.connection.cursor()
            # SQLite UPSERT 문법
            # 먼저 업데이트 시도
            cursor.execute("UPDATE TD_SYSTEM_PROP SET VALUE = ? WHERE SKEY = ?", (value, key))
            if cursor.rowcount == 0:  # 업데이트된 행이 없으면 (해당 키가 없으면)
                cursor.execute("INSERT INTO TD_SYSTEM_PROP (SKEY, VALUE) VALUES (?, ?)", (key, value))
            self.connection.commit()

            return True
        except sqlite3.Error as e:
            print(f"Error updating property: {e}")
            return False

    def close(self):
        if self.connection:
            self.connection.close()