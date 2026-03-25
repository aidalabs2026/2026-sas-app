import pymysql
import copy
import json
from datetime import datetime, timedelta

from api.CBSDErrorCodes import CBSDErrorCodes
from api.CbsdDao import CbsdDao
from api.EscDao import EscDao
from api.SdDao import SdDao
from api.SysPropDao import SysPropDao



class CbsdApi:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = self.connect()

        self.CbsdDao = CbsdDao(db_config)
        self.EscDao = EscDao(db_config)
        self.SysPropDao = SysPropDao(db_config)
        self.SdDao = SdDao(db_config)

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
            print("CBSDAPI : Connected to MySQL database")
            return connection
        except pymysql.MySQLError as e:
            print(f"Connection error: {e}")
            return None

    def cbsd_exists(self, cbsd_id):
        return self.CbsdDao.cbsd_exists(cbsd_id)

    def cbsd_list(self):
        result = self.CbsdDao.cbsd_list()
        return result
        '''
        try:
            with self.connection.cursor() as cursor:
                query = """SELECT * FROM TD_CBSD_REGIST ORDER BY CBSD_ID ASC"""
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None
        '''

    def dpa_list(self):
        result = self.CbsdDao.dpa_list()
        return result

    def grant_list(self, cbsd_id):
        result = self.CbsdDao.grant_list(cbsd_id)
        return result

    def register(self, cbsd):

        # 1. regist 가능 여부 확인 로직
        cbsd_id = f'{cbsd["userId"]}/{cbsd["cbsdSerialNumber"]}'
        if self.cbsd_exists(cbsd_id):
            self.CbsdDao.cbsd_update_status(cbsd_id, "REGIST")
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

        # 2. regist 응답 생성
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
        cbsd["status"] = 'REGIST'

        # 3. regist 데이터 베이스에 기록
        try:
            self.CbsdDao.cbsd_insert(cbsd, cbsd_id)

            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }
        except pymysql.MySQLError as e:
            print(e)
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    def deregister(self, cbsd_id):
        try:
            # 1. grant 삭제
            self.CbsdDao.grant_delete_by_cbsdid(cbsd_id)

            # 2. cbsd 삭제
            self.CbsdDao.cbsd_delete(cbsd_id)
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }
        except pymysql.MySQLError as e:
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    def cbsd_delete(self, cbsd_id):
        try:
            return self.CbsdDao.cbsd_device_delete(cbsd_id)
        except pymysql.MySQLError as e:
            print(f"Error checking sensor existence: {e}")
            return None

    def spectrumInquery(self, request_data):
        availableChannelList = []
        # 1. 주파수 사용 가능 여부 확인 로직 실행
        # 현재는 ESC 가 센싱하는 채널들 중 1차 사용자가 감지된 채널은 사용불가로 반환한다.
        # w
        sensing_ch_list = self.EscDao.esc_sensing_channel_status()

        if sensing_ch_list != None:

            for sensing_ch in sensing_ch_list:
                availableChannel = {
                    "frequencyRange": {"lowFrequency": sensing_ch["LOW_FREQ"], "highFrequency": sensing_ch["HIGH_FREQ"]},
                    "channelType": "PAL",
                    "ruleApplied": "FCC Part 96",
                    "maxEirp": 30 if sensing_ch["COUNT_USER_1"] == 0 else 0
                }
                availableChannelList.append(availableChannel)
        # 2. 주파수 사용 가능으로 응답 생성
        try:
            cbsd_id = request_data["cbsdId"]
            e_dpas = self.find_dpa_by_cbsd_id(cbsd_id)

            return {
                "cbsdId": cbsd_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                },
                "availableChannel": availableChannelList
            }
        except pymysql.MySQLError as e:
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    # Event SD 기반 SpectrumInquery 처리 함수
    def spectrumInqueryBySD(self, request_data):
        availableChannelList = []
        # 1. 주파수 사용 가능 여부 확인 로직 실행
        # 현재는 ESC 가 센싱하는 채널들 중 1차 사용자가 감지된 채널은 사용불가로 반환한다.

        # 2. 주파수 사용 가능으로 응답 생성
        try:
            base_freq = 3300000000  # CH 1의 LOW_FREQ 기준 (3.3GHz)
            channel_bw = 10000000  # 채널당 대역폭 10MHz
            cbsd_id = request_data["cbsdId"]
            channel_info = self.SdDao.get_available_ch(cbsd_id)

            for i in range(1, 11):
                avail_power = channel_info[f"SD_CH_{i}"]
                # 채널별 주파수 계산
                low_freq = base_freq + (i - 1) * channel_bw
                high_freq = low_freq + channel_bw

                availableChannel = {
                    "frequencyRange": {"lowFrequency": low_freq,
                                       "highFrequency": high_freq},
                    "channelType": "PAL",
                    "ruleApplied": "FCC Part 96",
                    "maxEirp": 30 if avail_power == 45 else 0
                }
                availableChannelList.append(availableChannel)


            return {
                "cbsdId": cbsd_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                },
                "availableChannel": availableChannelList
            }
        except pymysql.MySQLError as e:
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    def grant(self, request_data):
        base_freq = 3300000000  # CH 1의 LOW_FREQ 기준 (3.3GHz)
        channel_bw = 10000000   # 채널당 대역폭 10MHz
        cbsd_id = request_data.get("cbsdId", "")

        try:
            lowFrequency = int(request_data["operationParam"]["operationFrequencyRange"]["lowFrequency"])
            highFrequency = int(request_data["operationParam"]["operationFrequencyRange"]["highFrequency"])
        except (KeyError, TypeError, ValueError):
            return self._error_response(cbsd_id, "", "MISSING_PARAM")

        grant_id = f'{cbsd_id}/{lowFrequency / 1000000}'

        # G4. CBSD 등록 확인
        if not self.CbsdDao.cbsd_exists(cbsd_id):
            return self._error_response(cbsd_id, grant_id, "DEREGISTER")

        # G5. 주파수 범위 검증
        if lowFrequency >= highFrequency or lowFrequency < base_freq or highFrequency > (base_freq + channel_bw * 10):
            return self._error_response(cbsd_id, grant_id, "UNSUPPORTED_SPECTRUM")

        ch_no = int((lowFrequency - base_freq) / channel_bw) + 1
        if ch_no < 1 or ch_no > 10:
            return self._error_response(cbsd_id, grant_id, "UNSUPPORTED_SPECTRUM")

        try:
            sysprop_grantexpiretime = int(self.SysPropDao.prop_get("GRANT_EXPIRETIME") or 600)
            sysprop_heartbeat_intval = int(self.SysPropDao.prop_get("HEARTBEAT_INTERVAL") or 60)
            if sysprop_heartbeat_intval <= 0:
                sysprop_heartbeat_intval = 60

            formatted_time_with_z = self.calcTime(sysprop_grantexpiretime)

            # G1. 중복 확인 (1회만)
            if self.CbsdDao.grant_exists(grant_id):
                return self._error_response(cbsd_id, grant_id, "GRANT_CONFLICT")

            # 채널 가용성 확인
            channel_info = self.SdDao.get_available_ch(cbsd_id)
            avail_power = channel_info[f"SD_CH_{ch_no}"] if channel_info else 0

            if avail_power <= 0:
                return self._error_response(cbsd_id, grant_id, "UNSUPPORTED_SPECTRUM")

            # Grant 승인 — 응답 생성
            response = {
                "cbsdId": cbsd_id,
                "grantId": grant_id,
                "transmitExpireTime": formatted_time_with_z,
                "grantExpireTime": formatted_time_with_z,
                "heartbeatDuration": sysprop_heartbeat_intval,
                "heartbeatInterval": sysprop_heartbeat_intval,
                "measReportConfig": {},
                "operationParam": {
                    "maxEirp": 30,
                    "operationFrequencyRange": {"lowFrequency": lowFrequency, "highFrequency": highFrequency}
                },
                "channelType": "PAL",
                "response": {
                    "responseCode": CBSDErrorCodes.get_error("SUCCESS").code,
                    "responseMessage": CBSDErrorCodes.get_error("SUCCESS").name
                }
            }

            # G1. DB INSERT (UNIQUE 위반 시 GRANT_CONFLICT)
            if not self.CbsdDao.grant_insert(response, grant_id, cbsd_id):
                return self._error_response(cbsd_id, grant_id, "GRANT_CONFLICT")

            return response

        except (pymysql.MySQLError, Exception) as e:
            # G2. 에러 시 에러 코드 반환 (SUCCESS 아님)
            print(f"Grant error: {e}")
            return self._error_response(cbsd_id, grant_id, "MISSING_PARAM")

    def heartbeat(self, request_data, broadcast_message=None):
        cbsd_id = request_data.get("cbsdId", "")
        grant_id = request_data.get("grantId", "")

        try:
            grantRenew = request_data.get("grantRenew", False)
            responseCode = 0
            responseMsg = "SUCCESS"

            sysprop_operparam_on = int(self.SysPropDao.prop_get("OPERPARAM_ON") or 0)
            sysprop_heartbeat_intval = int(self.SysPropDao.prop_get("HEARTBEAT_INTERVAL") or 60)
            sysprop_grantexpiretime = int(self.SysPropDao.prop_get("GRANT_EXPIRETIME") or 600)
            if sysprop_heartbeat_intval <= 0:
                sysprop_heartbeat_intval = 60

            # Grant 유효성 확인
            grant_info = self.CbsdDao.grant_list_by_grantid(grant_id)
            if grant_info is None:
                return {
                    "cbsdId": cbsd_id,
                    "grantId": grant_id,
                    "grantRenew": False,
                    "transmitExpireTime": self.calcTime(0),
                    "grantExpireTime": self.calcTime(0),
                    "heartbeatDuration": sysprop_heartbeat_intval,
                    "heartbeatInterval": sysprop_heartbeat_intval,
                    "response": {
                        "responseCode": CBSDErrorCodes.get_error("TERMINATED_GRANT").code,
                        "responseMessage": CBSDErrorCodes.get_error("TERMINATED_GRANT").name
                    }
                }

            # H2. Grant의 실제 주파수 (SUSPEND 시에도 올바른 값)
            oper_low_freq = grant_info["LOW_FREQ"]
            oper_high_freq = grant_info["HIGH_FREQ"]

            # H1. DB에서 현재 grantExpireTime 읽기 (빈 문자열 방지)
            db_grant_expire = grant_info.get("GRANT_EXPIRETIME")
            if db_grant_expire:
                if isinstance(db_grant_expire, datetime):
                    grantExpireTime = db_grant_expire.strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    grantExpireTime = str(db_grant_expire)
            else:
                grantExpireTime = self.calcTime(sysprop_grantexpiretime)

            formatted_time_with_z = self.calcTime(sysprop_grantexpiretime)

            # Grant 상태 분기
            if grant_info["SUSPEND_AT"] == 1:
                formatted_time_with_z = self.calcTime(0)
                responseCode = CBSDErrorCodes.get_error("SUSPENDED_GRANT").code
                responseMsg = CBSDErrorCodes.get_error("SUSPENDED_GRANT").name
                self.CbsdDao.grant_update_expiretime(grant_id, transmit_expiretime=formatted_time_with_z)

            elif grant_info.get("EVENT_TRIGGER") == "TERMINATED_GRANT":
                responseCode = CBSDErrorCodes.get_error("TERMINATED_GRANT").code
                responseMsg = CBSDErrorCodes.get_error("TERMINATED_GRANT").name
                formatted_time_with_z = self.calcTime(0)
                self.CbsdDao.grant_update_expiretime(grant_id, transmit_expiretime=formatted_time_with_z)

            elif grant_info.get("EVENT_TRIGGER") == "UNSYNC_OP_PARAM":
                responseCode = CBSDErrorCodes.get_error("UNSYNC_OP_PARAM").code
                responseMsg = CBSDErrorCodes.get_error("UNSYNC_OP_PARAM").name
                formatted_time_with_z = self.calcTime(0)
                self.CbsdDao.grant_update_expiretime(grant_id, transmit_expiretime=formatted_time_with_z)

            else:
                # 정상 상태
                if grant_info["STATUS"] in ("GRANT", "GRANTED"):
                    self.CbsdDao.grant_update_status(grant_id, "AUTHORIZED")
                    if broadcast_message is not None:
                        broadcast_message["is_send"] = True

                if grantRenew:
                    grantExpireTime = self.calcTime(sysprop_grantexpiretime)
                    self.CbsdDao.grant_update_expiretime(grant_id, grantExpireTime, formatted_time_with_z)
                else:
                    self.CbsdDao.grant_update_expiretime(grant_id, transmit_expiretime=formatted_time_with_z)

            # OPERPARAM_ON: 강제 채널 이동
            operationParamFlag = sysprop_operparam_on != 0
            if operationParamFlag:
                oper_high_freq = 3300000000 + (sysprop_operparam_on * 10000000)
                oper_low_freq = oper_high_freq - 10000000

            # H3. 응답 구조 통합 (중복 제거)
            resp = {
                "cbsdId": cbsd_id,
                "grantId": grant_id,
                "grantRenew": grantRenew,
                "operationStatusReq": True,
                "transmitExpireTime": formatted_time_with_z,
                "grantExpireTime": grantExpireTime,
                "heartbeatDuration": sysprop_heartbeat_intval,
                "heartbeatInterval": sysprop_heartbeat_intval,
                "measReportConfig": {},
                "response": {
                    "responseCode": responseCode,
                    "responseMessage": responseMsg
                }
            }

            if operationParamFlag:
                resp["operationParam"] = {
                    "maxEirp": 30,
                    "operationFrequencyRange": {"lowFrequency": oper_low_freq, "highFrequency": oper_high_freq}
                }

            return resp

        except (pymysql.MySQLError, Exception) as e:
            # H4. 에러 시 에러 코드 반환
            print(f"Heartbeat error: {e}")
            return {
                "cbsdId": cbsd_id,
                "grantId": grant_id,
                "grantRenew": False,
                "transmitExpireTime": self.calcTime(0),
                "grantExpireTime": self.calcTime(0),
                "heartbeatDuration": 60,
                "heartbeatInterval": 60,
                "response": {
                    "responseCode": CBSDErrorCodes.get_error("MISSING_PARAM").code,
                    "responseMessage": "Internal server error"
                }
            }

    def relinquishment(self, request_data):
        try:

            cbsd_id = request_data["cbsdId"]
            grant_id = request_data["grantId"]

            # 1. grant 정보 데이터베이스에서 해당 grant 삭제
            if self.CbsdDao.grant_exists(grant_id):
                self.CbsdDao.grant_delete(grant_id)
                #if len(self.CbsdDao.suspend_grant_list(cbsd_id)) > 0:
                #    self.CbsdDao.cbsd_update_status(cbsd_id, "SUSPEND")
                #if len(self.CbsdDao.grant_list_by_status(cbsd_id, "AUTHORIZED")) > 0:
                #    self.CbsdDao.cbsd_update_status(cbsd_id, "AUTHORIZED")
                #else:
                #    self.CbsdDao.cbsd_update_status(cbsd_id, "REGIST")

            # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
            return {
                "cbsdId": cbsd_id,
                "grantId": grant_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }
        except pymysql.MySQLError as e:
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    def sensing_result_report(self, esc):
        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_SENSOR_RESULTS (SENSOR_ID, RESULT, REPORT_TIME) 
                           VALUES (%s, %s, NOW())"""
                cursor.execute(query, (esc.escSensorId, json.dumps(esc)))
                self.connection.commit()
                return {"status": "success", "message": "Sensing result reported successfully"}
        except pymysql.MySQLError as e:
            return {"status": "error", "message": str(e)}

    def find_dpa_by_cbsd_id(self, cbsd_id):
        cbsd_info = self.CbsdDao.cbsd_list_by_cbsd_id(cbsd_id)
        if len(cbsd_info) == 1:
            cbsd = cbsd_info[0]

            e_dpas = self.CbsdDao.find_e_dpa_by_loc(cbsd["LAT"], cbsd["LNG"])
            return e_dpas
        return []

    def check_last_grant_time(self, interval):
        return self.CbsdDao.check_last_grant_time(interval)

    def grant_delete(self,grant_id):
        self.CbsdDao.grant_delete(grant_id)

    def prop_load(self):
        return self.SysPropDao.prop_list()

    def prop_update(self, key, value):
        self.SysPropDao.prop_update(key, value)

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")

    def _error_response(self, cbsd_id, grant_id, error_name):
        """에러 응답 생성 헬퍼"""
        err = CBSDErrorCodes.get_error(error_name)
        return {
            "cbsdId": cbsd_id,
            "grantId": grant_id,
            "response": {
                "responseCode": err.code,
                "responseMessage": err.name
            }
        }

    def calcTime(self, sec):
        # G6. UTC 시간 사용 (기존: 로컬 시간에 UTC 라벨만 부착하는 버그)
        now = datetime.utcnow()
        future_time = now + timedelta(seconds=sec)
        return future_time.strftime('%Y-%m-%dT%H:%M:%SZ')




