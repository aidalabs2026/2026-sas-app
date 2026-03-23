import pymysql
import json

from esc_emul_std_alone_v1_0.EscStdAloneDao import EscStdAloneDao


class EscStdAloneApi:
    def __init__(self, db_config):
        self.db_config = db_config
        #self.connection = self.connect()
        self.db_config = "esc_std_alone.sqlite3"

        #self.CbsdDao = CbsdDao(db_config)
        self.EscDao = EscStdAloneDao(self.db_config)

    """
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
            print("Connected to MySQL database")
            return connection
        except Exception as e:
            print(f"Connection error: {e}")
            return None
    """

    def sensor_exists(self, sensor_id):
        try:
            return self.EscDao.esc_exists(sensor_id)
        except Exception as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sensor_ch_exists(self, sensor_id):
        try:
            return self.EscDao.esc_ch_exists(sensor_id)
        except Exception as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def sensor_list(self):
        try:
            return self.EscDao.esc_list()
        except Exception as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def sensor_sensor_delete(self, sensor_id):
        try:
            return self.EscDao.esc_sensor_delete(sensor_id)
        except Exception as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def sensor_channel_list(self, sensor_id):
        try:
            result = self.EscDao.sensor_channel_list(sensor_id)
            return result
        except Exception as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def register(self, esc):
        try:
            esc_sensor = self.EscDao.esc_search(esc.escSensorId)
            print(esc_sensor)
            if len(esc_sensor) > 0 and esc_sensor[0]['STATUS'] == "REGIST":
                if not self.sensor_ch_exists(esc.escSensorId):
                    self.EscDao.esc_channels_insert(esc)

                self.EscDao.esc_update(esc)

                return {
                    "escSensorId": esc.escSensorId,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": "Already registed"
                    }
                }
            else:
                if len(esc_sensor) == 0:
                    self.EscDao.esc_delete_all()
                    self.EscDao.esc_channels_delete_all()
                    self.EscDao.esc_insert(esc)
                    self.EscDao.esc_channels_delete(esc.escSensorId)
                    self.EscDao.esc_channels_insert(esc)

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
                    self.EscDao.esc_update(esc)

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
        except Exception as e:
            return {
                    "escSensorId": esc.escSensorId,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": str(e)
                    }
                }

    def deregister(self, esc):
        try:
            self.EscDao.esc_delete(esc.escSensorId)
            return {
                "escSensorId": esc.escSensorId,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }
        except Exception as e:
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

            return response


        except Exception as e:
            response["response"]["responseCode"] = 1
            response["response"]["responseMessage"] = str(e)
            return response

    def sensing_result_process(self, esc_sensor_id, sensing_result):
        incumbentUserActivation = sensing_result["incumbentUserActivation"]
        lowFrequency = sensing_result["frequencyRange"]["lowFrequency"]
        highFrequency = sensing_result["frequencyRange"]["highFrequency"]

        try:
            if incumbentUserActivation:  # esc센서가 incumbent user 를 감지했을 때,
                # 1. 해당 주파수 대역에 grant 받은 cbsd가 있는지 조회한다.
                grant_list = self.CbsdDao.grant_list_by_freq(lowFrequency, highFrequency, "AUTHORIZED", 0)

                self.EscDao.esc_ch_update_status(esc_sensor_id, lowFrequency, highFrequency, 1)

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

                self.EscDao.esc_ch_update_status(esc_sensor_id, lowFrequency, highFrequency, 0)
        except pymysql.MySQLError as e:
            print(e)
            return
    def esc_ch_update_status(self, sensor_id, lowFreq, highFreq, status):
        self.EscDao.esc_ch_update_status(sensor_id, lowFreq, highFreq, status)

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")