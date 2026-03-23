import pymysql
import json
from datetime import datetime, timedelta
import pytz
import copy

class SfDao:
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
            print("SFDAO : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def sf_exists(self, msfd_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_CBSD_SF WHERE MFSD_ID = %s"""
                cursor.execute(query, (msfd_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sf_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_CBSD_SF ORDER BY MFSD_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def sf_insert(self, fcc_id, mfsd_id):
        if not self.connection.open:
            self.connect()

        cbsd = {}
        cbsd["SF_ID"] = ''
        cbsd["FCC_ID"] = fcc_id
        cbsd["MFSD_ID"] = mfsd_id
        cbsd["CH_1"] =  45
        cbsd["CH_2"] = 45
        cbsd["CH_3"] = 45
        cbsd["CH_4"] = 45
        cbsd["CH_5"] = 45
        cbsd["CH_6"] = 45
        cbsd["CH_7"] = 45
        cbsd["CH_8"] = 45
        cbsd["CH_9"] = 45
        cbsd["CH_10"] =45

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_CBSD_SF (FCC_ID, MFSD_ID, SF_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                            %s, %s, %s)"""

                values = tuple(map(cbsd.get, [
                    'FCC_ID', 'MFSD_ID', 'SF_ID', 'CH_1', 'CH_2', 'CH_3', 'CH_4',
                    'CH_5', 'CH_6', 'CH_7',
                    'CH_8', 'CH_9', 'CH_10'
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def update_channels(self, fcc_id, mfsd_id, occupied_channels):
        """
        conn : MySQL connection 객체
        record_id : TD_CBSD_SF 테이블의 ID
        occupied_channels : [1,2,3] 처럼 점유된 채널 번호 리스트
        """
        # 채널 최대 갯수
        max_channels = 10
        values = {}

        for ch in range(1, max_channels + 1):
            col = f"CH_{ch}"
            if ch in occupied_channels:
                values[col] = -999

        set_clause = ", ".join([f"{col} = %s" for col in values.keys()])
        sql = f"UPDATE TD_CBSD_SF SET {set_clause} WHERE FCC_ID = %s AND MFSD_ID = %s"

        params = list(values.values()) + [fcc_id, mfsd_id]

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        self.connection.commit()


    def sf_delete(self, sf_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_SF WHERE MFSD_ID = %s"""
                cursor.execute(query, (sf_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def sf_delete_all(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_SF"""
                cursor.execute(query)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()