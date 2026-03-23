import pymysql
import json
from datetime import datetime, timedelta
import pytz
import copy

class SdDao:
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
            print("SDDAO : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")


    def merge_sd(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:

                self.evt_sd_delete()
                self.evt_sd_copy()

                # 1. SF MERGE
                # CBSD_SF 테이블에서 모든 데이터 가져오기
                cursor.execute(
                    "SELECT FCC_ID, MFSD_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10 FROM TD_CBSD_SF")
                rows = cursor.fetchall()

                for row in rows:
                    fcc_id = row["FCC_ID"]
                    mfsd_id = row["MFSD_ID"]

                    # CBSD_SD 현재 값 가져오기
                    cursor.execute("""
                                SELECT ID, SD_CH_1, SD_CH_2, SD_CH_3, SD_CH_4, SD_CH_5, SD_CH_6, SD_CH_7, SD_CH_8, SD_CH_9, SD_CH_10
                                FROM TD_CBSD_EVT_SD
                                WHERE FCC_ID = %s AND MFSD_ID = %s
                            """, (fcc_id, mfsd_id))
                    sd_row = cursor.fetchone()

                    if not sd_row:
                        continue  # 대응되는 SD 데이터 없으면 건너뜀

                    update_fields = []
                    update_values = []

                    # CH_1 ~ CH_10 비교
                    for i in range(1, 11):
                        se_val = row[f"CH_{i}"]
                        sd_val = sd_row[f"SD_CH_{i}"]

                        if se_val is not None:
                            if sd_val is None or sd_val > se_val:
                                update_fields.append(f"SD_CH_{i} = %s")
                                update_values.append(se_val)

                    # 업데이트할 값이 있으면 실행
                    if update_fields:
                        sql = f"""
                                    UPDATE TD_CBSD_EVT_SD
                                    SET {', '.join(update_fields)}, UPDATE_DT = CURRENT_TIMESTAMP
                                    WHERE ID = %s
                                """
                        update_values.append(sd_row["ID"])
                        cursor.execute(sql, tuple(update_values))
                        print(f"Updated FCC_ID={fcc_id}, MFSD_ID={mfsd_id}")

                # 2. SE MERGE
                # CBSD_SE 테이블에서 모든 데이터 가져오기
                cursor.execute(
                    "SELECT FCC_ID, MFSD_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10 FROM TD_CBSD_SE")
                rows = cursor.fetchall()

                for row in rows:
                    fcc_id = row["FCC_ID"]
                    mfsd_id = row["MFSD_ID"]

                    if mfsd_id == "mfsd-135/322021410006594":
                        print(mfsd_id)

                    # CBSD_SD 현재 값 가져오기
                    cursor.execute("""
                                        SELECT ID, SD_CH_1, SD_CH_2, SD_CH_3, SD_CH_4, SD_CH_5, SD_CH_6, SD_CH_7, SD_CH_8, SD_CH_9, SD_CH_10
                                        FROM TD_CBSD_EVT_SD
                                        WHERE FCC_ID = %s AND MFSD_ID = %s
                                    """, (fcc_id, mfsd_id))
                    sd_row = cursor.fetchone()

                    if not sd_row:
                        continue  # 대응되는 SD 데이터 없으면 건너뜀

                    update_fields = []
                    update_values = []

                    # CH_1 ~ CH_10 비교
                    for i in range(1, 11):
                        se_val = row[f"CH_{i}"]
                        sd_val = sd_row[f"SD_CH_{i}"]

                        if se_val is not None:
                            if sd_val is None or sd_val > se_val:
                                update_fields.append(f"SD_CH_{i} = %s")
                                update_values.append(se_val)

                    # 업데이트할 값이 있으면 실행
                    if update_fields:
                        sql = f"""
                                            UPDATE TD_CBSD_EVT_SD
                                            SET {', '.join(update_fields)}, UPDATE_DT = CURRENT_TIMESTAMP
                                            WHERE ID = %s
                                        """
                        update_values.append(sd_row["ID"])
                        cursor.execute(sql, tuple(update_values))
                        print(f"Updated FCC_ID={fcc_id}, MFSD_ID={mfsd_id}")

                # 3. SN MERGE
                # CBSD_SN 테이블에서 모든 데이터 가져오기
                cursor.execute(
                    "SELECT FCC_ID, MFSD_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10 FROM TD_CBSD_SN")
                rows = cursor.fetchall()

                for row in rows:
                    fcc_id = row["FCC_ID"]
                    mfsd_id = row["MFSD_ID"]

                    # CBSD_SD 현재 값 가져오기
                    cursor.execute("""
                                        SELECT ID, SD_CH_1, SD_CH_2, SD_CH_3, SD_CH_4, SD_CH_5, SD_CH_6, SD_CH_7, SD_CH_8, SD_CH_9, SD_CH_10
                                        FROM TD_CBSD_EVT_SD
                                        WHERE FCC_ID = %s AND MFSD_ID = %s
                                    """, (fcc_id, mfsd_id))
                    sd_row = cursor.fetchone()

                    if not sd_row:
                        continue  # 대응되는 SD 데이터 없으면 건너뜀

                    update_fields = []
                    update_values = []

                    # CH_1 ~ CH_10 비교
                    for i in range(1, 11):
                        se_val = row[f"CH_{i}"]
                        sd_val = sd_row[f"SD_CH_{i}"]

                        if se_val is not None:
                            if sd_val is None or sd_val > se_val:
                                update_fields.append(f"SD_CH_{i} = %s")
                                update_values.append(se_val)

                    # 업데이트할 값이 있으면 실행
                    if update_fields:
                        sql = f"""
                                            UPDATE TD_CBSD_EVT_SD
                                            SET {', '.join(update_fields)}, UPDATE_DT = CURRENT_TIMESTAMP
                                            WHERE ID = %s
                                        """
                        update_values.append(sd_row["ID"])
                        cursor.execute(sql, tuple(update_values))
                        print(f"Updated FCC_ID={fcc_id}, MFSD_ID={mfsd_id}")

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def get_available_ch(self, cbsd_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT *  FROM TD_CBSD_EVT_SD WHERE MFSD_ID = %s"""
                cursor.execute(query, (cbsd_id,))
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sf_exists(self, sf_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_CBSD_SF WHERE SF_ID = %s"""
                cursor.execute(query, (sf_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sn_exists(self, sf_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_CBSD_SN WHERE SN_ID = %s"""
                cursor.execute(query, (sf_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def se_exists(self, sf_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_CBSD_SE WHERE SE_ID = %s"""
                cursor.execute(query, (sf_id,))
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

    def sn_list(self):
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

    def se_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_CBSD_SE ORDER BY MFSD_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def sf_insert(self, cbsd, sf_id):
        if not self.connection.open:
            self.connect()


        cbsd["SF_ID"] = sf_id
        cbsd["FCC_ID"] = f'{cbsd["FCC_ID"]}'
        cbsd["MFSD_ID"] = f'{cbsd["MFSD_ID"]}'
        cbsd["CH_1"] =  cbsd["CH_1"]
        cbsd["CH_2"] = cbsd["CH_2"]
        cbsd["CH_3"] = cbsd["CH_3"]
        cbsd["CH_4"] = cbsd["CH_4"]
        cbsd["CH_5"] = cbsd["CH_5"]
        cbsd["CH_6"] = cbsd["CH_6"]
        cbsd["CH_7"] = cbsd["CH_7"]
        cbsd["CH_8"] = cbsd["CH_8"]
        cbsd["CH_9"] = cbsd["CH_9"]
        cbsd["CH_10"] = cbsd["CH_10"]

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

    def sn_insert(self, cbsd, sn_id):
        if not self.connection.open:
            self.connect()


        cbsd["SN_ID"] = sn_id
        cbsd["FCC_ID"] = f'{cbsd["FCC_ID"]}'
        cbsd["MFSD_ID"] = f'{cbsd["MFSD_ID"]}'
        cbsd["CH_1"] =  cbsd["CH_1"]
        cbsd["CH_2"] = cbsd["CH_2"]
        cbsd["CH_3"] = cbsd["CH_3"]
        cbsd["CH_4"] = cbsd["CH_4"]
        cbsd["CH_5"] = cbsd["CH_5"]
        cbsd["CH_6"] = cbsd["CH_6"]
        cbsd["CH_7"] = cbsd["CH_7"]
        cbsd["CH_8"] = cbsd["CH_8"]
        cbsd["CH_9"] = cbsd["CH_9"]
        cbsd["CH_10"] = cbsd["CH_10"]

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_CBSD_SN (FCC_ID, MFSD_ID, SN_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10) 
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

    def se_insert(self, cbsd, se_id):
        if not self.connection.open:
            self.connect()


        cbsd["SE_ID"] = se_id
        cbsd["FCC_ID"] = f'{cbsd["FCC_ID"]}'
        cbsd["MFSD_ID"] = f'{cbsd["MFSD_ID"]}'
        cbsd["CH_1"] =  cbsd["CH_1"]
        cbsd["CH_2"] = cbsd["CH_2"]
        cbsd["CH_3"] = cbsd["CH_3"]
        cbsd["CH_4"] = cbsd["CH_4"]
        cbsd["CH_5"] = cbsd["CH_5"]
        cbsd["CH_6"] = cbsd["CH_6"]
        cbsd["CH_7"] = cbsd["CH_7"]
        cbsd["CH_8"] = cbsd["CH_8"]
        cbsd["CH_9"] = cbsd["CH_9"]
        cbsd["CH_10"] = cbsd["CH_10"]

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_CBSD_SE (FCC_ID, MFSD_ID, SE_ID, CH_1, CH_2, CH_3, CH_4, CH_5, CH_6, CH_7, CH_8, CH_9, CH_10) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                            %s, %s, %s)"""

                values = tuple(map(cbsd.get, [
                    'FCC_ID', 'MFSD_ID', 'SE_ID', 'CH_1', 'CH_2', 'CH_3', 'CH_4',
                    'CH_5', 'CH_6', 'CH_7',
                    'CH_8', 'CH_9', 'CH_10'
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def sf_delete(self, sf_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_SF WHERE SF_ID = %s"""
                cursor.execute(query, (sf_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def evt_sd_delete(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_EVT_SD"""
                cursor.execute(query)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def evt_sd_copy(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """INSERT INTO
        TD_CBSD_EVT_SD(FCC_ID, MFSD_ID, SD_CH_1, SD_CH_2, SD_CH_3, SD_CH_4, SD_CH_5, SD_CH_6, SD_CH_7, SD_CH_8,
                               SD_CH_9, SD_CH_10)
        SELECT
        FCC_ID, MFSD_ID, SD_CH_1, SD_CH_2, SD_CH_3, SD_CH_4, SD_CH_5, SD_CH_6, SD_CH_7, SD_CH_8, SD_CH_9, SD_CH_10
        FROM
         TD_CBSD_SD"""
                cursor.execute(query)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False



    def sn_delete(self, sn_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_SN WHERE SN_ID = %s"""
                cursor.execute(query, (sn_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def se_delete(self, se_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_CBSD_SE WHERE SE_ID = %s"""
                cursor.execute(query, (se_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def cbsd_device_delete(self, cbsd_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TD_CBSD_REGIST SET DELETE_AT='Y' WHERE ID = %s"""
                cursor.execute(query, (cbsd_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def cbsd_update_status(self, cbsd_id, status):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TD_CBSD_REGIST SET STATUS=%s WHERE CBSD_ID = %s"""
                cursor.execute(query, (status, cbsd_id))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def grant_exists(self, grant_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_GRANT WHERE GRANT_ID = %s"""
                cursor.execute(query, (grant_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def find_e_dpa_by_loc(self, lat, lng):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT *
                        FROM
                        TD_E_DPA
                        WHERE
                        ST_Intersects(
                            AREA,
                            ST_GeomFromText('POINT(%s %s)')
                        );"""
                cursor.execute(query, (lng, lat,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None


    def grant_list_by_freq(self, lowFreq, highFreq, status, suspend_at):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT 
                    WHERE
                        LOW_FREQ BETWEEN %s AND %s
                        AND  
                        HIGH_FREQ BETWEEN %s AND %s
                        AND 
                        STATUS = %s AND 
                        SUSPEND_AT = %s
                    """
                cursor.execute(query, (lowFreq, highFreq, lowFreq, highFreq, status, suspend_at))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def grant_list_by_grantid(self, grant_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT WHERE GRANT_ID= %s"""
                cursor.execute(query, (grant_id,))
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def grant_list(self, cbsd_id ):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT WHERE CBSD_ID = %s ORDER BY GRANT_ID ASC"""
                cursor.execute(query, (cbsd_id, ))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def grant_list_by_status(self, cbsd_id, status ):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT WHERE CBSD_ID = %s AND STATUS = %s ORDER BY GRANT_ID ASC"""
                cursor.execute(query, (cbsd_id, status))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def suspend_grant_list(self, cbsd_id ):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT WHERE CBSD_ID = %s AND SUSPEND_AT = 1 ORDER BY GRANT_ID ASC"""
                cursor.execute(query, (cbsd_id))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def grant_insert(self, grant, grant_id, cbsd_id):
        # grant를 깊은 복사하여 원본을 보존
        grant_data = copy.deepcopy(grant)
        grant_data["CBSD_ID"] = cbsd_id
        grant_data["maxEirp"] = grant_data["operationParam"]["maxEirp"]
        grant_data["lowFrequency"] = grant_data["operationParam"]["operationFrequencyRange"]["lowFrequency"]
        grant_data["highFrequency"] = grant_data["operationParam"]["operationFrequencyRange"]["highFrequency"]
        grant_data["STATUS"] = "GRANTED"
        grant_data["grant_id"] = grant_id

        grant_data["CH_NO"] = grant_data["highFrequency"] % 3310000000 / 10000000 + 1

        # 문자열을 datetime 객체로 파싱 (T와 Z를 처리)
        dt_obj = datetime.strptime(grant_data["grantExpireTime"], "%Y-%m-%dT%H:%M:%SZ")

        # 원하는 형식으로 다시 문자열로 변환
        grant_data["grantExpireTime_newformat"] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")


        # 문자열을 datetime 객체로 파싱 (T와 Z를 처리)
        dt_obj = datetime.strptime(grant_data["transmitExpireTime"], "%Y-%m-%dT%H:%M:%SZ")

        # 원하는 형식으로 다시 문자열로 변환
        grant_data["transmitExpireTime_newformat"] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_GRANT (CBSD_ID, MAX_EIRP, LOW_FREQ, HIGH_FREQ, STATUS, HB_DUR, HB_IINTV, CH_TYPE, GRANT_ID, CH_NO,
                                            TRANSMIT_EXPIRETIME, GRANT_EXPIRETIME) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                values = tuple(map(grant_data.get, [
                    'CBSD_ID', 'maxEirp', 'lowFrequency', 'highFrequency', 'STATUS', 'hearbeatDuration', 'hearbeatinterval',
                    'channelType', 'grant_id', "CH_NO", "transmitExpireTime_newformat", "grantExpireTime_newformat"
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def grant_update_status(self, grant_id, status):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TD_GRANT SET STATUS=%s WHERE GRANT_ID = %s"""
                cursor.execute(query, (status, grant_id))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def grant_update_expiretime(self, grant_id, grant_expiretime=None, transmit_expiretime=None):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                if grant_expiretime == None:
                    # 문자열을 datetime 객체로 파싱 (T와 Z를 처리)
                    dt_obj = datetime.strptime(transmit_expiretime, "%Y-%m-%dT%H:%M:%SZ")
                    # 원하는 형식으로 다시 문자열로 변환
                    transmit_expiretime = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

                    query = """UPDATE TD_GRANT SET TRANSMIT_EXPIRETIME = %s WHERE GRANT_ID = %s"""
                    cursor.execute(query, (transmit_expiretime, grant_id))
                else:
                    # 문자열을 datetime 객체로 파싱 (T와 Z를 처리)
                    dt_obj = datetime.strptime(grant_expiretime, "%Y-%m-%dT%H:%M:%SZ")
                    # 원하는 형식으로 다시 문자열로 변환
                    grant_expiretime = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

                    # 문자열을 datetime 객체로 파싱 (T와 Z를 처리)
                    dt_obj = datetime.strptime(transmit_expiretime, "%Y-%m-%dT%H:%M:%SZ")
                    # 원하는 형식으로 다시 문자열로 변환
                    transmit_expiretime = dt_obj.strftime("%Y-%m-%d %H:%M:%S")

                    query = """UPDATE TD_GRANT SET GRANT_EXPIRETIME=%s, TRANSMIT_EXPIRETIME = %s WHERE GRANT_ID = %s"""
                    cursor.execute(query, (grant_expiretime, transmit_expiretime, grant_id))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def grant_update_suspend_at(self, grant_id, status):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TD_GRANT SET SUSPEND_AT=%s WHERE GRANT_ID = %s"""
                cursor.execute(query, (status, grant_id))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def grant_delete(self, grant_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_GRANT WHERE GRANT_ID = %s"""
                cursor.execute(query, (grant_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def grant_delete_by_cbsdid(self, cbsd_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_GRANT WHERE CBSD_ID = %s"""
                cursor.execute(query, (cbsd_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def check_last_grant_time(self, interval):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * 
                    FROM TD_GRANT
                    WHERE UPDATE_DT < DATE_SUB(NOW(), INTERVAL %s DAY);
                    """
                cursor.execute(query, (interval))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return []



    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()