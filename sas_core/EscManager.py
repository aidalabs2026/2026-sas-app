import threading
import time
from datetime import datetime, timedelta
import requests
from types import SimpleNamespace

class ESC:
    def __init__(self, esc_id, last_report_time, report_interval, ip_addr):
        self.esc_id = esc_id
        self.ip_addr = ip_addr
        self.report_interval = report_interval
        self.last_report_time = last_report_time
        self.lock = threading.Lock()

    def update_report_time(self):
        with self.lock:
            self.last_report_time = datetime.now()

    def get_last_report_time(self):
        with self.lock:
            return self.last_report_time

    def get_report_interval(self):
        return self.report_interval


class ESCManager:
    def __init__(self, registed_esc_list, escApi):
        self.esc_dict = {}  # {esc_id: ESC}
        self.lock = threading.Lock()
        self.running = True
        self.escApi = escApi
        #self.broadcast_message = broadcast_message_fn

        # 초기 등록된 ESC 리스트를 추가
        for esc_info in registed_esc_list:
            self.add_esc(esc_info["SENSOR_ID"], esc_info["LAST_REPORT_DT"], esc_info["REPORT_INTERVAL"], esc_info["IP_ADDR"])

        # 단일 ESC 모니터링 스레드 시작
        self.monitor_thread = threading.Thread(target=self.monitor_all_escs, daemon=True)
        self.monitor_thread.start()

    async def notify_clients(self, msg):
        await self.broadcast_message(msg)  # async로 호출 가능

    def add_esc(self, esc_id, last_report_dt, report_interval, ip_addr):
        with self.lock:
            if esc_id not in self.esc_dict:
                self.esc_dict[esc_id] = ESC(esc_id, last_report_dt, report_interval, ip_addr)
                print(f"[INFO] ESC {esc_id} 등록")

    def update_esc(self, esc_id, report_interval, client_ip):
        with self.lock:
            if esc_id in self.esc_dict:
                self.esc_dict[esc_id].report_interval = report_interval
                self.esc_dict[esc_id].last_report_time = datetime.now()
                self.esc_dict[esc_id].client_ip = client_ip
                print(f"[INFO] ESC {esc_id} 등록")

    def remove_esc(self, esc_id):
        with self.lock:
            if esc_id in self.esc_dict:
                del self.esc_dict[esc_id]
                print(f"[INFO] ESC {esc_id} 해지 및 제거")

    def request_report(self, esc_id):
        """ESC 상태 보고가 지연된 경우, 상태 확인 요청을 보냄."""

        #print(f"[WARN] ESC '{esc_id}'의 상태 보고가 지연되었습니다. 상태 보고를 요청합니다.")

        esc_info = self.esc_dict[esc_id]
        if not esc_info:
            print(f"[ERROR] '{esc_id}'에 대한 정보를 esc_dict에서 찾을 수 없습니다.")
            return

        ip_addr = esc_info.ip_addr
        if not ip_addr:
            print(f"[ERROR] '{esc_id}'의 IP 주소가 없습니다.")
            return

        esc_url = f"http://{ip_addr}:6544/api/health"

        try:
            escSensorMonitoring = 2
            payload = {
                "escSensorId": esc_id,
                "escSensorMonitoring" : escSensorMonitoring
            }
            #response = requests.get(esc_url, timeout=2)
            response = requests.post(esc_url, json=payload, timeout=2)
            print(response.json())
            respobj = response.json()
            if "escFault" in respobj:
                print("✅ escFault 있음:", respobj["escFault"])
                if (respobj["escFault"]["hardwareFault"] == True or
                    respobj["escFault"]["softwareFault"] == True or
                    respobj["escFault"]["networkFault"] == True or
                    respobj["escFault"]["securityFault"] == True):
                    print( "escFault 에서 에러 발생")

                    self.processEscFault(esc_id, respobj["dpaId"], ip_addr)
            else:
                print("⚠️ escFault 없음")

            if "escPerformance" in respobj:
                print("✅ escPerformance 있음:", respobj["escPerformance"])

            else:
                print("⚠️ escPerformance 없음")

        except requests.exceptions.Timeout:
            #print(f"[ERROR] ESC '{esc_id}' 상태 요청 타임아웃 발생.")
            print()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] ESC '{esc_id}' 상태 요청 실패: {e}")

    def processEscFault(self, esc_id, dpa_id, esc_ip):
        from datetime import datetime, timezone

        current_date = datetime.now(timezone.utc)
        iso_string_without_millis = current_date.isoformat().split('.')[0] + 'Z'
        print(iso_string_without_millis)

        payload = {
          "escSensorId": esc_id,
          "dpaId": dpa_id,
          "sensingResult": [
            {
              "frequencyRange": {
                "lowFrequency": "3300000000",
                "highFrequency": "3310000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3390000000",
                "highFrequency": "3400000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3310000000",
                "highFrequency": "3320000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3320000000",
                "highFrequency": "3330000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3330000000",
                "highFrequency": "3340000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3340000000",
                "highFrequency": "3350000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3350000000",
                "highFrequency": "3360000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3360000000",
                "highFrequency": "3370000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3370000000",
                "highFrequency": "3380000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            },
            {
              "frequencyRange": {
                "lowFrequency": "3380000000",
                "highFrequency": "3390000000"
              },
              "incumbentUserActivation": True,
              "incumbentUserDetectionTime": iso_string_without_millis
            }
          ]
        }
        sensing_type = "SENSING_RESULT_REPORT"

        #msgLogDao.insert(request_data["escSensorId"], "ESC", "SAS", sensing_type,
        #                 json.dumps(request_data, cls=DateTimeEncoder), "REQ")

        request_data2 = SimpleNamespace(**payload)

        esc_sensor_id = request_data2.escSensorId
        dpa_id = request_data2.dpaId
        lowFrequency = request_data2.sensingResult[0]["frequencyRange"]["lowFrequency"]
        highFrequency = request_data2.sensingResult[0]["frequencyRange"]["highFrequency"]
        incumbentUserActivation = request_data2.sensingResult[0]["incumbentUserActivation"]

        response = self.escApi.sensing_result_report(request_data2, payload)

        self.update_esc(esc_sensor_id, response["sensingResultTxInterval"], esc_ip)

        #self.notify_clients(payload)

        #msgLogDao.insert(response["escSensorId"], "SAS", "ESC", sensing_type, json.dumps(response, cls=DateTimeEncoder),
        #                 "RESP")
        """
        response = requests.post(f"http://127.0.0.1:8000/esc_sensing", json=payload)

        # add_log("GRANT", "RESP", "SUCCESS", pretty_json)

        # response check
        responseCode = response.json()["response"]["responseCode"]
        responseMessage = response.json()["response"]["responseMessage"]
        if responseCode != 0:
            if responseCode == 200:  # REG_PENDING
                print(responseMessage)
        """
    def monitor_all_escs(self):
        while self.running:
            with self.lock:
                now = datetime.now()
                for esc_id, esc in list(self.esc_dict.items()):
                    last_report = esc.get_last_report_time()
                    interval = esc.get_report_interval()
                    if last_report is None:
                        self.request_report(esc_id)
                    else:
                        # interval이 정수인 경우 timedelta로 변환
                        if isinstance(interval, (int, float)):
                            interval = timedelta(seconds=interval)

                        if now - last_report > interval:
                            self.request_report(esc_id)
            time.sleep(1)  # 주기적으로 전체 ESC를 체크

    def stop(self):
        self.running = False
        self.monitor_thread.join()
        print("[INFO] ESCManager 종료")

# === 테스트 코드 ===
if __name__ == "__main__":
    esc_mgr = ESCManager()
    esc_mgr.add_esc("ESC001", 10)
    esc_mgr.add_esc("ESC002", 5)

    try:
        while True:
            time.sleep(3)
            esc_mgr.esc_dict["ESC001"].update_report_time()
            print("[DEBUG] ESC001 보고 갱신")

    except KeyboardInterrupt:
        esc_mgr.stop()
