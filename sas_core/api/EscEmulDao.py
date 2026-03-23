import pymysql
import json
from datetime import datetime, timedelta
import pytz

class EscEmulDao:
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
            print("")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def esc_exists(self, sensor_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_ESC_REGIST WHERE SENSOR_ID = %s AND DELETE_AT = 'N' """
                cursor.execute(query, (sensor_id,))
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def esc_search(self, sensor_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_ESC_REGIST WHERE SENSOR_ID = %s AND DELETE_AT = 'N' """
                cursor.execute(query, (sensor_id,))
                result = cursor.fetchall()
                self.connection.commit()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def esc_ch_exists(self, sensor_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_ESC_EMUL_CHANNELS WHERE SENSOR_ID = %s"""
                cursor.execute(query, (sensor_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def esc_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_ESC_REGIST WHERE DELETE_AT='N' ORDER BY SENSOR_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error get sensor list: {e}")
            return None

    def esc_registed_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_ESC_REGIST WHERE DELETE_AT='N' AND STATUS='REGIST' ORDER BY SENSOR_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error get sensor list: {e}")
            return None

    def esc_insert(self, esc):

        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_ESC_REGIST (SENSOR_ID, LAT, LNG, HEIGHT, HEIGHT_TYPE, ANTENNA_AZIMUTH, ANTENNA_DOWNTILT, 
                                    AZIMUTH_RAD_PATTERN, ELEVATION_RAD_PATTERN, STATUS, PROTECT_LEVEL, DPA_ID, IP_ADDR) 
                                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query,
                               (esc.escSensorId, esc.installationParam["latitude"], esc.installationParam["longitude"],
                                esc.installationParam["height"], esc.installationParam["heightType"],
                                esc.installationParam["antennaAzimuth"], esc.installationParam["antennaDowntilt"],
                                json.dumps(esc.installationParam["azimuthRadiationPattern"]),
                                json.dumps(esc.installationParam["elevationRadiationPattern"]), "REGIST",
                                esc.protectionLevel,
                                esc.dpaId,
                                esc.client_ip))

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def esc_update(self, esc):

        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """
                                UPDATE TD_ESC_REGIST
                                SET LAT = %s,
                                    LNG = %s,
                                    HEIGHT = %s,
                                    HEIGHT_TYPE = %s,
                                    ANTENNA_AZIMUTH = %s,
                                    ANTENNA_DOWNTILT = %s,
                                    AZIMUTH_RAD_PATTERN = %s,
                                    ELEVATION_RAD_PATTERN = %s,
                                    STATUS = %s,
                                    PROTECT_LEVEL = %s,
                                    DPA_ID = %s
                                WHERE SENSOR_ID = %s AND DELETE_AT = 'N'
                            """
                cursor.execute(query, (
                    esc.installationParam["latitude"],
                    esc.installationParam["longitude"],
                    esc.installationParam["height"],
                    esc.installationParam["heightType"],
                    esc.installationParam["antennaAzimuth"],
                    esc.installationParam["antennaDowntilt"],
                    json.dumps(esc.installationParam["azimuthRadiationPattern"]),
                    json.dumps(esc.installationParam["elevationRadiationPattern"]),
                    "REGIST",
                    esc.protectionLevel,
                    esc.dpaId,
                    esc.escSensorId  # WHERE 조건의 SENSOR_ID
                ))

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def esc_last_report_dt_update(self, esc):

        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """
                                UPDATE TD_ESC_REGIST
                                SET LAST_REPORT_DT = NOW()
                                WHERE SENSOR_ID = %s AND DELETE_AT = 'N'
                            """
                cursor.execute(query, (
                    esc.escSensorId  # WHERE 조건의 SENSOR_ID
                ))

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def esc_channels_insert(self, esc):

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_ESC_EMUL_CHANNELS (SENSOR_ID, CH_NO, LOW_FREQ, HIGH_FREQ) 
                                                   VALUES (%s, %s, %s, %s)"""
                cursor.execute(query,(esc.escSensorId, "1", "3300000000", "3310000000"))
                cursor.execute(query, (esc.escSensorId, "2", "3310000000", "3320000000"))
                cursor.execute(query, (esc.escSensorId, "3", "3320000000", "3330000000"))
                cursor.execute(query, (esc.escSensorId, "4", "3330000000", "3340000000"))
                cursor.execute(query, (esc.escSensorId, "5", "3340000000", "3350000000"))
                cursor.execute(query, (esc.escSensorId, "6", "3350000000", "3360000000"))
                cursor.execute(query, (esc.escSensorId, "7", "3360000000", "3370000000"))
                cursor.execute(query, (esc.escSensorId, "8", "3370000000", "3380000000"))
                cursor.execute(query, (esc.escSensorId, "9", "3380000000", "3390000000"))
                cursor.execute(query, (esc.escSensorId, "10", "3390000000", "3400000000"))
                """
                cursor.execute(query,
                               [
                                   (esc.escSensorId, "1", "3300000000", "3310000000"),
                                   (esc.escSensorId, "2", "3310000000", "3320000000"),
                                   (esc.escSensorId, "3", "3320000000", "3330000000"),
                                   (esc.escSensorId, "4", "3330000000", "3340000000"),
                                   (esc.escSensorId, "5", "3340000000", "3350000000"),
                                   (esc.escSensorId, "6", "3350000000", "3360000000"),
                                   (esc.escSensorId, "7", "3360000000", "3370000000"),
                                   (esc.escSensorId, "8", "3370000000", "3380000000"),
                                   (esc.escSensorId, "9", "3380000000", "3390000000"),
                                   (esc.escSensorId, "10", "3390000000", "3400000000")
                               ]
                               )
                """

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def esc_channels_insert2(self, escSensorId):

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_ESC_EMUL_CHANNELS (SENSOR_ID, CH_NO, LOW_FREQ, HIGH_FREQ) 
                                                   VALUES (%s, %s, %s, %s)"""
                cursor.execute(query,(escSensorId, "1", "3300000000", "3310000000"))
                cursor.execute(query, (escSensorId, "2", "3310000000", "3320000000"))
                cursor.execute(query, (escSensorId, "3", "3320000000", "3330000000"))
                cursor.execute(query, (escSensorId, "4", "3330000000", "3340000000"))
                cursor.execute(query, (escSensorId, "5", "3340000000", "3350000000"))
                cursor.execute(query, (escSensorId, "6", "3350000000", "3360000000"))
                cursor.execute(query, (escSensorId, "7", "3360000000", "3370000000"))
                cursor.execute(query, (escSensorId, "8", "3370000000", "3380000000"))
                cursor.execute(query, (escSensorId, "9", "3380000000", "3390000000"))
                cursor.execute(query, (escSensorId, "10", "3390000000", "3400000000"))
                """
                cursor.execute(query,
                               [
                                   (esc.escSensorId, "1", "3300000000", "3310000000"),
                                   (esc.escSensorId, "2", "3310000000", "3320000000"),
                                   (esc.escSensorId, "3", "3320000000", "3330000000"),
                                   (esc.escSensorId, "4", "3330000000", "3340000000"),
                                   (esc.escSensorId, "5", "3340000000", "3350000000"),
                                   (esc.escSensorId, "6", "3350000000", "3360000000"),
                                   (esc.escSensorId, "7", "3360000000", "3370000000"),
                                   (esc.escSensorId, "8", "3370000000", "3380000000"),
                                   (esc.escSensorId, "9", "3380000000", "3390000000"),
                                   (esc.escSensorId, "10", "3390000000", "3400000000")
                               ]
                               )
                """

                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def sensor_channel_list(self, sensor_id):
        try:
            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_ESC_EMUL_CHANNELS WHERE SENSOR_ID=%s ORDER BY CH_NO ASC"""
                cursor.execute(query,
                               (sensor_id,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def esc_ch_update_status(self, sensor_id, low_freq, high_freq, status):
        try:
            with self.connection.cursor() as cursor:
                query = """UPDATE TD_ESC_EMUL_CHANNELS SET INCUMBENT_USER=%s WHERE SENSOR_ID = %s AND LOW_FREQ=%s AND HIGH_FREQ=%s"""
                cursor.execute(query, (status, sensor_id, low_freq, high_freq, ))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def esc_ch_get_status(self, sensor_id, low_freq, high_freq):
        try:
            with self.connection.cursor() as cursor:
                query = """SELECT INCUMBENT_USER FROM TD_ESC_EMUL_CHANNELS WHERE SENSOR_ID = %s AND LOW_FREQ=%s AND HIGH_FREQ=%s"""
                cursor.execute(query, (sensor_id, low_freq, high_freq, ))
                result = cursor.fetchone()
                return True if result['INCUMBENT_USER'] == 1 else False
        except pymysql.MySQLError as e:
            return False

    def esc_delete(self, sensor_id):
        try:
            with self.connection.cursor() as cursor:
                query = """UPDATE TD_ESC_REGIST SET STATUS='DEREGIST' WHERE SENSOR_ID = %s"""
                cursor.execute(query, (sensor_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def esc_sensor_delete(self, sensor_id):
        try:
            with self.connection.cursor() as cursor:
                query = """UPDATE TD_ESC_REGIST SET DELETE_AT='Y' WHERE ID = %s"""
                cursor.execute(query, (sensor_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def esc_channels_delete(self, sensor_id):
        try:
            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_ESC_CHANNELS WHERE SENSOR_ID=%s"""
                cursor.execute(query, (sensor_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def grant_exists(self, grant_id):
        try:
            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_GRANT WHERE GRANT_ID = %s"""
                cursor.execute(query, (grant_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def grant_list_by_freq(self, lowFreq, highFreq):
        try:
            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT LIMIT 1"""
                cursor.execute(query, )
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def grant_list_by_grantid(self, grant_id):
        try:
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
            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_GRANT WHERE CBSD_ID = %s ORDER BY GRANT_ID ASC"""
                cursor.execute(query, (cbsd_id, ))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def grant_insert(self, grant, grant_id, cbsd_id):
        grant["CBSD_ID"] = cbsd_id
        grant["maxEirp"] = grant["operationParam"]["maxEirp"]
        grant["lowFrequency"] = grant["operationParam"]["operationFrequencyRange"]["lowFrequency"]
        grant["highFrequency"] = grant["operationParam"]["operationFrequencyRange"]["highFrequency"]
        grant["STATUS"] = "AUTHORIZED"
        grant["grant_id"] = grant_id

        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_GRANT (CBSD_ID, MAX_EIRP, LOW_FREQ, HIGH_FREQ, STATUS, HB_DUR, HB_IINTV, CH_TYPE, GRANT_ID, CH_NO) 
                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, '1')"""

                values = tuple(map(grant.get, [
                    'CBSD_ID', 'maxEirp', 'lowFrequency', 'highFrequency', 'STATUS', 'hearbeatDuration', 'hearbeatinterval',
                    'channelType', 'grant_id'
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            print(e)
            return False

    def grant_update_status(self, grant_id, status):
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                query = """UPDATE TD_GRANT SET STATUS=%s WHERE GRANT_ID = %s"""
                cursor.execute(query, (status, grant_id))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False
        finally:
            self.close()

    def esc_sensing_channel_status(self, row_freq = None, high_freq = None):
        try:
            with self.connection.cursor() as cursor:
                if row_freq == None:
                    query = """SELECT CH_NO, LOW_FREQ, HIGH_FREQ,
                                    SUM(CASE WHEN INCUMBENT_USER = 1 THEN 1 ELSE 0 END) AS COUNT_USER_1,
                                    SUM(CASE WHEN INCUMBENT_USER = 0 THEN 1 ELSE 0 END) AS COUNT_USER_0
                                FROM TD_ESC_EMUL_CHANNELS
                                GROUP BY CH_NO
                                ORDER BY CH_NO ASC"""
                    cursor.execute(query, )
                else:
                    query = """SELECT CH_NO, LOW_FREQ, HIGH_FREQ,
                                    SUM(CASE WHEN INCUMBENT_USER = 1 THEN 1 ELSE 0 END) AS COUNT_USER_1,
                                    SUM(CASE WHEN INCUMBENT_USER = 0 THEN 1 ELSE 0 END) AS COUNT_USER_0
                                FROM TD_ESC_EMUL_CHANNELS
                                WHERE LOW_FREQ=%s AND HIGH_FREQ=%s
                                GROUP BY CH_NO
                                ORDER BY CH_NO ASC"""
                    cursor.execute(query, (row_freq, high_freq))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def grant_delete(self, grant_id):
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                query = """DELETE FROM TD_GRANT WHERE GRANT_ID = %s"""
                cursor.execute(query, (grant_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False
        finally:
            self.close()

    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()