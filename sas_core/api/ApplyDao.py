import pymysql
import json
from datetime import datetime, timedelta
import pytz
import copy

class ApplyDao:
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
            print("APPLYDAO : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def activate_apply_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT 
                a.APPLYEMUL_SEQ,
                a.SN,
                a.DPA_NM,
                a.OPER_NM,
                a.FREQUENCY,
                a.LIC_BAND,
                ST_AsText(a.RX_AREA) AS RX_AREA,
                a.RX_NM,
                a.RX_HEIGHT,
                a.RX_ANT_PATTERN,
                a.RX_POLAR,
                a.RX_ANT_GAIN,
                a.RX_ANT_WIDTH,
                a.RX_ANT_AZIM,
                a.RX_ANT_ELEV,
                a.RX_FEED,
                a.RX_NOISE,
                a.IN_THRESHOLD,
                a.PERIOD_TYPE,
                a.PERIODIC_DAY,
                a.PERIODIC_START,
                a.PERIODIC_END,
                a.PERIODIC_START_TIME,
                a.PERIODIC_END_TIME,
                a.REGIST_DT,
                a.UPDATE_DT,
                a.DELETE_AT,
                a.ID
            FROM TD_APPLY_EMUL a
            WHERE 
                1 = 1
                AND (
                        (a.PERIOD_TYPE = 'periodic'
                         AND a.PERIODIC_END >= NOW())
                      OR
                        (a.PERIOD_TYPE = 'nonPeriodic'
                         AND EXISTS (
                             SELECT 1
                             FROM TR_APPLY_NON_PERIODIC np
                             WHERE np.APPLY_ID = a.ID AND DELETE_AT='N'
                               AND np.NON_PERIODIC_END >= NOW()
                         ))
                      )
                AND DELETE_AT='N';"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def apply_move_list(self, apply_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT 
                            a.APPLYEMUL_SEQ,
                            a.SN,
                            a.DPA_NM,
                            a.OPER_NM,
                            a.FREQUENCY,
                            a.LIC_BAND,
                            ST_AsText(a.RX_AREA) AS RX_AREA,
                            a.RX_NM,
                            a.RX_HEIGHT,
                            a.RX_ANT_PATTERN,
                            a.RX_POLAR,
                            a.RX_ANT_GAIN,
                            a.RX_ANT_WIDTH,
                            a.RX_ANT_AZIM,
                            a.RX_ANT_ELEV,
                            a.RX_FEED,
                            a.RX_NOISE,
                            a.IN_THRESHOLD,
                            a.PERIOD_TYPE,
                            a.PERIODIC_DAY,
                            a.PERIODIC_START,
                            a.PERIODIC_END,
                            a.PERIODIC_START_TIME,
                            a.PERIODIC_END_TIME,
                            a.REGIST_DT,
                            a.UPDATE_DT,
                            a.DELETE_AT,
                            a.ID,
                            c.CBSD_ID,
                            c.FCC_ID,
                            c.MODEL,
                            c.VENDOR,
                            c.LAT,
                            c.LNG
                        FROM TD_APPLY_EMUL a
                        JOIN TD_CBSD_REGIST c
                          ON ST_Contains(
                                a.RX_AREA, Point(c.LNG, c.LAT)
                             )
                        WHERE a.ID = %s;"""
                cursor.execute(query, (apply_id,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def apply_exists(self, apply_id):
        try:
            #self.connect()
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT COUNT(*) as count FROM TD_APPLY_EMUL WHERE ID = %s AND DELETE_AT = 'N'"""
                cursor.execute(query, (apply_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def apply_list(self):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_APPLY_EMUL WHERE DELETE_AT='N' ORDER BY ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def non_periodic_list_by_apply_id(self, apply_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TR_APPLY_NON_PERIODIC WHERE APPLY_ID=%s AND DELETE_AT='N' ORDER BY APPLY_ID ASC"""
                cursor.execute(query, (apply_id,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def apply_insert_or_update(self, apply, apply_id=None):
        if not self.connection.open:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                # rxArea 는 json 배열을 문자열로 바꿔서 저장함.
                # Serialize complex data types to JSON strings before adding to the tuple.
                rx_area_data = apply.get('rxArea', [])
                rx_area_wkt = rx_area_data[0] if rx_area_data else None

                rx_ant_pattern = json.dumps(apply.get('rxAntPattern'))
                periodic_data = apply.get('periodicTime', {})

                values = (
                    apply.get('sn'),
                    apply.get('dpaNm'),
                    apply.get('operNm'),
                    apply.get('frequency'),
                    apply.get('licBand'),
                    rx_area_wkt,  # Insert the serialized JSON string
                    apply.get('rxNm'),
                    apply.get('rxHeight'),
                    rx_ant_pattern,  # Insert the serialized JSON string
                    apply.get('rxPolar'),
                    apply.get('rxAntGain'),
                    apply.get('rxAntWidth'),
                    apply.get('rxAntAzim'),
                    apply.get('rxAntElev'),
                    apply.get('rxFeed'),
                    apply.get('rxNoise'),
                    apply.get('inThreshold'),
                    apply.get('periodType'),
                    periodic_data.get('weekday'),
                    periodic_data.get('startDateTime'),
                    periodic_data.get('endDateTime'),
                    periodic_data.get('startTime'),
                    periodic_data.get('endTime')
                )

                if apply_id:
                    # UPDATE 쿼리를 작성합니다.
                    query = """UPDATE TD_APPLY_EMUL 
                                           SET SN=%s, DPA_NM=%s, OPER_NM=%s, FREQUENCY=%s, LIC_BAND=%s,
                                               RX_AREA=ST_GeomFromText(%s), RX_NM=%s, RX_HEIGHT=%s, 
                                               RX_ANT_PATTERN=%s, RX_POLAR=%s, RX_ANT_GAIN=%s, 
                                               RX_ANT_WIDTH=%s, RX_ANT_AZIM=%s, RX_ANT_ELEV=%s, 
                                               RX_FEED=%s, RX_NOISE=%s, IN_THRESHOLD=%s, 
                                               PERIOD_TYPE=%s, PERIODIC_DAY=%s, PERIODIC_START=%s, PERIODIC_END=%s,
                                               PERIODIC_START_TIME=%s, PERIODIC_END_TIME=%s
                                           WHERE ID=%s"""
                    # WHERE 절에 사용할 ID를 추가합니다.
                    values = values + (apply_id,)
                    cursor.execute(query, values)
                    rows_affected = cursor.rowcount  # 업데이트된 행의 개수
                    self.connection.commit()
                    return rows_affected
                else:
                    # INSERT 쿼리를 작성합니다.
                    query = """INSERT INTO TD_APPLY_EMUL (SN, DPA_NM, OPER_NM, FREQUENCY, LIC_BAND, RX_AREA, RX_NM, RX_HEIGHT, RX_ANT_PATTERN, RX_POLAR, RX_ANT_GAIN, RX_ANT_WIDTH, RX_ANT_AZIM, RX_ANT_ELEV, RX_FEED, RX_NOISE, IN_THRESHOLD, PERIOD_TYPE, PERIODIC_DAY, PERIODIC_START, PERIODIC_END, PERIODIC_START_TIME, PERIODIC_END_TIME) 
                                           VALUES (%s, %s, %s, %s, %s, 
                                           ST_GeomFromText(%s), %s, %s, %s, %s,
                                           %s, %s, %s, %s, %s, 
                                           %s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(query, values)
                    last_id = cursor.lastrowid
                    self.connection.commit()
                    return last_id

        except pymysql.MySQLError as e:
            print(e)
            return False

    def non_periodic_insert_or_update(self, non_periodic, apply_id, non_periodic_id=None):
        if not self.connection.open:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                # INSERT와 UPDATE에 공통으로 사용될 값들을 정의합니다.
                values = (
                    non_periodic.get('startDateTimeNon'),
                    non_periodic.get('endDateTimeNon'),
                    apply_id,
                )

                if non_periodic_id:
                    # non_periodic_id가 제공되면 UPDATE 쿼리를 실행합니다.
                    query = """UPDATE TR_APPLY_NON_PERIODIC 
                                           SET NON_PERIODIC_START = %s, NON_PERIODIC_END = %s, APPLY_ID = %s 
                                           WHERE ID = %s"""

                    # WHERE 절에 사용할 ID를 추가합니다.
                    values += (non_periodic_id,)
                    cursor.execute(query, values)
                    rows_affected = cursor.rowcount  # 업데이트된 행의 개수
                    self.connection.commit()
                    return rows_affected
                else:
                    # non_periodic_id가 없으면 INSERT 쿼리를 실행합니다.
                    query = """INSERT INTO TR_APPLY_NON_PERIODIC (NON_PERIODIC_START, NON_PERIODIC_END, APPLY_ID) 
                                           VALUES (%s, %s, %s)"""

                    cursor.execute(query, values)
                    last_id = cursor.lastrowid
                    self.connection.commit()
                    return last_id

        except pymysql.MySQLError as e:
            print(e)
            return False

    def apply_delete(self, apply_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TD_APPLY_EMUL SET DELETE_AT='Y' WHERE ID = %s"""
                cursor.execute(query, (apply_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def apply_get(self, apply_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_APPLY_EMUL WHERE ID = %s"""
                cursor.execute(query, (apply_id,))
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def non_periodic_delete(self, non_periodic_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TR_APPLY_NON_PERIODIC SET DELETE_AT='Y' WHERE ID = %s"""
                cursor.execute(query, (non_periodic_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def non_periodic_delete_by_apply_id(self, apply_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """UPDATE TR_APPLY_NON_PERIODIC SET DELETE_AT='Y' WHERE APPLY_ID = %s"""
                cursor.execute(query, (apply_id,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False

    def get_applications(self, apply_id=None, start_date=None, end_date=None):
        try:
            if not self.connection.open:
                self.connect()
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 기본 쿼리를 정의합니다.
                query = "SELECT APPLYEMUL_SEQ, SN, DPA_NM, OPER_NM, FREQUENCY, LIC_BAND, ST_AsText(RX_AREA) AS RX_AREA, RX_NM, RX_HEIGHT, RX_ANT_PATTERN, RX_POLAR, RX_ANT_GAIN, RX_ANT_WIDTH, RX_ANT_AZIM, RX_ANT_ELEV, RX_FEED, RX_NOISE, IN_THRESHOLD, PERIOD_TYPE, PERIODIC_DAY, PERIODIC_START, PERIODIC_END, TIME_FORMAT(PERIODIC_START_TIME, '%%H:%%i') AS PERIODIC_START_TIME, TIME_FORMAT(PERIODIC_END_TIME, '%%H:%%i') AS PERIODIC_END_TIME, REGIST_DT, UPDATE_DT, DELETE_AT, ID FROM TD_APPLY_EMUL WHERE 1=1 AND DELETE_AT = 'N' ORDER BY REGIST_DT DESC;"  # 모든 조건을 붙이기 위한 꼼수
                params = []

                # apply_id가 제공되면 쿼리에 WHERE 절을 추가합니다.
                if apply_id:
                    query += " AND ID = %s"
                    params.append(apply_id)

                if start_date:
                    query += " AND PERIODIC_START >= %s"  # 또는 다른 날짜 컬럼
                    params.append(start_date)

                if end_date:
                    query += " AND PERIODIC_END <= %s"  # 또는 다른 날짜 컬럼
                    params.append(end_date)

                cursor.execute(query, params)
                applications = cursor.fetchall()

                # 조회된 데이터가 없으면 None을 반환합니다.
                if not applications:
                    return []

                # 각 신청에 대한 비주기 시간 데이터를 가져와서 추가합니다.
                for app in applications:
                    app_id = app.get('ID')
                    if app_id:
                        non_periodic_query = "SELECT ID, NON_PERIODIC_START, NON_PERIODIC_END, REGIST_DT, UPDATE_DT, DELETE_AT, APPLY_ID FROM TR_APPLY_NON_PERIODIC WHERE APPLY_ID = %s AND DELETE_AT = 'N'"
                        cursor.execute(non_periodic_query, (app_id,))
                        non_periodic_data = cursor.fetchall()
                        app['nonPeriodicTime'] = non_periodic_data

                # 단일 조회인 경우
                if apply_id:
                    return applications
                    """
                    {
                        "application": applications[0],
                        "response": {
                            "responseCode": 0,
                            "responseMessage": "Success"
                        }
                    }
                    """
                # 전체 조회인 경우
                else:
                    return applications
                    """
                        {
                        "applications": applications,
                        "response": {
                            "responseCode": 0,
                            "responseMessage": "Success"
                        }
                    }
                    """

        except pymysql.MySQLError as e:
            print("Exception : ", e)
            return {
                "application": None,
                "response": {
                    "responseCode": 1,
                    "responseMessage": str(e)
                }
            }

    def get_active_apply_emul_by_channel(self, apply_id):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT 
                    a.APPLYEMUL_SEQ,
                    a.SN,
                    a.DPA_NM,
                    a.OPER_NM,
                    a.FREQUENCY,
                    a.LIC_BAND,
                    ST_AsText(a.RX_AREA) AS RX_AREA,
                    a.RX_NM,
                    a.RX_HEIGHT,
                    a.RX_ANT_PATTERN,
                    a.RX_POLAR,
                    a.RX_ANT_GAIN,
                    a.RX_ANT_WIDTH,
                    a.RX_ANT_AZIM,
                    a.RX_ANT_ELEV,
                    a.RX_FEED,
                    a.RX_NOISE,
                    a.IN_THRESHOLD,
                    a.PERIOD_TYPE,
                    a.PERIODIC_DAY,
                    a.PERIODIC_START,
                    a.PERIODIC_END,
                    a.REGIST_DT,
                    a.UPDATE_DT,
                    a.DELETE_AT,
                    a.ID,
                    get_channels(a.FREQUENCY, a.LIC_BAND) AS APPLY_CHANNEL
                    
                FROM TD_APPLY_EMUL a
                WHERE 
                    -- a.ID = 19
                    1 = 1
                    AND (
                            (a.PERIOD_TYPE = 'periodic'
                             AND NOW() BETWEEN a.PERIODIC_START AND a.PERIODIC_END)
                          OR
                            (a.PERIOD_TYPE = 'nonPeriodic'
                             AND EXISTS (
                                 SELECT 1
                                 FROM TR_APPLY_NON_PERIODIC np
                                 WHERE np.APPLY_ID = a.ID
                                   AND NOW() BETWEEN np.NON_PERIODIC_START AND np.NON_PERIODIC_END
                             ))
                          ) AND JSON_CONTAINS(get_channels(a.FREQUENCY, a.LIC_BAND), '%s', '$');"""
                cursor.execute(query, (apply_id,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def get_active_apply_emul_by_channel_and_mfsd(self, lat, lng, ch):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """SELECT 
                    a.APPLYEMUL_SEQ,
                    a.SN,
                    a.DPA_NM,
                    a.OPER_NM,
                    a.FREQUENCY,
                    a.LIC_BAND,
                    ST_AsText(a.RX_AREA) AS RX_AREA,
                    a.RX_NM,
                    a.RX_HEIGHT,
                    a.RX_ANT_PATTERN,
                    a.RX_POLAR,
                    a.RX_ANT_GAIN,
                    a.RX_ANT_WIDTH,
                    a.RX_ANT_AZIM,
                    a.RX_ANT_ELEV,
                    a.RX_FEED,
                    a.RX_NOISE,
                    a.IN_THRESHOLD,
                    a.PERIOD_TYPE,
                    a.PERIODIC_DAY,
                    a.PERIODIC_START,
                    a.PERIODIC_END,
                    a.REGIST_DT,
                    a.UPDATE_DT,
                    a.DELETE_AT,
                    a.ID,
                    get_channels(a.FREQUENCY, a.LIC_BAND) AS APPLY_CHANNEL

                FROM TD_APPLY_EMUL a
                WHERE 
                    -- a.ID = 19
                    1 = 1
                    AND (
                            (a.PERIOD_TYPE = 'periodic'
                             AND NOW() BETWEEN a.PERIODIC_START AND a.PERIODIC_END)
                          OR
                            (a.PERIOD_TYPE = 'nonPeriodic'
                             AND EXISTS (
                                 SELECT 1
                                 FROM TR_APPLY_NON_PERIODIC np
                                 WHERE np.APPLY_ID = a.ID
                                   AND NOW() BETWEEN np.NON_PERIODIC_START AND np.NON_PERIODIC_END
                             ))
                          )
                    AND DELETE_AT='N' 
                     AND ST_Contains(
                                a.RX_AREA, Point(%s,%s)
                             )
                    AND JSON_CONTAINS(get_channels(a.FREQUENCY, a.LIC_BAND), '%s', '$');"""
                cursor.execute(query, (lng,lat,ch))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

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