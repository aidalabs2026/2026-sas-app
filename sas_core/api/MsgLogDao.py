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


    def list_by_deviceid(self, device_id, start = None, end= None):
        try:
            with self.connection.cursor() as cursor:
                one_hour_ago = datetime.now() - timedelta(hours=1)
                if start == None:
                    query = """
                                            SELECT * FROM TD_SYSTEM_MSG_LOG 
                                            WHERE ( DEVICE_ID = %s OR 1=1) 
                                                AND REGIST_DT >= %s
                                            ORDER BY REGIST_DT DESC LIMIT 50"""
                    cursor.execute(query,
                                   (device_id, one_hour_ago))
                else:
                    query = """
                                            SELECT * FROM TD_SYSTEM_MSG_LOG 
                                            WHERE ( DEVICE_ID = %s OR 1=1) 
                                                AND REGIST_DT BETWEEN %s AND %s
                                            ORDER BY REGIST_DT DESC LIMIT 50"""
                    cursor.execute(query,
                                   (device_id, start, end))

                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
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