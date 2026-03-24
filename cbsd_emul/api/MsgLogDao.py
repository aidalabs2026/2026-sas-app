import pymysql
import json
from datetime import datetime, timedelta
import pytz

class MsgLogDao:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.connect()
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                # 🔽 여기에 추가
                connect_timeout=10,  # 연결 시도 제한 시간
                read_timeout=30,  # 읽기 타임아웃
                write_timeout=30,  # 쓰기 타임아웃
                max_allowed_packet=1024 * 1024 * 64  # 64MB로 설정 (서버에서 허용해야 함)
            )
            print("MsgLogDao : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def insert(self, device_id, source, target, mssage_id, mssage, mssage_se):
        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_SYSTEM_MSG_LOG (DEVICE_ID, SOURC, TRGT, MSSAGE_ID, MSSAGE, MSSAGE_SE) 
                                                   VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(query,
                               (device_id, source, target, mssage_id, mssage, mssage_se))

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False


    def list_by_deviceid(self, device_id, start=None, end=None, limit=20, light=False):
        try:
            with self.connection.cursor() as cursor:
                one_hour_ago = datetime.now() - timedelta(hours=1)
                cols = "ID, DEVICE_ID, SOURC, TRGT, MSSAGE_ID, MSSAGE_SE, REGIST_DT" if light else "*"
                if start is None:
                    query = f"""SELECT {cols} FROM TD_SYSTEM_MSG_LOG
                                WHERE DEVICE_ID = %s AND REGIST_DT >= %s
                                ORDER BY REGIST_DT DESC LIMIT %s"""
                    cursor.execute(query, (device_id, one_hour_ago, limit))
                else:
                    query = f"""SELECT {cols} FROM TD_SYSTEM_MSG_LOG
                                WHERE DEVICE_ID = %s AND REGIST_DT BETWEEN %s AND %s
                                ORDER BY REGIST_DT DESC LIMIT %s"""
                    cursor.execute(query, (device_id, start, end, limit))

                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def get_message_by_id(self, msg_id):
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT * FROM TD_SYSTEM_MSG_LOG WHERE ID = %s"
                cursor.execute(query, (msg_id,))
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return None

    def list_by_part(self, start = 1, direction = 'DOWN', length = 100):
        try:
            with self.connection.cursor() as cursor:
                if direction == "UP":
                    query = f"""
                        SELECT * FROM (
                            SELECT *
                            FROM TD_SYSTEM_MSG_LOG
                            WHERE ID < {start}
                            ORDER BY ID DESC
                            LIMIT {length}
                        ) AS sub
                        ORDER BY ID ASC
                    """
                    cursor.execute(query)
                elif direction == "DOWN":
                    query = f"""
                        SELECT *
                        FROM TD_SYSTEM_MSG_LOG
                        WHERE ID > {start}
                        ORDER BY ID ASC
                        LIMIT {length}
                    """
                    cursor.execute(query)
                elif direction == "LAST":
                    query = f"""
                    SELECT * FROM (
                        SELECT *
                        FROM TD_SYSTEM_MSG_LOG
                        ORDER BY ID DESC
                        LIMIT {length}
                    ) AS sub
                        ORDER BY ID ASC
                    """
                    cursor.execute(query)

                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()