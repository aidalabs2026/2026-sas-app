import json
import os
import sys
import threading
import time

from EscManager import ESCManager
from api.ApplyApi import ApplyApi
from api.FSPAApi import FSPAApi
from api.SdDao import SdDao

from fastapi import FastAPI, HTTPException, Request

from types import SimpleNamespace

from api.CbsdApi import CbsdApi
from api.EscApi import EscApi
from api.MsgLogDao import MsgLogDao
from mysql.Database import Database
from api.property import SettingsManager
from typing import List, Dict, Any
import pandas as pd
from io import BytesIO

from fastapi import WebSocket, WebSocketDisconnect

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Query
from typing import Optional


""" Main application entry point.

    python -m 2024SAS-APP  ...

"""
import uuid

impact_accur = False

app = FastAPI()

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
connected_clients = set()

escApi = EscApi(db_config)
cbsdApi = CbsdApi(db_config)
applyApi = ApplyApi(db_config, connected_clients)
msgLogDao = MsgLogDao(db_config)

fspaApi = FSPAApi(db_config)

sdDao = SdDao(db_config)


def main():
    """ Execute the application.

    """
    raise NotImplementedError


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print("📨 받은 메시지:", data)
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("🔌 클라이언트 연결 해제")
    except Exception as e:
        connected_clients.remove(websocket)
        print(f"❌ WebSocket 오류 발생: {e}")
        #await websocket.close()  # 예외 발생 시 명시적으로 종료
    #finally:
    #    connected_clients.discard(websocket)  # 항상 정리


async def broadcast_message(message: str):
    for client in connected_clients:
        try:
            print(message)
            await client.send_text(message)
        except Exception as e:
            print("메시지 전송 실패:", e)

esc_mgr = ESCManager(escApi.registed_sensor_list(), escApi)

