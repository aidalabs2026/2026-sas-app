from pyramid.view import view_config
from pyramid.response import Response
import json
from datetime import datetime

from api.EscApi import EscApi
from api.CbsdApi import CbsdApi
import requests
import threading
import time
import asyncio

from aiohttp import web

from api.MsgLogDao import MsgLogDao
from websocket.ClientManager import ClientManager

periodic_thread = {}

client_manager = ClientManager()

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

db_config = {
    'host': '192.168.0.166',
    'user': 'root',
    'password': 'delta5535',
    'database': '2024sas_dev'
}

cbsdApi = CbsdApi(db_config)
escApi = EscApi(db_config)
msgLogDao = MsgLogDao(db_config)

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

        response = requests.post("http://127.0.0.1:8000/esc_regist", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)

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

        response = requests.post("http://127.0.0.1:8000/esc_deregist", json=payload)

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

@view_config(route_name='api/sensing', renderer='json', request_method='POST')
def sensing(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        response = requests.post("http://127.0.0.1:8000/esc_sensing", json=payload)

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

@view_config(route_name='api/release', renderer='json', request_method='POST')
def release(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        response = requests.post("http://127.0.0.1:8000/esc_sensing", json=payload)

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

    response = requests.post("http://127.0.0.1:8000/heartbeat", json=payload)
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
                asyncio.run( client_manager.send_message_to_clients('{"status":"SUSPENDED_GRANT", "cbsd_id":"'+payload["cbsdId"]+'"}'))


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