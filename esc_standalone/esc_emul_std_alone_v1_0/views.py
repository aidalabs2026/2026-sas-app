from pyramid.view import view_config
from pyramid.response import Response
import json
from datetime import datetime

#from api.CbsdApi import CbsdApi
import requests
import threading
import time
import asyncio

from types import SimpleNamespace


from aiohttp import web

from api.property import SettingsManager
from esc_emul_std_alone_v1_0.EscStdAloneApi import EscStdAloneApi
from esc_emul_std_alone_v1_0.MsgLogDao import MsgLogDao
from esc_emul_std_alone_v1_0.SysPropDao import SysPropDao
#from websocket.ClientManager import ClientManager
from esc_emul_std_alone_v1_0.SensingManager import SensingManager

from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout


heartbeatManager = SensingManager()

periodic_thread = {}

#client_manager = ClientManager()

class PeriodicThread:
    def __init__(self, interval, target, *args, **kwargs):
        self.interval = interval
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run)

    def _run(self):
        while not self._stop_event.is_set():
            start_time = time.time()
            global df_log_data
            self.target(*self.args, **self.kwargs)

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.thread.join()

# 예제 테이블 데이터
table_data = [
    {"id": 1, "name": "John Doe", "email": "john@example.com"},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
    {"id": 3, "name": "Alice Johnson", "email": "alice@example.com"},
]

default_data = {
    "userId": "user-1234",
    "fccId": "msit-1234",
    "cbsdCategory": "B",
    "callSign": "n.a.",
    "userId": "John Doe",
    "airInterface": {
        "radioTechnology": "6G",
        "supportedSpec": "LTE-Rel10"
    },
    "cbsdInfo": {
        "vendor": "ETRI",
        "model": "etri-1234",
        "softwareVersion" : 1.0,
        "hardwareVersion" : 1.0,
        "firmwareVersion" : 1.0
    },
    "cbsdSerialNumber": "sn-1234",
    "measCapability": [],
    "installationParam": {
        "latitude": 37.425056,
        "longitude": -122.084113,
        "height": 9.3,
        "heightType": "AGL",
        "horizontalAccuracy": "n.a.",
        "verticalAccuracy": "n.a.",
        "indoorDeployment": False,
        "antennaAzimuth": 0,
        "antennaDowntilt": 15,
        "antennaGain": 18,
        "eirpCapability": 47,
        "antennaBeamwidth": 65,
        "antennaModel": "ant-1234"
    }
}

config_file_path = 'config.json'

# 설정 매니저 인스턴스 생성
#settings_manager = SettingsManager(config_file_path)
#settings_manager.load_settings()

#db_config = {
#    'host': settings_manager.get_setting("host"),
#    'user': settings_manager.get_setting("user"),
#    'password': settings_manager.get_setting("password"),
#    'database': settings_manager.get_setting("database"),
#}

#cbsdApi = CbsdApi(db_config)
escApi = EscStdAloneApi("")
msgLogDao = MsgLogDao("")
sysPropDao = SysPropDao("")

esc_list = escApi.sensor_list()
if len(esc_list) > 0:
    heartbeatManager.start_heartbeat(esc_list[0]["SENSOR_ID"], 60)

@view_config(route_name='index', renderer='./templates/main.jinja2')
def index_view(request):
    return {"table_data": table_data, "default_data": default_data}

@view_config(route_name='msglog', renderer='./templates/msgSequence.jinja2')
def msglog_view(request):
    device_id = request.matchdict.get('device_id')

    esc_id = f"{device_id}"

    msg_list = msgLogDao.list_by_deviceid(esc_id)

    for item in msg_list:
        if isinstance(item['MSSAGE'], bytes):
            item['MSSAGE'] = item['MSSAGE'].decode('utf-8')
            item['MSSAGE'] = item['MSSAGE'].replace('"', "'")

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return {"device_id": f"{device_id}", "data" : json_object}

@view_config(route_name='msglogview', renderer='./templates/msgSequenceView.jinja2')
def msglogview_view(request):
    device_id = request.matchdict.get('device_id')

    esc_id = f"{device_id}"

    msg_list = msgLogDao.list_by_deviceid(esc_id)

    for item in msg_list:
        if isinstance(item['MSSAGE'], bytes):
            item['MSSAGE'] = item['MSSAGE'].decode('utf-8')
            item['MSSAGE'] = item['MSSAGE'].replace('"', "'")

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return {"device_id": f"{device_id}", "data" : json_object}

