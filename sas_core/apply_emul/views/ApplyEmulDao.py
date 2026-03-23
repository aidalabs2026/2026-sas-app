import pymysql
import json
from datetime import datetime, timedelta
import pytz

class ApplyEmulDao:
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
                autocommit=True
            )
            print("ApplyEmulDAO : Connected to MySQL database")

        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")

    def applyList(self):
        try:
            #self.connect()
            with self.connection.cursor() as cursor:
                query = """
                    SELECT 
                        A.APPLYEMUL_SEQ, A.SN, A.DPA_NM, A.OPER_NM, A.FREQUENCY, A.LIC_BAND, A.RX_NM, A.RX_HEIGHT,
                        A.RX_ANT_PATTERN, A.RX_POLAR, A.RX_ANT_GAIN, A.RX_ANT_WIDTH, A.RX_ANT_AZIM, A.RX_ANT_ELEV,
                        A.RX_FEED, A.RX_NOISE, A.IN_THRESHOLD, A.PERIOD_TYPE, A.PERIODIC_DAY, A.REGIST_DT,
                        DATE_FORMAT(A.PERIODIC_START, '%H:%i') AS PERIODIC_START,
                        DATE_FORMAT(A.PERIODIC_END, '%H:%i') AS PERIODIC_END,
                        ST_AsText(A.RX_AREA) AS RX_AREA
                    FROM TD_APPLY_EMUL A
                    WHERE A.DELETE_AT = 'N'
                    ORDER BY A.REGIST_DT DESC;
                """
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def applyList11(self):
        try:
            #self.connect()
            with self.connection.cursor() as cursor:
                query = """
                    SELECT 
                        A.ID, A.SN, A.DPA_NM, A.OPER_NM, A.FREQUENCY, A.LIC_BAND, A.RX_NM, A.RX_HEIGHT,
                        A.RX_ANT_PATTERN, A.RX_POLAR, A.RX_ANT_GAIN, A.RX_ANT_WIDTH, A.RX_ANT_AZIM, A.RX_ANT_ELEV,
                        A.RX_FEED, A.RX_NOISE, A.IN_THRESHOLD, A.PERIOD_TYPE, A.PERIODIC_DAY, A.REGIST_DT,
                        DATE_FORMAT(A.PERIODIC_START, '%H:%i') AS PERIODIC_START,
                        DATE_FORMAT(A.PERIODIC_END, '%H:%i') AS PERIODIC_END,
                        ST_AsText(A.RX_AREA) AS RX_AREA,
                        (
                            SELECT JSON_ARRAYAGG(
                                       JSON_OBJECT(
                                           'id', B.ID,
                                           'nonPeriodicDate', B.NON_PERIODIC_DATE,
                                           'startTime', B.NON_PERIODIC_START,
                                           'endTime', B.NON_PERIODIC_END
                                       )
                                   )
                            FROM TR_APPLY_NON_PERIODIC B
                            WHERE B.APPLYEMUL_SEQ = A.APPLYEMUL_SEQ
                              AND B.DELETE_AT = 'N'
                            ORDER BY B.ID ASC
                        ) AS nonPeriodicList
                    FROM TD_APPLY_EMUL A
                    WHERE A.DELETE_AT = 'N'
                    ORDER BY A.REGIST_DT DESC;
                """
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def applyDel(self, seq):
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                query = """
                    UPDATE 
                        TD_APPLY_EMUL 
                    SET 
                        DELETE_AT = 'Y' 
                    WHERE APPLYEMUL_SEQ = %s
                """
                cursor.execute(query, (seq,))
                self.connection.commit()
                return True
        except pymysql.MySQLError as e:
            return False


    def applyTest(self, ID):
        try:
            # self.connect()
            with self.connection.cursor() as cursor:
                query = """
                    SELECT 
                        A.APPLYEMUL_SEQ, A.SN, A.DPA_NM, A.OPER_NM, A.FREQUENCY, A.LIC_BAND, A.RX_NM, A.RX_HEIGHT,
                        A.RX_ANT_PATTERN, A.RX_POLAR, A.RX_ANT_GAIN, A.RX_ANT_WIDTH, A.RX_ANT_AZIM, A.RX_ANT_ELEV,
                        A.RX_FEED, A.RX_NOISE, A.IN_THRESHOLD, A.PERIOD_TYPE, A.PERIODIC_DAY, A.REGIST_DT,
                        DATE_FORMAT(A.PERIODIC_START, '%%H:%%i') AS PERIODIC_START,
                        DATE_FORMAT(A.PERIODIC_END, '%%H:%%i') AS PERIODIC_END,
                        ST_AsText(A.RX_AREA) AS RX_AREA
                    FROM TD_APPLY_EMUL A
                    WHERE A.DELETE_AT = 'N'
                        AND ID = %s
                    ORDER BY A.REGIST_DT DESC;
                """
                cursor.execute(query, (ID,))
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def close(self):
        """ 데이터베이스 연결 종료 """
        if self.connection:
            self.connection.close()