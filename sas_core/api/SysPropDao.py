import pymysql
import json
from datetime import datetime, timedelta
import pytz

class SysPropDao:
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
            print("SYSPROP : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def prop_list(self):
        try:
            with self.connection.cursor() as cursor:
                query = """SELECT SKEY, VALUE FROM TD_SYSTEM_PROP"""
                cursor.execute(query, )
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False


    _defaults = {
        "HEARTBEAT_INTERVAL": "60",
        "GRANT_EXPIRETIME": "600",
        "OPERPARAM_ON": "0",
    }

    def prop_get(self, key):
        try:
            if self.connection is None or not self.connection.open:
                self.connect()
            with self.connection.cursor() as cursor:
                query = """SELECT VALUE FROM TD_SYSTEM_PROP WHERE SKEY = %s"""
                cursor.execute(query, (key,))
                result = cursor.fetchone()
                if result:
                    return result['VALUE']
                return self._defaults.get(key, "0")
        except pymysql.MySQLError as e:
            print(f"SysPropDao.prop_get error ({key}): {e}")
            self.connection = None
            return self._defaults.get(key, "0")

    def prop_update(self, key, value):
        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_SYSTEM_PROP(SKEY, VALUE) VALUES( %s, %s)
                ON DUPLICATE KEY UPDATE VALUE=%s"""

                cursor.execute(query, (key, value, value))

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()