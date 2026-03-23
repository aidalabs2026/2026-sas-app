import pymysql
import json

from api.CbsdDao import CbsdDao
from api.EscEmulDao import EscEmulDao


class EscEmulApi:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = self.connect()

        self.CbsdDao = CbsdDao(db_config)
        self.EscEmulDao = EscEmulDao(db_config)

    def connect(self):
        try:
            connection = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("ESCAPI : Connected to MySQL database")
            return connection
        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")
            return None

    def sensor_exists(self, sensor_id):
        try:
            return self.EscEmulDao.esc_exists(sensor_id)
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sensor_ch_exists(self, sensor_id):
        try:
            return self.EscEmulDao.esc_ch_exists(sensor_id)
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sensor_list(self):
        try:
            return self.EscEmulDao.esc_list()
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def registed_sensor_list(self):
        try:
            return self.EscEmulDao.esc_registed_list()
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None


    def sensor_sensor_delete(self, sensor_id):
        try:
            return self.EscEmulDao.esc_sensor_delete(sensor_id)
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def sensor_channel_list(self, sensor_id):
        try:
            result = self.EscEmulDao.sensor_channel_list(sensor_id)
            return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def register(self, esc):
        try:
            esc_sensor = self.EscEmulDao.esc_search(esc.escSensorId)
            print(esc_sensor)
            if len(esc_sensor) > 0 and esc_sensor[0]['STATUS'] == "REGIST":
                if not self.sensor_ch_exists(esc.escSensorId):
                    self.EscEmulDao.esc_channels_insert(esc)
                return {
                    "escSensorId": esc.escSensorId,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": "Already registed"
                    }
                }
            else:
                if len(esc_sensor) == 0:
                    self.EscEmulDao.esc_insert(esc)
                    self.EscEmulDao.esc_channels_delete(esc.escSensorId)
                    self.EscEmulDao.esc_channels_insert(esc)

                    return {
                        "escSensorId": esc.escSensorId,
                        "dpaId": esc.dpaId,
                        "sensingResultTxInterval": 60,
                        "incumbentUserDeactivationDecisionTime": 3600,
                        "response": {
                            "responseCode": 0,
                            "responseMessage": "SUCCESS"
                        }
                    }
                else:
                    self.EscEmulDao.esc_update(esc)
                    if not self.sensor_ch_exists(esc.escSensorId):
                        self.EscEmulDao.esc_channels_insert(esc)

                    return {
                        "escSensorId": esc.escSensorId,
                        "dpaId": esc.dpaId,
                        "sensingResultTxInterval": 60,
                        "incumbentUserDeactivationDecisionTime": 3600,
                        "response": {
                            "responseCode": 0,
                            "responseMessage": "SUCCESS"
                        }
                    }
        except pymysql.MySQLError as e:
            return {
                    "escSensorId": esc.escSensorId,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": str(e)
                    }
                }

    def channel_insert(self, escSensorId):
        if not self.sensor_ch_exists(escSensorId):
            self.EscEmulDao.esc_channels_insert2(escSensorId)

    def deregister(self, esc):
        try:
            self.EscEmulDao.esc_delete(esc.escSensorId)
            return {
                "escSensorId": esc.escSensorId,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }
        except pymysql.MySQLError as e:
            return {
                    "escSensorId": esc.escSensorId,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": str(e)
                    }
                }

    def sensing_result_report(self, esc, reqdata):

        esc_sensor_id = esc.escSensorId
        dpa_id = esc.dpaId

        response = {
            "escSensorId": esc_sensor_id,
            "sensingResultTxInterval": 60,
            "incumbentUserDeactivationDecisionTime": 3600,
            "response": {
                "responseCode": 0,
                "responseMessage": "SUCCESS"
            }
        }

        try:
            for sensing_result in esc.sensingResult:
                self.sensing_result_process(esc_sensor_id, sensing_result)

            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_SENSOR_RESULTS (SENSOR_ID, RESULT, REPORT_TIME) 
                           VALUES (%s, %s, NOW())"""
                cursor.execute(query, (esc.escSensorId, json.dumps(reqdata)))
                self.connection.commit()

            # 센서의 마지막 센서 시간을 업데이트한다.
            self.EscEmulDao.esc_last_report_dt_update(esc)

            return response

        except pymysql.MySQLError as e:
            response["response"]["responseCode"] = 1
            response["response"]["responseMessage"] = str(e)
            return response

    def sensing_result_process(self, esc_sensor_id, sensing_result):
        incumbentUserActivation = sensing_result["incumbentUserActivation"]
        lowFrequency = sensing_result["frequencyRange"]["lowFrequency"]
        highFrequency = sensing_result["frequencyRange"]["highFrequency"]

        try:
            # incumbentUserActivation 의 직전 상태와 비교하여, 동일하면 처리하지 않는다.
            pre_incumbentUserActivation = self.EscEmulDao.esc_ch_get_status(esc_sensor_id, lowFrequency, highFrequency)

            if pre_incumbentUserActivation == incumbentUserActivation:
                print(f'이전 incumbentUserActivation 의 상태({pre_incumbentUserActivation}) 가 현재 incumbentUserActivation의 상태({incumbentUserActivation}) 와 동일함.')
                return
            else:
                print(
                    f'이전 incumbentUserActivation 의 상태({pre_incumbentUserActivation}) 가 현재 incumbentUserActivation의 상태({incumbentUserActivation}) 로 변경됨.')

            if incumbentUserActivation:  # esc센서가 incumbent user 를 감지했을 때,
                # 새로운 절차 2025
                # 1. esc 가 속한 e_dpa를 구하고, move_list 를 가져온다.
                # 2. move_list 중에서 현재 esc 가 센싱한 채널을 사용하는 grant 가 있는지 확인하고 그 목록을 가져온다.

                # 1. 해당 주파수 대역에 grant 받은 cbsd가 있는지 조회한다.
                #grant_list = self.CbsdDao.grant_list_by_freq(lowFrequency, highFrequency, "AUTHORIZED", 0)
                grant_list = self.CbsdDao.get_move_list_by_e_dpa(esc_sensor_id, lowFrequency, highFrequency, "AUTHORIZED", 0)
                self.EscEmulDao.esc_ch_update_status(esc_sensor_id, lowFrequency, highFrequency, 1)

                # 2. 각 CBSD 의 조회 된 grant 상태를 suspend 로 바꾸고,
                for grant in grant_list:
                    self.CbsdDao.grant_update_suspend_at(grant["GRANT_ID"], 1)
                    self.CbsdDao.grant_update_status(grant["GRANT_ID"], "GRANTED")
                    # 3. CBSD 의 상태를 SUSPEND 로 바꾼다.
                    # self.CbsdDao.cbsd_update_status(grant["CBSD_ID"], "SUSPEND")

            else:  # esc 센서가 incumbent user 를 해제했을 때
                grant_list = self.CbsdDao.grant_list_by_freq(lowFrequency, highFrequency, "GRANTED", 1)

                for grant in grant_list:
                    self.CbsdDao.grant_update_status(grant["GRANT_ID"], "AUTHORIZED")
                    self.CbsdDao.grant_update_suspend_at(grant["GRANT_ID"], 0)
                    # 3. CBSD 의 상태를 SUSPEND 로 바꾼다.
                    # if len(self.CbsdDao.grant_list_by_status(grant["CBSD_ID"], "SUSPEND")) == 0:
                    #    self.CbsdDao.cbsd_update_status(grant["CBSD_ID"], "AUTHORIZED")

                self.EscEmulDao.esc_ch_update_status(esc_sensor_id, lowFrequency, highFrequency, 0)
        except pymysql.MySQLError as e:
            print(e)
            return
    def esc_ch_update_status(self, sensor_id, lowFreq, highFreq, status):
        self.EscEmulDao.esc_ch_update_status(sensor_id, lowFreq, highFreq, status)

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")