@app.post("/regist")
async def regist(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()



    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    resp = cbsdApi.register(request_data)

    msgLogDao.insert(resp["cbsdId"], "CBSD", "SAS", "REGIST", json.dumps(request_data), "REQ")
    msgLogDao.insert(resp["cbsdId"], "SAS", "CBSD", "REGIST", json.dumps(resp), "RESP")

    await broadcast_message(json.dumps(resp))

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return resp


@app.post("/deregist")
async def deregist(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()

    msgLogDao.insert(request_data["cbsdId"], "CBSD", "SAS", "DEREGIST", json.dumps(request_data), "REQ")
    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    cbsd_id = request_data["cbsdId"]
    resp = cbsdApi.deregister(cbsd_id)
    msgLogDao.insert(resp["cbsdId"], "SAS", "CBSD", "DEREGIST", json.dumps(resp), "RESP")
    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환

    await broadcast_message(json.dumps(resp))

    return resp

@app.post("/spectrumInquery")
async def spectrumInquery(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()

    msgLogDao.insert(request_data["cbsdId"], "CBSD", "SAS", "SPECTRUM_INQUERY", json.dumps(request_data), "REQ")

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    resp = cbsdApi.spectrumInqueryBySD(request_data)

    msgLogDao.insert(request_data["cbsdId"], "SAS", "CBSD", "SPECTRUM_INQUERY", json.dumps(resp), "RESP")
    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환

    await broadcast_message(json.dumps(resp))

    return resp


@app.post("/grant")
async def grant(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()
    msgLogDao.insert(request_data["cbsdId"], "CBSD", "SAS", "GRANT", json.dumps(request_data), "REQ")

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    resp = cbsdApi.grant(request_data)

    msgLogDao.insert(request_data["cbsdId"], "SAS", "CBSD", "GRANT", json.dumps(resp), "RESP")

    await broadcast_message(json.dumps(resp))
    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return resp

@app.post("/relinquishment")
async def relinquishment(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()
    msgLogDao.insert(request_data["cbsdId"], "CBSD", "SAS", "RELINQUISHMENT", json.dumps(request_data), "REQ")

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    resp = cbsdApi.relinquishment(request_data)

    msgLogDao.insert(request_data["cbsdId"], "SAS", "CBSD", "RELINQUISHMENT", json.dumps(resp), "RESP")

    await broadcast_message(json.dumps(resp))
    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return resp

@app.post("/heartbeat")
async def heartbeat(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()
    msgLogDao.insert(request_data["cbsdId"], "CBSD", "SAS", "HEARTBEAT", json.dumps(request_data, cls=DateTimeEncoder), "REQ")

    # 가져온 JSON 데이터 출력
    #print("Received JSON data:", request_data)

    broadcast_message_flag = { "is_send" : False}
    resp = cbsdApi.heartbeat(request_data, broadcast_message_flag)

    if broadcast_message_flag["is_send"] :
        await broadcast_message(json.dumps(resp))
    msgLogDao.insert(request_data["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(resp, cls=DateTimeEncoder), "RESP")

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return resp



@app.post("/esc_regist")
async def esc_regist(request: Request):
    client_ip = request.client.host  # 클라이언트 IP 가져오기
    print(f"[INFO] Client IP: {client_ip}")

    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()

    msgLogDao.insert(request_data["escSensorId"], "ESC", "SAS", "REGIST", json.dumps(request_data, cls=DateTimeEncoder), "REQ")

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    request_data = SimpleNamespace(**request_data)

    request_data.client_ip = client_ip

    response = escApi.register(request_data)

    msgLogDao.insert(response["escSensorId"], "SAS", "ESC", "REGIST", json.dumps(response, cls=DateTimeEncoder), "RESP")

    await broadcast_message(json.dumps(response))

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return response

@app.post("/esc_sensing")
async def esc_sensing(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리

    client_ip = request.client.host  # 클라이언트 IP 가져오기
    print(f"[INFO] Client IP: {client_ip}")

    request_data = await request.json()

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    incumbentUserActivation = request_data["sensingResult"][0]["incumbentUserActivation"]

    sensing_type = "SENSING_RESULT_REPORT" if incumbentUserActivation else "SENSING_RESULT_REPORT"

    msgLogDao.insert(request_data["escSensorId"], "ESC", "SAS", sensing_type, json.dumps(request_data, cls=DateTimeEncoder), "REQ")


    request_data2 = SimpleNamespace(**request_data)

    esc_sensor_id = request_data2.escSensorId
    dpa_id = request_data2.dpaId
    lowFrequency = request_data2.sensingResult[0]["frequencyRange"]["lowFrequency"]
    highFrequency = request_data2.sensingResult[0]["frequencyRange"]["highFrequency"]
    incumbentUserActivation = request_data2.sensingResult[0]["incumbentUserActivation"]

    response = escApi.sensing_result_report(request_data2, request_data)

    esc_mgr.update_esc(esc_sensor_id, response["sensingResultTxInterval"], client_ip)

    msgLogDao.insert(response["escSensorId"], "SAS", "ESC", sensing_type, json.dumps(response, cls=DateTimeEncoder), "RESP")

    await broadcast_message(json.dumps(request_data))

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return response

@app.post("/esc_deregist")
async def esc_deregist(request: Request):
    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()

    msgLogDao.insert(request_data["escSensorId"], "ESC", "SAS", "DEREGIST", json.dumps(request_data), "REQ")

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    request_data = SimpleNamespace(**request_data)

    response = escApi.deregister(request_data)

    msgLogDao.insert(response["escSensorId"], "SAS", "ESC", "DEREGIST", json.dumps(response), "RESP")

    await broadcast_message(json.dumps(response))

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return response

@app.post("/api/application")
async def application_create(request: Request):
    client_ip = request.client.host  # 클라이언트 IP 가져오기
    print(f"[INFO] Client IP: {client_ip}")

    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()

    response = applyApi.create(request_data)

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data)

    await broadcast_message(json.dumps(response))

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return response

@app.get("/api/application")
async def get_all_applications(
    start_date: Optional[str] = Query(None, description="조회 시작일"),
    end_date: Optional[str] = Query(None, description="조회 종료일")
):
    result = applyApi.get_applications(start_date=start_date, end_date=end_date)

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", start_date, end_date)

    #applications_json_string = json.dumps(result, ensure_ascii=False, indent=4)

    #python_object = json.loads(applications_json_string)

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return result

@app.get("/api/application/{apply_id}")
async def application_search_by_id(apply_id: int):

    result = applyApi.get_applications(apply_id=apply_id)

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", apply_id)

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return result

@app.put("/api/application/{apply_id}")
async def application_update(apply_id: int, request: Request):
    client_ip = request.client.host  # 클라이언트 IP 가져오기
    print(f"[INFO] Client IP: {client_ip}")

    # 요청의 body에서 JSON 데이터를 가져와서 처리
    request_data = await request.json()

    response = applyApi.update(request_data, apply_id)

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", request_data, apply_id)

    await broadcast_message(json.dumps(response))

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return response

@app.delete("/api/application/{apply_id}")
async def application_update(apply_id: int):

    applyApi.delete(apply_id)

    # 가져온 JSON 데이터 출력
    print("Received JSON data:", apply_id)

    # 요청으로부터 받은 JSON 데이터와 파라미터로 받은 item을 모두 반환
    return True

# --- 엑셀 파일을 입력받는 새로운 API 엔드포인트 ---
@app.post("/process_mfsd_sf_excel")
async def process_mfsd_sf_excel(file: UploadFile = File(...)):
    """
    MFSD_ID와 FCC_ID를 포함하는 엑셀 파일을 입력받아 각 행의 데이터를 처리합니다.
    """

    # 파일 확장자 확인
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ('.xlsx', '.xls', '.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .xlsx, .xls, or .csv file.")

    responses: List[Dict[str, Any]] = []

    try:
        # 엑셀 파일 읽기
        # 파일 형식에 따라 데이터프레임 읽기
        file_content = BytesIO(await file.read())
        if file_extension in ('.xlsx', '.xls'):
            df = pd.read_excel(file_content)
        elif file_extension == '.csv':
            # csv 파일의 경우 인코딩을 명시할 수 있습니다. (예: 'utf-8')
            df = pd.read_csv(file_content, encoding='utf-8')

        # 필수 컬럼(MFSD_ID, FCC_ID)이 엑셀 파일에 있는지 확인
        required_columns = ['MFSD_ID', 'FCC_ID']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in the Excel file. Must include: {', '.join(required_columns)}"
            )

        # 데이터프레임의 각 행을 순회하며 처리
        for index, row in df.iterrows():

            if index == 0:
                result = sdDao.sf_exists(row['SF_ID'])

                if result == True:
                    sdDao.sf_delete(row['SF_ID'])

            sdDao.sf_insert(row, row['SF_ID'])

        sdDao.merge_sd()

    except HTTPException as e:
        # 필수 컬럼 누락 등 400 에러는 여기서 다시 발생시킴
        raise e
    except Exception as e:
        # 그 외 파일 처리 중 오류 발생 시
        print(f"An error occurred while processing the file: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {e}")

        # 모든 처리 결과를 리스트로 반환
    return {"status": "success", "processed_count": len(responses), "results": responses}


@app.post("/process_mfsd_sn_excel")
async def process_mfsd_sn_excel(file: UploadFile = File(...)):
    """
    MFSD_ID와 FCC_ID를 포함하는 엑셀 파일을 입력받아 각 행의 데이터를 처리합니다.
    """

    # 파일 확장자 확인
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ('.xlsx', '.xls', '.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .xlsx, .xls, or .csv file.")

    responses: List[Dict[str, Any]] = []

    try:
        # 엑셀 파일 읽기
        # 파일 형식에 따라 데이터프레임 읽기
        file_content = BytesIO(await file.read())
        if file_extension in ('.xlsx', '.xls'):
            df = pd.read_excel(file_content)
        elif file_extension == '.csv':
            # csv 파일의 경우 인코딩을 명시할 수 있습니다. (예: 'utf-8')
            df = pd.read_csv(file_content, encoding='utf-8')

        # 필수 컬럼(MFSD_ID, FCC_ID)이 엑셀 파일에 있는지 확인
        required_columns = ['MFSD_ID', 'FCC_ID']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in the Excel file. Must include: {', '.join(required_columns)}"
            )

        # 데이터프레임의 각 행을 순회하며 처리
        for index, row in df.iterrows():

            if index == 0:
                result = sdDao.sn_exists(row['SN_ID'])

                if result == True:
                    sdDao.sn_delete(row['SN_ID'])

            sdDao.sn_insert(row, row['SN_ID'])

        sdDao.merge_sd()

    except HTTPException as e:
        # 필수 컬럼 누락 등 400 에러는 여기서 다시 발생시킴
        raise e
    except Exception as e:
        # 그 외 파일 처리 중 오류 발생 시
        print(f"An error occurred while processing the file: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {e}")

        # 모든 처리 결과를 리스트로 반환
    return {"status": "success", "processed_count": len(responses), "results": responses}

@app.post("/process_mfsd_se_excel")
async def process_mfsd_se_excel(file: UploadFile = File(...)):
    """
    MFSD_ID와 FCC_ID를 포함하는 엑셀 파일을 입력받아 각 행의 데이터를 처리합니다.
    """

    # 파일 확장자 확인
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ('.xlsx', '.xls', '.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .xlsx, .xls, or .csv file.")

    responses: List[Dict[str, Any]] = []

    try:
        # 엑셀 파일 읽기
        # 파일 형식에 따라 데이터프레임 읽기
        file_content = BytesIO(await file.read())
        if file_extension in ('.xlsx', '.xls'):
            df = pd.read_excel(file_content)
        elif file_extension == '.csv':
            # csv 파일의 경우 인코딩을 명시할 수 있습니다. (예: 'utf-8')
            df = pd.read_csv(file_content, encoding='utf-8')

        # 필수 컬럼(MFSD_ID, FCC_ID)이 엑셀 파일에 있는지 확인
        required_columns = ['MFSD_ID', 'FCC_ID']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in the Excel file. Must include: {', '.join(required_columns)}"
            )

        # 데이터프레임의 각 행을 순회하며 처리
        for index, row in df.iterrows():

            if index == 0:
                result = sdDao.se_exists(row['SE_ID'])

                if result == True:
                    sdDao.se_delete(row['SE_ID'])

            sdDao.se_insert(row, row['SE_ID'])
        sdDao.merge_sd()

    except HTTPException as e:
        # 필수 컬럼 누락 등 400 에러는 여기서 다시 발생시킴
        raise e
    except Exception as e:
        # 그 외 파일 처리 중 오류 발생 시
        print(f"An error occurred while processing the file: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {e}")

        # 모든 처리 결과를 리스트로 반환
    return {"status": "success", "processed_count": len(responses), "results": responses}

@app.get("/health")
async def health(request: Request):
    print("get health")
    return ""

@app.post("/health")
async def health(request: Request):
    print("post health")
    return ""


from datetime import datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # datetime을 문자열로 변환
        return super().default(obj)

# Make the script executable.

def check_cbsd_th():
    """1시간 간격으로 1일 이상 Heartbeat 없는 Grant를 정리한다."""
    while True:
        try:
            grantlist = cbsdApi.check_last_grant_time(1)
            for grant in grantlist:
                cbsdApi.grant_delete(grant["GRANT_ID"])
                msgLogDao.insert(grant["GRANT_ID"], "SAS", "SAS", "GRANT_DELETE",
                                 json.dumps({"reason": "Delete the grant if there is no heartbeat for one day."}), "RESP")
            if grantlist:
                print(f"[check_cbsd_th] Cleaned up {len(grantlist)} expired grants")
        except Exception as e:
            print(f"[check_cbsd_th] Error: {e}")
        time.sleep(3600)

if __name__ == "__main__":
    try:
        fspaApi.spa_update()
        thread1 = threading.Thread(target=check_cbsd_th, daemon=True)
        thread1.start()
        os.chdir(sys._MEIPASS)
        print(sys._MEIPASS)
    except:
        os.chdir(os.getcwd())

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    raise SystemExit(main())

#실행파일 제작
#.\venv\Scripts\pyinstaller --noconfirm --onefile --console --name "sas_core" "C:\pythonProject\2024-sas-app\__main__.py"

#.\venv\Scripts\pip freeze > requirements.txt
#.\venv\Scripts\pip install -r requirements.txt
