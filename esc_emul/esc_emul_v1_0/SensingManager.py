import threading
import time

import pytz
import requests
from datetime import datetime, timedelta

from api.CbsdDao import CbsdDao
from api.EscEmulDao import EscEmulDao
from api.MsgLogDao import MsgLogDao
from api.property import SettingsManager


class SensingManager:
    def __init__(self):
        self.heartbeat_threads = {}

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

        self.msgLogDao = MsgLogDao(db_config)
        self.cbsdDao = CbsdDao(db_config)
        self.escEmulDao = EscEmulDao(db_config)

    def start_heartbeat(self, sensor_id, interval):

        if sensor_id in self.heartbeat_threads:
            return {
                "escSensorId": sensor_id,
                "response": {
                    "responseCode": 1,
                    "responseMessage": "ALREADY SENSING ON"
                }
            }

        """주기적으로 heartbeat 메시지를 보내는 스레드 시작."""
        self.heartbeat_threads[sensor_id] = {
            'sensor_id': sensor_id,
            'thread': None,
            'interval': interval,
            'shared_data': {},
            'runcount': 0,
            'running': True,  # 각 스레드의 실행 상태
            'last_heartbeat_success_time' : ''
        }
        thread = threading.Thread(target=self.heartbeat_thread, args=(sensor_id, interval))
        thread.start()
        self.heartbeat_threads[sensor_id]['thread'] = thread

        return {
                "escSensorId": sensor_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    def heartbeat_thread(self, sensor_id, interval):
        """주기적으로 heartbeat 메시지를 보내는 메서드."""
        while self.heartbeat_threads[sensor_id]['running']:

            self.send_heartbeat(sensor_id)

            """
            last_heartbeat_success_time_str = self.heartbeat_threads[grant_id]['last_heartbeat_success_time']
            if last_heartbeat_success_time_str != None and last_heartbeat_success_time_str != "":
                last_heartbeat_success_time = datetime.strptime(last_heartbeat_success_time_str, '%Y-%m-%dT%H:%M:%SZ')

                if current_time >= ( last_heartbeat_success_time + timedelta(days=7) ):
                    # sas 로 부터 heartbeat 의 응답을 7일동안 받지 못하면, SAS 와 연결이 끊겼다고 가정하고, 모든 channel 의 전송을 중지한다.
                    # 모든 heartbeat thread 를 중지하고, grant 를 삭제한다.
                    self.stop_all()
            """
            time.sleep(interval)

        del self.heartbeat_threads[sensor_id]

    def send_heartbeat(self, sensor_id):
        """REST API 호출로 heartbeat 메시지 전송."""
        shared_data = self.heartbeat_threads[sensor_id]['shared_data']
        runcount = self.heartbeat_threads[sensor_id]['runcount']
        print(f"Sending heartbeat from thread {sensor_id}: {shared_data}")

        self.heartbeat_threads[sensor_id]['runcount'] = runcount + 1

        channel_list = self.escEmulDao.sensor_channel_list(sensor_id)
        sensingResult = []
        for channel in channel_list:
            sensingResult.append({
                "frequencyRange": {
                    "lowFrequency": channel["LOW_FREQ"],
                    "highFrequency": channel["HIGH_FREQ"],
                },
                "incumbentUserActivation": True if channel["INCUMBENT_USER"] == 1 else False,
                "incumbentUserDetectionTime": ""
            })

        # 예시 REST API 호출
        try:
            response = requests.post("http://127.0.0.1:8000/esc_sensing", json={
                "escSensorId": sensor_id,
                "dpaId": "dpaId",
                "sensingResult": sensingResult
            }, timeout=5)
            self.receive_message(sensor_id, response.json())
        except requests.exceptions.Timeout as e:
            print(f"Timeout {sensor_id}: {e}")
        except Exception as e:
            print(f"Error sending heartbeat from thread {sensor_id}: {e}")

    def receive_message(self, sensor_id, response):
        """수신한 메시지에 따라 동작 수행."""
        print(f"Thread {sensor_id} received message: {response}")

        responseCode = response["response"]["responseCode"]
        responseMessage = response["response"]["responseMessage"]


            #msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response.json()), "RESP")

        self.heartbeat_threads[sensor_id]['last_heartbeat_success_time'] = datetime.strptime(self.calcTime(0), '%Y-%m-%dT%H:%M:%SZ')

    def update_shared_data(self, thread_id, key, value):
        """특정 스레드의 공유 데이터 업데이트 메서드."""
        if thread_id in self.heartbeat_threads:
            self.heartbeat_threads[thread_id]['shared_data'][key] = value

    def update_interval(self, thread_id, new_interval):
        """스레드의 동작 주기를 동적으로 변경."""
        if thread_id in self.heartbeat_threads:
            self.heartbeat_threads[thread_id]['interval'] = new_interval

    def update_expiration_time(self, thread_id, grant_id):
        """스레드의 만료 시간 업데이트."""
        new_expiration_time = datetime.now() + timedelta(minutes=10)  # 10분으로 업데이트
        self.heartbeat_threads[grant_id]['expiration_time'] = new_expiration_time
        print(f"Thread {thread_id} expiration time updated to {new_expiration_time}")

    def stop_heartbeat(self, sensor_id):
        """특정 스레드 중지."""
        if sensor_id in self.heartbeat_threads:
            self.heartbeat_threads[sensor_id]['running'] = False  # 실행 상태를 False로 변경
            #self.heartbeat_threads[grant_id]['thread'].join()  # 스레드가 종료될 때까지 대기
            #del self.heartbeat_threads[grant_id]  # 스레드 목록에서 제거

        return {
                "escSensorId": sensor_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

    def check_exist(self, sensor_id):
        """특정 스레드 중지."""
        if sensor_id in self.heartbeat_threads:
            running = self.heartbeat_threads[sensor_id]['running']

            return {
                    "escSensorId": sensor_id,
                    "sensing" : "on" if running else "off",
                    "response": {
                        "responseCode": 0,
                        "responseMessage": "SUCCESS"
                    }
                }

        return {
            "escSensorId": sensor_id,
            "sensing": "off",
            "response": {
                "responseCode": 0,
                "responseMessage": "SUCCESS"
            }
        }
    def stop_all(self):
        """모든 스레드 중지."""
        for thread_id in list(self.heartbeat_threads.keys()):
            self.stop_heartbeat(thread_id)
            self.cbsdDao.grant_delete(thread_id)

    def send_grant(self, cbsd_id, lowFreq, highFreq):
        try:
            response = requests.post("http://127.0.0.1:6543/api/grant", json={
                "cbsdId": cbsd_id,
                "operationParam": {
                    "maxEirp": 30,
                    "operationFrequencyRange": { "lowFrequency": lowFreq, "highFrequency": highFreq }
                }
            }, timeout=5)
        except requests.exceptions.Timeout as e:
            print(f"Timeout {cbsd_id}: {e}")
        except Exception as e:
            print(f"Error sending heartbeat from thread {cbsd_id}: {e}")

    def send_relinquishment(self, cbsd_id, grant_id):
        try:
            response = requests.post("http://127.0.0.1:6543/api/relinquishment", json={
                "cbsdId": cbsd_id,
                "grantId": grant_id
            }, timeout=5)
        except requests.exceptions.Timeout as e:
            print(f"Timeout {cbsd_id}: {e}")
        except Exception as e:
            print(f"Error sending heartbeat from thread {cbsd_id}: {e}")

    def calcTime(self, sec):
        # 현재 시간 가져오기
        now = datetime.now()
        # 하루 이후의 시간 계산
        future_time = now + timedelta(seconds=sec)
        # UTC 시간으로 변환
        future_time_utc = future_time.replace(tzinfo=pytz.UTC)

        # YYYY-MM-DDThh:mm:ssZ 형식으로 문자열 변환
        formatted_time = future_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        return formatted_time

# 사용 예시
if __name__ == "__main__":
    manager = SensingManager()

    # 여러 스레드 시작
    expiration_time_1 = datetime.now() + timedelta(minutes=10)  # 초기 만료 시간 설정
    manager.start_heartbeat('thread_1', 'grant_id', 2, expiration_time_1)  # 2초마다 heartbeat 전송

    expiration_time_2 = datetime.now() + timedelta(minutes=10)
    manager.start_heartbeat('thread_2', 'grant_id', 3, expiration_time_2)  # 3초마다 heartbeat 전송

    # 일정 시간 후 모든 스레드 중지
    time.sleep(30)
    manager.stop_all()
    print("All heartbeat threads stopped.")