@view_config(route_name='get_data', renderer='json')
def get_data_view(request):
    return {"table_data": table_data}

@view_config(route_name='update_form', renderer='json')
def update_form_view(request):
    row_id = int(request.params.get('id', 0))
    # 테이블에서 선택한 ID에 해당하는 데이터를 반환
    selected_data = next((row for row in table_data if row["id"] == row_id), None)
    return selected_data if selected_data else {}

@view_config(route_name='api/regist', renderer='json', request_method='POST')
def regist(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        sas_url = sysPropDao.prop_get("sas_url")

        if not sas_url:
            raise ValueError("SAS URL 설정이 존재하지 않습니다.")

        # 외부 요청 시도
        try:
            response = requests.post(f'{sas_url}/esc_regist', json=payload)
            response.raise_for_status()  # HTTP 오류가 있으면 예외 발생
        except (ConnectionError, Timeout) as conn_err:
            print(f"접속 오류: {conn_err}")
            return Response(
                status=503,
                json_body={'status': 'error', 'message': f"SAS 서버에 연결할 수 없습니다: {conn_err}"}
            )
        except HTTPError as http_err:
            print(f"HTTP 오류: {http_err}")
            return Response(
                status=response.status_code,
                json_body={'status': 'error', 'message': f"HTTP 오류 발생: {http_err}"}
            )
        except RequestException as req_err:
            print(f"요청 실패: {req_err}")
            return Response(
                status=500,
                json_body={'status': 'error', 'message': f"요청 중 오류가 발생했습니다: {req_err}"}
            )
        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)
        else:
            # dict를 객체처럼 변환
            esc = SimpleNamespace(**payload)

            escApi.register(esc)
        msgLogDao.insert(response.json()["escSensorId"],"ESC", "SAS", "REGIST", json.dumps(payload), "REQ")
        msgLogDao.insert(response.json()["escSensorId"], "SAS", "ESC", "REGIST", json.dumps(response.json()), "RESP")


            # 처리 결과를 JSON으로 반환
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/deregist', renderer='json', request_method='POST')
def deregist(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        sas_url = sysPropDao.prop_get("sas_url")

        response = requests.post(f"{sas_url}/esc_deregist", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)

            # 처리 결과를 JSON으로 반환
        else:
            # dict를 객체처럼 변환
            esc = SimpleNamespace(**payload)

            escApi.deregister(esc)

        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )


