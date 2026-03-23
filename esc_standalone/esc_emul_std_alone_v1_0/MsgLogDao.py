import sqlite3
from datetime import datetime, timedelta

class MsgLogDao:
    def __init__(self, db_path):
        self.db_path = "esc_std_alone_msg_log.sqlite3"#db_path
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 딕셔너리처럼 결과 사용
            print("MsgLogDao : Connected to SQLite database")
            self.create_table_if_not_exists()
        except sqlite3.Error as e:
            print(f"Connection error: {e}")

    def create_table_if_not_exists(self):
        try:
            create_query = """
            CREATE TABLE IF NOT EXISTS TD_SYSTEM_MSG_LOG (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                DEVICE_ID TEXT,
                SOURC TEXT,
                TRGT TEXT,
                MSSAGE_ID TEXT,
                MSSAGE TEXT,
                MSSAGE_SE TEXT,
                REGIST_DT DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.connection.execute(create_query)
            self.connection.commit()
            print("Table 'TD_SYSTEM_MSG_LOG' checked/created.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert(self, device_id, source, target, mssage_id, mssage, mssage_se):
        try:
            with self.connection:
                query = """INSERT INTO TD_SYSTEM_MSG_LOG 
                           (DEVICE_ID, SOURC, TRGT, MSSAGE_ID, MSSAGE, MSSAGE_SE) 
                           VALUES (?, ?, ?, ?, ?, ?)"""
                self.connection.execute(query, (device_id, source, target, mssage_id, mssage, mssage_se))
                return True
        except sqlite3.Error as e:
            print(e)
            return False

    def list_by_deviceid(self, device_id, start=None, end=None):
        try:
            cursor = self.connection.cursor()
            one_hour_ago = datetime.now() - timedelta(hours=10)
            if start is None:
                query = """
                    SELECT * FROM TD_SYSTEM_MSG_LOG 
                    WHERE (DEVICE_ID = ? OR 1=1) 
                        AND REGIST_DT >= ?
                    ORDER BY REGIST_DT ASC"""
                cursor.execute(query, (device_id, one_hour_ago))
            else:
                query = """
                    SELECT * FROM TD_SYSTEM_MSG_LOG 
                    WHERE (DEVICE_ID = ? OR 1=1) 
                        AND REGIST_DT BETWEEN ? AND ?
                    ORDER BY REGIST_DT ASC"""
                cursor.execute(query, (device_id, start, end))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error listing by device ID: {e}")
            return None

    def list_by_part(self, start=1, direction='DOWN', length=100):
        try:
            cursor = self.connection.cursor()
            if direction == "UP":
                query = f"""
                    SELECT * FROM (
                        SELECT * FROM TD_SYSTEM_MSG_LOG
                        WHERE ID < ?
                        ORDER BY ID DESC
                        LIMIT ?
                    ) 
                    ORDER BY ID ASC"""
                cursor.execute(query, (start, length))
            elif direction == "DOWN":
                query = """
                    SELECT *
                    FROM TD_SYSTEM_MSG_LOG
                    WHERE ID > ?
                    ORDER BY ID ASC
                    LIMIT ?"""
                cursor.execute(query, (start, length))
            elif direction == "LAST":
                query = f"""
                    SELECT * FROM (
                        SELECT *
                        FROM TD_SYSTEM_MSG_LOG
                        ORDER BY ID DESC
                        LIMIT ?
                    )
                    ORDER BY ID ASC"""
                cursor.execute(query, (length,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error listing by part: {e}")
            return None

    def close(self):
        if self.connection:
            self.connection.close()