import sys

from cbsd_emul_v1_0.HeartbeatManager import HeartbeatManager
from cbsd_emul_v1_0.views.CbsdEmulDao import CbsdEmulDao

sys.path.append('.')
from pyramid.view import view_config
from pyramid.response import Response
import json
from datetime import datetime

from api.CbsdApi import CbsdApi
from api.EscApi import EscApi
import requests
import threading
import time
import asyncio
import socket

from aiohttp import web

from api.MsgLogDao import MsgLogDao
from api.property import SettingsManager
#from cbsd_emul.v3_0 import ClientManager


periodic_thread = {}

#client_manager = ClientManager()
heartbeatManager = HeartbeatManager()
heartbeatManager.restore_heartbeats()

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
settings_manager = SettingsManager(config_file_path)
settings_manager.load_settings()

db_config = {
    'host': settings_manager.get_setting("host"),
    'user': settings_manager.get_setting("user"),
    'password': settings_manager.get_setting("password"),
    'database': settings_manager.get_setting("database"),
}

cbsdApi = CbsdApi(db_config)
escApi = EscApi(db_config)
msgLogDao = MsgLogDao(db_config)

cbsdEmulDao = CbsdEmulDao(db_config)

@view_config(route_name='index', renderer='../templates/base3.jinja2')
def index_view(request):
    # 서버 IP 주소 가져오기
    return {"table_data": table_data, "default_data": default_data}

@view_config(route_name='msglog', renderer='../templates/msgSequence.jinja2')
def msglog_view(request):
    device_id = request.matchdict.get('device_id')
    sub_id = request.matchdict.get('sub_id')

    cbsd_id = f"{device_id}/{sub_id}"

    msg_list = msgLogDao.list_by_deviceid(cbsd_id)

    for item in msg_list:
        if isinstance(item['MSSAGE'], bytes):
            item['MSSAGE'] = item['MSSAGE'].decode('utf-8')
            item['MSSAGE'] = item['MSSAGE'].replace('"', "'")

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return {"device_id": f"{device_id}/{sub_id}", "data" : json_object}