@view_config(route_name='api/sensing', renderer='json', request_method='POST')
def sensing(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        sas_url = sysPropDao.prop_get("sas_url")

        response = requests.post(f"{sas_url}/esc_sensing", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)

            # 처리 결과를 JSON으로 반환
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/sensing_report', renderer='json', request_method='POST')
def sensing_report(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        sas_url = sysPropDao.prop_get("sas_url")

        response = requests.post(f"{sas_url}/esc_sensing", json=payload)

        msgLogDao.insert(response.json()["escSensorId"], "ESC", "SAS", "SENSING", payload, "REQ")
        msgLogDao.insert(response.json()["escSensorId"], "SAS", "ESC", "SENSING", json.dumps(response.json()),
                              "RESP")


        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)

            # 처리 결과를 JSON으로 반환
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/incumbent_change', renderer='json', request_method='POST')
def incumbent_change(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body
        sensor_id = payload["escSensorId"]
        lowFreq = payload["sensingResult"][0]["frequencyRange"]["lowFrequency"]
        highFreq = payload["sensingResult"][0]["frequencyRange"]["highFrequency"]
        incumbentUserActivation = payload["sensingResult"][0]["incumbentUserActivation"]
        incumbentUserDetectionTime = payload["sensingResult"][0]["incumbentUserDetectionTime"]

        incumbentUserActivation = 1 if incumbentUserActivation == 'true' else 0
        escApi.esc_ch_update_status(sensor_id, lowFreq, highFreq, incumbentUserActivation)

        return {}
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )



@view_config(route_name='api/release', renderer='json', request_method='POST')
def release(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        sas_url = sysPropDao.prop_get("sas_url")

        response = requests.post(f"{sas_url}/esc_sensing", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)

            # 처리 결과를 JSON으로 반환
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/cbsd_list', renderer='json')
def cbsd_list(request):
    cbsd_list = cbsdApi.cbsd_list()

    json_object = json.dumps(cbsd_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/esc_list', renderer='json')
def esc_list(request):
    esc_list = escApi.sensor_list()

    json_object = json.dumps(esc_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/esc_sensor_delete', renderer='json')
def esc_sensor_delete(request):
    # JSON 데이터를 받아옴
    sensor_id = request.params.get('sensor_id', 0)

    escApi.sensor_sensor_delete(sensor_id)

    json_object = json.dumps({}, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/dpa_list', renderer='json')
def dpa_list(request):
    #dpa_list = cbsdApi.dpa_list()
    #cbsd_list = cbsdApi.cbsd_list()

    #json_object = json.dumps({"dpa_list":dpa_list, "cbsd_list":cbsd_list}, cls=DateTimeEncoder)

    json_object = json.dumps({"dpa_list": [], "cbsd_list": []}, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/esc_ch_list', renderer='json')
def esc_ch_list(request):
    # JSON 데이터를 받아옴
    sensor_id = request.params.get('sensor_id', 0)

    esc_ch_list = escApi.sensor_channel_list(sensor_id)

    json_object = json.dumps(esc_ch_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/grant_list', renderer='json')
def grant_list(request):
    #cbsd_id = request.matchdict.get('cbsd_id')
    cbsd_id = request.params.get('cbsd_id', 0)
    list = cbsdApi.grant_list(cbsd_id)

    json_object = json.dumps(list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/msg_list', renderer='json')
def msg_list(request):
    #cbsd_id = request.matchdict.get('cbsd_id')
    cbsd_id = request.params.get('cbsd_id', 0)
    msg_list = msgLogDao.list_by_deviceid(cbsd_id)

    for item in msg_list:
        if isinstance(item['MSSAGE'], bytes):
            item['MSSAGE'] = item['MSSAGE'].decode('utf-8')

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/sensing_on', renderer='json')
def sensing_on(request):
    payload = request.json_body

    sensor_id = payload["escSensorId"]
    sensing = payload["sensing"]

    if sensing :
        result = heartbeatManager.start_heartbeat(sensor_id, 60)
    else:
        result = heartbeatManager.stop_heartbeat(sensor_id)

    return result  # JSON 응답

@view_config(route_name='api/sensing_check', renderer='json')
def sensing_check(request):
    payload = request.json_body
    sensor_id = payload["escSensorId"]

    result = heartbeatManager.check_exist(sensor_id)

    return result  # JSON 응답

@view_config(route_name='api/save_setting', renderer='json')
def save_setting(request):
    try:
        payload = request.json_body

        sas_url = payload["sas_url"]
        report_path = payload["report_path"]

        result = sysPropDao.prop_update("sas_url", sas_url)
        result = sysPropDao.prop_update("report_path", report_path)
        return {
                        "sas_url": result,
                        "response": {
                            "responseCode": 0,
                            "responseMessage": "SUCCESS"
                        }
                    }  # JSON 응답  # JSON 응답
    except KeyError as e:
        print(f"[ERROR] Missing key in request payload: {e}")
        return {
            "response": {
                "responseCode": 1,
                "responseMessage": f"Missing key in request payload: {str(e)}"
            }
        }
    except Exception as e:
        print(f"[ERROR] Internal server error: {e}")
        return {
            "response": {
                "responseCode": 2,
                "responseMessage": f"Internal server error: {str(e)}"
            }
        }
@view_config(route_name='api/load_setting', renderer='json')
def load_setting(request):
    payload = request.json_body

    result = sysPropDao.prop_get("sas_url")
    report_path = sysPropDao.prop_get("report_path")
    return {
                    "sas_url": result,
                    "report_path":report_path,
                    "response": {
                        "responseCode": 0,
                        "responseMessage": "SUCCESS"
                    }
                }  # JSON 응답

@view_config(route_name='api/sas_status', renderer='json')
def sas_status(request):
    try:
        return {
            "status": "connected",
            "response": {
                "responseCode": 0,
                "responseMessage": "SAS 서버 연결 성공"
            }
        }

        sas_url = sysPropDao.prop_get("sas_url")

        # SAS 서버 연결 확인 로직 (예: HTTP ping 등)
        import requests
        response = requests.get(sas_url + "/health", timeout=2)  # 예시 엔드포인트
        if response.status_code == 200:
            return {
                "status": "connected",
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SAS 서버 연결 성공"
                }
            }
        else:
            return {
                "status": "disconnected",
                "response": {
                    "responseCode": 1,
                    "responseMessage": f"SAS 서버 응답 오류: {response.status_code}"
                }
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "response": {
                "responseCode": 2,
                "responseMessage": f"SAS 서버 연결 실패: {str(e)}"
            }
        }

@view_config(route_name='api/health', renderer='json')
def health(request):
    payload = request.json_body

    sensor_id = payload["escSensorId"]
    monitoring = payload["escSensorMonitoring"]
    try:

        errorResp = None
        perfResp = None
        if monitoring == 0:
            errorResp = getSensorError()
        elif monitoring == 1:
            perfResp = getSensorPerf()
        else:
            errorResp = getSensorError()
            perfResp = getSensorPerf()

        response = {
            "escSensorId": sensor_id,
            "dpaId": "aaaa"
        }

        if errorResp is not None:
            response["escFault"] = errorResp

        if perfResp is not None:
            response["escPerformance"] = perfResp

        return response
    except Exception as e:
        return {
            "status": "disconnected",
            "response": {
                "responseCode": 2,
                "responseMessage": f"SAS 서버 연결 실패: {str(e)}"
            }
        }

def getSensorError():
    hardwareFault = True
    softwareFault = False
    networkFault = False
    securityFault = False

    return {
        "hardwareFault" : hardwareFault,
        "softwareFault": softwareFault,
        "networkFault": networkFault,
        "securityFault": securityFault,
    }

def getSensorPerf():
    powerDetectionThreshold = -89
    detectionProbability = 99
    acceptableNoiseLevel = -109
    monitoringFrequency = {
        "lowFrequency" : 3300000000,
        "highFrequency" : 3400000000
    }

    return {
        "powerDetectionThreshold": powerDetectionThreshold,
        "detectionProbability": detectionProbability,
        "acceptableNoiseLevel": acceptableNoiseLevel,
        "monitoringFrequency": monitoringFrequency,
    }

def heartbeat(cbsdId, grantId):
    payload = {
        "cbsdId": cbsdId,
        "grantId": grantId,
        "grantRenew": False,
        "operationState": "AUTHORIZED",
        "measReport": {
        }
    }

    pretty_req_json = json.dumps(payload, indent=4, ensure_ascii=False)

    #add_log("HEARBEAT", "REQ", "-", pretty_req_json)

    sas_url = sysPropDao.prop_get("sas_url")

    response = requests.post(f"{sas_url}/heartbeat", json=payload)
    pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

    msgLogDao.insert(payload["cbsdId"], "CBSD", "SAS", "HEARTBEAT", json.dumps(payload), "REQ")

    # response check
    responseCode = response.json()["response"]["responseCode"]
    responseMessage = response.json()["response"]["responseMessage"]
    if responseCode != 0:
        if responseCode == 501:  # SUSPENDED_GRANT
            print(responseMessage)
            if response.json()["transmitExpireTime"] != "":
                print('CBSD SUSPENDED')
                msgLogDao.insert(payload["cbsdId"], "CBSD", "CBSD", "SUSPEND", json.dumps(payload), "REQ")
                #asyncio.run( client_manager.send_message_to_clients('{"status":"SUSPENDED_GRANT", "cbsd_id":"'+payload["cbsdId"]+'"}'))


        elif responseCode == 500: # TERMINATED_GRANT
            print(responseMessage)
    else:
        #get_grant_list(cbsdId)
        print(responseMessage)
        # 최초의 hearbeat 인 경우 GRANT 의 상태를 AUTHORIZED 로 바꾼다.
        global periodic_thread
        #if periodic_thread[grantId]["count"] == 0:
        #    cbsdApi

    msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response.json()), "RESP")

    #add_log("HEARBEAT", "RESP", "SUCCESS", pretty_json)
    print(pretty_json)

    return pretty_json

# 커스텀 JSON 인코더 정의
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # datetime을 문자열로 변환
        return super().default(obj)