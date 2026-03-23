import pymysql
import json
from datetime import datetime, timedelta
import pytz
import copy

class SeDao:
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
            print("SNDAO : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def se_exists(self, msfd_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_CBSD_SN WHERE MFSD_ID = %s"""
                cursor.execute(query, (msfd_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def se_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_CBSD_SN ORDER BY MFSD_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def se_insert(self, fcc_id, mfsd_id):
        if not self.connection.open:
            self.connect()

        cbsd = {}
        cbsd["SN_ID"] = ''
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
                query = """INSERT INTO TD_CBSD_SE (FCC_ID, MFSD_ID, SN_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                            %s, %s, %s)"""

                values = tuple(map(cbsd.get, [
                    'FCC_ID', 'MFSD_ID', 'SN_ID', 'CH_1', 'CH_2', 'CH_3', 'CH_4',
                    'CH_5', 'CH_6', 'CH_7',
                    'CH_8', 'CH_9', 'CH_10'
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def update_channels_to_nonavail(self, fcc_id, mfsd_id, occupied_channels):
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
        sql = f"UPDATE TD_CBSD_SE SET {set_clause} WHERE FCC_ID = %s AND MFSD_ID = %s"

        params = list(values.values()) + [fcc_id, mfsd_id]

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        self.connection.commit()

    def get_esc_move_list(self, sensor_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT *, ST_Distance(
                              D.AREA,
                               POINT(C.LNG, C.LAT)
                           ) * 111.12
                        FROM TD_CBSD_REGIST C
                        JOIN (
                            SELECT AREA
                            FROM TD_E_DPA A
                            JOIN TD_ESC_REGIST B ON B.DPA_ID = A.DPA_ID
                            WHERE B.SENSOR_ID = %s
                        ) D
                        ON ST_Distance(
                              D.AREA,
                               POINT(C.LNG, C.LAT)
                           ) * 111.12 <= 20;
                    """
                cursor.execute(query, (sensor_id))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def get_ch_status(self, sensor_id):


        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """
                    SELECT 
                        SENSOR_ID,
                        MAX(CASE WHEN CH_NO = 1 THEN INCUMBENT_USER END) AS CH_1,
                        MAX(CASE WHEN CH_NO = 2 THEN INCUMBENT_USER END) AS CH_2,
                        MAX(CASE WHEN CH_NO = 3 THEN INCUMBENT_USER END) AS CH_3,
                        MAX(CASE WHEN CH_NO = 4 THEN INCUMBENT_USER END) AS CH_4,
                        MAX(CASE WHEN CH_NO = 5 THEN INCUMBENT_USER END) AS CH_5,
                        MAX(CASE WHEN CH_NO = 6 THEN INCUMBENT_USER END) AS CH_6,
                        MAX(CASE WHEN CH_NO = 7 THEN INCUMBENT_USER END) AS CH_7,
                        MAX(CASE WHEN CH_NO = 8 THEN INCUMBENT_USER END) AS CH_8,
                        MAX(CASE WHEN CH_NO = 9 THEN INCUMBENT_USER END) AS CH_9,
                        MAX(CASE WHEN CH_NO = 10 THEN INCUMBENT_USER END) AS CH_10
                        
                    FROM TD_ESC_CHANNELS
                    WHERE SENSOR_ID = %s
                    GROUP BY SENSOR_ID;
                    """
                cursor.execute(query, (sensor_id))
                result = cursor.fetchone()  # ← 한 행만 반환
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def update_channels_status(self):

        self.set_all_channels_to_45()
        """
               TD_ESC_REGIST 테이블에서 조건에 맞는 행을 조회하고 루프를 돌며 update_channels_to_avail 실행
               """
        select_sql = """
                   SELECT SENSOR_ID, LAT, LNG, HEIGHT
                   FROM TD_ESC_REGIST
                   WHERE DELETE_AT = 'N' AND STATUS = 'REGIST'
               """

        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(select_sql)
            regist_list = cursor.fetchall()

        # 루프 돌며 update 실행
        for row in regist_list:
            sensor_id = row.get("SENSOR_ID")
            sensor_status = self.get_ch_status(sensor_id)
            move_list = self.get_esc_move_list(sensor_id)
            for move in move_list:
                lat = row.get("LAT")
                lng = row.get("LNG")
                self.update_ch_status_by_cbsdid(move['CBSD_ID'], sensor_status)

    def update_ch_status_by_cbsdid(self, cbsd_id, chlist):

        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                # SET 절을 CASE WHEN 구문으로 구성
                set_clause_parts = []
                values = []

                for col, val in chlist.items():
                    if col == "SENSOR_ID":
                        continue
                    # -999가 아닌 경우에만 갱신, 이미 -999면 그대로 둠
                    set_clause_parts.append(f"{col} = CASE WHEN {col} = -999 THEN -999 ELSE %s END")
                    if val == 1:
                        values.append(-999)
                    else:
                        values.append(45)

                set_clause = ", ".join(set_clause_parts)

                query = f"""
                    UPDATE TD_CBSD_SE
                    SET {set_clause}
                    WHERE MFSD_ID = %s
                """

                cursor.execute(query, values + [cbsd_id])
                self.connection.commit()
                return True

        except pymysql.MySQLError as e:
            print(f"Error updating channel status: {e}")
            return False

    def set_all_channels_to_45(self, fcc_id=None, mfsd_id=None):
        """
        TD_CBSD_SE 테이블의 CH_1~CH_10 컬럼을 45로 업데이트
        fcc_id, mfsd_id 지정하면 해당 조건에 맞는 행만 업데이트
        """
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                # CH_1~CH_10 컬럼을 45로 SET
                ch_columns = [f"CH_{i}" for i in range(1, 11)]
                set_clause = ", ".join([f"{col} = 45" for col in ch_columns])

                # WHERE 조건 동적 구성
                where_clause = ""
                values = []
                if fcc_id is not None:
                    where_clause += "FCC_ID = %s"
                    values.append(fcc_id)
                if mfsd_id is not None:
                    if where_clause:
                        where_clause += " AND "
                    where_clause += "MFSD_ID = %s"
                    values.append(mfsd_id)

                query = f"UPDATE TD_CBSD_SE SET {set_clause}"
                if where_clause:
                    query += " WHERE " + where_clause

                cursor.execute(query, values)
                self.connection.commit()
                print(f"[INFO] CH_1~CH_10 값을 45로 업데이트 완료")
                return True

        except pymysql.MySQLError as e:
            print(f"[ERROR] set_all_channels_to_45 실패: {e}")
            return False

    def se_delete(self, sf_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_SN WHERE MFSD_ID = %s"""
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
                query = """DELETE FROM TD_CBSD_SN"""
                cursor.execute(query)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()