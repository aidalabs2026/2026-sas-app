import pymysql
import json
from datetime import datetime, timedelta
import pytz
import copy

class CbsdDao:
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
            print("CBSDDAO : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def cbsd_exists(self, cbsd_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_CBSD_REGIST WHERE CBSD_ID = %s AND DELETE_AT = 'N'"""
                cursor.execute(query, (cbsd_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def cbsd_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_CBSD_REGIST WHERE DELETE_AT='N' ORDER BY CBSD_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def dpa_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT DPA_ID, CH_STATUS, ST_AsGeoJSON(AREA) AS AREA FROM TD_E_DPA ORDER BY DPA_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def cbsd_list_by_cbsd_id(self, cbsd_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_CBSD_REGIST WHERE CBSD_ID=%s ORDER BY CBSD_ID ASC"""
                cursor.execute(query, (cbsd_id,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def cbsd_insert(self, cbsd, cbsd_id):
        if not self.connection.open:
            self.connect()


        cbsd["CBSD_ID"] = cbsd_id
        cbsd["measCapability"] = f'{cbsd["measCapability"]}'
        cbsd["radioTechnology"] = cbsd["airInterface"]["radioTechnology"]
        cbsd["supportedSpec"] = cbsd["airInterface"]["supportedSpec"]
        cbsd["latitude"] = cbsd["installationParam"]["latitude"]
        cbsd["longitude"] = cbsd["installationParam"]["longitude"]
        cbsd["height"] = cbsd["installationParam"]["height"]
        cbsd["heightType"] = cbsd["installationParam"]["heightType"]
        cbsd["indoorDeployment"] = cbsd["installationParam"]["indoorDeployment"]
        cbsd["antennaAzimuth"] = cbsd["installationParam"]["antennaAzimuth"]
        cbsd["antennaDowntilt"] = cbsd["installationParam"]["antennaDowntilt"]
        cbsd["antennaGain"] = cbsd["installationParam"]["antennaGain"]
        cbsd["antennaBeamwidth"] = cbsd["installationParam"]["antennaBeamwidth"]

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_CBSD_REGIST (FCC_ID, CATEGORY, CALL_SIGN, USER_ID, RADIO_TECH, SUPP_SPEC, VENDOR, MODEL, SOFT_VER, HARD_VER, 
                            FIRM_VER, SN, MEAS_CAPA, LAT, LNG, HEIGHT, HEIGHT_TYPE, HORIZON_ACC, VERTICAL_ACC, INDOOR, 
                            ANT_AZIM, ANT_DWN, ANT_GAIN, EIRP_CAPA, ANT_BWIDTH, ANT_MODEL, CBSD_ID, STATUS) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s)"""

                values = tuple(map(cbsd.get, [
                    'fccId', 'cbsdCategory', 'callSign', 'userId', 'radioTechnology', 'supportedSpec', 'vendor',
                    'model', 'softwareVersion', 'hardwareVersion',
                    'firmwareVersion', 'cbsdSerialNumber', 'measCapability', 'latitude', 'longitude', 'height',
                    'heightType', 'horizontalAccuracy', 'verticalAccuracy', 'indoorDeployment',
                    'antennaAzimuth', 'antennaDowntilt', 'antennaGain', 'eirpCapa', 'antennaBeamwidth',
                    'antennaModel', 'CBSD_ID', 'status'
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def cbsd_delete(self, cbsd_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TD_CBSD_REGIST SET STATUS='UNREGISTERED' WHERE CBSD_ID = %s"""
                cursor.execute(query, (cbsd_id,))
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
    def get_move_list_by_e_dpa(self, esc_id, lowFreq, highFreq, status, suspend_at):
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
                        ) D ON ST_Distance(
                              D.AREA,  
                               POINT(C.LNG, C.LAT)
                           )* 111.12 <= 20
                        JOIN TD_GRANT G ON G.CBSD_ID = C.CBSD_ID
                        WHERE LOW_FREQ BETWEEN %s AND %s
                        AND  
                        HIGH_FREQ BETWEEN %s AND %s
                        AND 
                        G.STATUS = %s AND 
                        G.SUSPEND_AT = %s;
                    """
                cursor.execute(query, (esc_id, lowFreq, highFreq, lowFreq, highFreq, status, suspend_at))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def grant_list_by_freq_and_cbsd_id(self, lowFreq, highFreq, status, suspend_at, cbsd_id ):
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
                        SUSPEND_AT = %s AND
                        CBSD_ID = %s
                    """
                cursor.execute(query, (lowFreq, highFreq, lowFreq, highFreq, status, suspend_at, cbsd_id))
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

        grant_data["CH_NO"] = int(grant_data["highFrequency"] % 3310000000 / 10000000 + 1)

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