@view_config(route_name='msglogview', renderer='../templates/msgSequenceView.jinja2')
def msglogview_view(request):
    device_id = request.matchdict.get('device_id')
    sub_id = request.matchdict.get('sub_id')

    cbsd_id = f"{device_id}/{sub_id}"

    msg_list = msgLogDao.list_by_deviceid(cbsd_id)

    for item in msg_list:
        if isinstance(item['MSSAGE'], bytes):
            item['MSSAGE'] = item['MSSAGE'].decode('utf-8')
            item['MSSAGE'] = item['MSSAGE'].replace('"', "'")

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return {"device_id": f"{device_id}/{sub_id}", "data" : json_object}

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

        print( "sasurl : ",  settings_manager.get_setting('sasurl') )

        response = requests.post(f"{settings_manager.get_setting('sasurl')}regist", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        responseObj = response.json()

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)
                return Response(
                    status=responseCode,
                    json_body={'status': 'error', 'message': responseMessage}
                )
        cbsd_id = responseObj["cbsdId"]
        cbsd = payload

        if cbsdEmulDao.cbsd_exists(cbsd_id):
            cbsdEmulDao.cbsd_update_status(cbsd_id, "REGIST")
        else:
            cbsdEmulDao.cbsd_insert(cbsd, cbsd_id)

        #msgLogDao.insert(response.json()["cbsdId"],"CBSD", "SAS", "REGIST", json.dumps(payload), "REQ")
        #msgLogDao.insert(response.json()["cbsdId"], "SAS", "CBSD", "REGIST", json.dumps(response.json()), "RESP")
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

        response = requests.post(f"{settings_manager.get_setting('sasurl')}deregist", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200: # REG_PENDING
                print(responseMessage)


        responseObj = response.json()
        # 1. grant 삭제
        cbsd_id = responseObj["cbsdId"]

        cbsdEmulDao.grant_delete_by_cbsdid(cbsd_id)

        # 2. cbsd 삭제
        cbsdEmulDao.cbsd_delete(cbsd_id)

        # 처리 결과를 JSON으로 반환
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/grant_summary', renderer='json')
def grant_summary(request):
    result = cbsdEmulDao.grant_list_active()
    return json.dumps(result, cls=DateTimeEncoder)

@view_config(route_name='api/cbsd_list', renderer='json')
def cbsd_list(request):

    cbsd_list = cbsdEmulDao.cbsd_list()

    json_object = json.dumps(cbsd_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/dpa_list', renderer='json')
def dpa_list(request):
    dpa_list = cbsdApi.dpa_list()
    esc_list = escApi.sensor_list()

    json_object = json.dumps({"dpa_list":dpa_list, "esc_list":esc_list}, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/grant_list', renderer='json')
def grant_list(request):
    #cbsd_id = request.matchdict.get('cbsd_id')
    cbsd_id = request.params.get('cbsd_id', 0)
    list = cbsdEmulDao.grant_list(cbsd_id)

    json_object = json.dumps(list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/grant', renderer='json', request_method='POST')
def grant(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        response = requests.post(f"{settings_manager.get_setting('sasurl')}grant", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 401: # GRANT_CONFLICT
                print(responseMessage)

        else:
            # Create a PeriodicThread that runs every 5 seconds
            cbsdId = payload["cbsdId"]
            grantId = response.json()["grantId"]
            heartbeatInterval = response.json()["heartbeatInterval"]
            grantExpireTime = response.json()["grantExpireTime"]
            heartbeatManager.start_heartbeat(cbsdId, grantId, heartbeatInterval, grantExpireTime)

            # 3. grant 정보 데이터베이스에 등록
            if not cbsdEmulDao.grant_exists(grantId) and responseCode == 0:
                cbsdEmulDao.grant_insert(response.json(), grantId, cbsdId)

            """
            global periodic_thread
            periodic_thread_inst = PeriodicThread(interval=response.json()["hearbeatDuration"], target=heartbeat, cbsdId=payload["cbsdId"],
                                             grantId=response.json()["grantId"])

            periodic_thread[response.json()["grantId"]] = {
                "grant_id" : response.json()["grantId"],
                "inst":periodic_thread_inst,
                "count": 0,
            }

            # Start the thread
            periodic_thread_inst.start()

            # 필요한 데이터 처리 (예: 데이터베이스에 저장)
            #user_id = json_data.get('userId')
            #user_name = json_data.get('userName')
            #user_email = json_data.get('userEmail')
            """

            # 처리 결과를 JSON으로 반환
        #msgLogDao.insert(response.json()["cbsdId"], "CBSD", "SAS", "GRANT", json.dumps(payload), "REQ")
        #msgLogDao.insert(response.json()["cbsdId"], "SAS", "CBSD", "GRANT", json.dumps(response.json()), "RESP")
        return response.json()
    except Exception as e:
        print(str(e))
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/relinquishment', renderer='json', request_method='POST')
def relinquishment(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        response = requests.post(f"{settings_manager.get_setting('sasurl')}relinquishment", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        #msgLogDao.insert(payload["cbsdId"], "CBSD", "SAS", "RELINQUISHMENT", json.dumps(payload), "REQ")
        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 401: # GRANT_CONFLICT
                print(responseMessage)

        else:
            # Create a PeriodicThread that runs every 5 seconds
            grant_id = payload["grantId"]
            heartbeatManager.stop_heartbeat(grant_id)
            if cbsdEmulDao.grant_exists(grant_id):
                cbsdEmulDao.grant_delete(grant_id)

            # 처리 결과를 JSON으로 반환
        msgLogDao.insert(payload["cbsdId"], "CBSD", "CBSD", "DROP SUB DEVICE", json.dumps(response.json()), "RESP")

        #msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "RELINQUISHMENT", json.dumps(response.json()), "RESP")
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/spectrumInquery', renderer='json', request_method='POST')
def spectrumInquery(request):
    try:
        # JSON 데이터를 받아옴
        payload = request.json_body

        response = requests.post(f"{settings_manager.get_setting('sasurl')}spectrumInquery", json=payload)

        pretty_json = json.dumps(response.json(), indent=4, ensure_ascii=False)

        #add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 401: # GRANT_CONFLICT
                print(responseMessage)

            # 처리 결과를 JSON으로 반환
        return response.json()
    except Exception as e:
        return Response(
            status=400,
            json_body={'status': 'error', 'message': str(e)}
        )

@view_config(route_name='api/msg_list', renderer='json')
def msg_list(request):
    cbsd_id = request.params.get('cbsd_id', 0)
    limit = int(request.params.get('limit', 20))
    light = request.params.get('light', '0') == '1'

    msg_list = msgLogDao.list_by_deviceid(cbsd_id, limit=limit, light=light)

    if msg_list and not light:
        for item in msg_list:
            if isinstance(item.get('MSSAGE'), bytes):
                item['MSSAGE'] = item['MSSAGE'].decode('utf-8')

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/msg_detail', renderer='json')
def msg_detail(request):
    msg_id = request.params.get('id', 0)
    msg = msgLogDao.get_message_by_id(msg_id)

    if msg and isinstance(msg.get('MSSAGE'), bytes):
        msg['MSSAGE'] = msg['MSSAGE'].decode('utf-8')

    return json.dumps(msg, cls=DateTimeEncoder)

def heartbeat(cbsdId, grantId):
    payload = {
        "cbsdId": cbsdId,
        "grantId": grantId,
        "grantRenew": False,
        "operationState": "AUTHORIZED", # or GRANTED
        "measReport": {
        }
    }

    pretty_req_json = json.dumps(payload, indent=4, ensure_ascii=False)

    #add_log("HEARBEAT", "REQ", "-", pretty_req_json)

    response = requests.post(f"{settings_manager.get_setting('sasurl')}heartbeat", json=payload)
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
                msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response.json()), "RESP")
                msgLogDao.insert(payload["cbsdId"], "CBSD", "CBSD", "SUSPEND", json.dumps(payload), "REQ")
                #asyncio.run( client_manager.send_message_to_clients('{"status":"SUSPENDED_GRANT", "cbsd_id":"'+payload["cbsdId"]+'"}'))


        elif responseCode == 500: # TERMINATED_GRANT
            print(responseMessage)
            msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response.json()), "RESP")
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

@view_config(route_name='api/prop_load', renderer='json')
def prop_load(request):
    prop_list = cbsdApi.prop_load()
    props = []
    for item in prop_list:
        props.append({item["SKEY"] : item["VALUE"]})

    json_object = json.dumps(prop_list, cls=DateTimeEncoder)

    return json_object  # JSON 응답

@view_config(route_name='api/prop_update', renderer='json')
def prop_update(request):
    payload = request.json_body
    skey = payload['SKEY']
    value = payload['VALUE']

    cbsdApi.prop_update(skey, value)
    return {}  # JSON 응답

@view_config(route_name='api/get_msg_list_part', renderer='json')
def get_msg_list_part(request):
    startIdx = request.params.get('startIdx', 0)
    direction = request.params.get('direction', "UP")
    length = request.params.get('length', 100)

    msg_list = msgLogDao.list_by_part(startIdx, direction, length)

    for item in msg_list:
        if isinstance(item['MSSAGE'], bytes):
            item['MSSAGE'] = item['MSSAGE'].decode('utf-8')
            item['MSSAGE'] = item['MSSAGE'].replace('"', "'")

    json_object = json.dumps(msg_list, cls=DateTimeEncoder)

    return {"startIdx":startIdx, "direction":direction, "length":length, "data" : json_object}

# 커스텀 JSON 인코더 정의
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # datetime을 문자열로 변환
        elif isinstance(obj, bytes):
            return obj.decode('utf-8')  # bytes를 문자열로 변환
        return super().default(obj)