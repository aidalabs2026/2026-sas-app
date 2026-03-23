import threading
import time

import pytz
import requests
from datetime import datetime, timedelta

from api.CbsdDao import CbsdDao
from api.MsgLogDao import MsgLogDao
from api.property import SettingsManager
from cbsd_emul_v1_0.views.CbsdEmulDao import CbsdEmulDao

class HeartbeatManager:
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
        self.cbsdEmulDao = CbsdEmulDao(db_config)

        config_file_path = 'config.json'

        # 설정 매니저 인스턴스 생성
        self.settings_manager = SettingsManager(config_file_path)
        self.settings_manager.load_settings()

    def start_heartbeat(self, thread_id, grant_id, interval, expiration_time):
        print(expiration_time)
        """주기적으로 heartbeat 메시지를 보내는 스레드 시작."""
        expiration_time_t= datetime.strptime(expiration_time, '%Y-%m-%dT%H:%M:%SZ')
        self.heartbeat_threads[grant_id] = {
            'cbsd_id': thread_id,
            'grant_id': grant_id,
            'thread': None,
            'interval': interval,
            'shared_data': {},
            'runcount': 0,
            'running': True,  # 각 스레드의 실행 상태
            'expiration_time': expiration_time_t,  # 만료 시간
            'last_heartbeat_success_time' : ''
        }
        thread = threading.Thread(target=self.heartbeat_thread, args=(thread_id, grant_id, interval))
        thread.start()
        self.heartbeat_threads[grant_id]['thread'] = thread

    def heartbeat_thread(self, thread_id, grant_id, interval):
        """주기적으로 heartbeat 메시지를 보내는 메서드."""
        while self.heartbeat_threads[grant_id]['running']:
            expiration_time = self.heartbeat_threads[grant_id]['expiration_time']

            current_time = datetime.now()
            print(f"{current_time} - {expiration_time}")
            if current_time >= expiration_time - timedelta(minutes=5):
                # grantExpireTime 5분 전이다. grantRenew 를 진행한다.
                self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "GRANT EXPIRE IMMINENT",
                                      f"{{'message':'grantExpiredTime 만료 5분전이다.', 'grantExpireTime':'{expiration_time}', 'currentTime':'{current_time}'}}",
                                      "REQ")
                self.send_heartbeat(thread_id, grant_id, True)

                #self.update_expiration_time(thread_id)  # 만료시간 업데이트

            elif current_time >= expiration_time - timedelta(seconds=5):
                # grantExpireTime 5초 전이다. 60초 까지 사용중이던 채널의 전송을 중지한다.
                # 전송 중지 후 thread를 중지한다.
                self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "GRANT EXPIRED",
                                      f"{{'message':'grantExpiredTime 만료 되었다.', 'grantExpireTime':'{expiration_time}', 'currentTime':'{current_time}'}}"
                                      "REQ")
                self.heartbeat_threads[grant_id]['running'] = False
                break
            else:
                self.send_heartbeat(thread_id, grant_id)

            """
            last_heartbeat_success_time_str = self.heartbeat_threads[grant_id]['last_heartbeat_success_time']
            if last_heartbeat_success_time_str != None and last_heartbeat_success_time_str != "":
                last_heartbeat_success_time = datetime.strptime(last_heartbeat_success_time_str, '%Y-%m-%dT%H:%M:%SZ')

                if current_time >= ( last_heartbeat_success_time + timedelta(days=7) ):
                    # sas 로 부터 heartbeat 의 응답을 7일동안 받지 못하면, SAS 와 연결이 끊겼다고 가정하고, 모든 channel 의 전송을 중지한다.
                    # 모든 heartbeat thread 를 중지하고, grant 를 삭제한다.
                    self.stop_all()
            """
            interval = self.heartbeat_threads[grant_id]['interval']
            time.sleep(interval)

        del self.heartbeat_threads[grant_id]

    def send_heartbeat(self, thread_id, grant_id, grantRenew = False):
        """REST API 호출로 heartbeat 메시지 전송."""
        shared_data = self.heartbeat_threads[grant_id]['shared_data']
        runcount = self.heartbeat_threads[grant_id]['runcount']
        print(f"Sending heartbeat from thread {thread_id}: {shared_data}")

        operationState =  "GRANTED" if runcount == 0 else "AUTHORIZED"

        self.heartbeat_threads[grant_id]['runcount'] = runcount + 1

        # 예시 REST API 호출
        try:
            response = requests.post(f"{self.settings_manager.get_setting('sasurl')}heartbeat", json={
                "cbsdId": thread_id,
                "grantId": grant_id,
                "grantRenew": grantRenew,
                "operationState": operationState, # or GRANTED
                "measReport": {
                }
            }, timeout=5)
            self.receive_message(thread_id, grant_id, response.json())
        except requests.exceptions.Timeout as e:
            print(f"Timeout {thread_id}: {e}")
        except Exception as e:
            print(f"Error sending heartbeat from thread {thread_id}: {e}")

    def receive_message(self, thread_id, grant_id, response):
        """수신한 메시지에 따라 동작 수행."""
        print(f"Thread {thread_id} received message: {response}")

        responseCode = response["response"]["responseCode"]
        responseMessage = response["response"]["responseMessage"]
        grantRenew = response["grantRenew"]
        if responseCode != 0:
            if responseCode == 501:  # SUSPENDED_GRANT
                print(responseMessage)
                if response["transmitExpireTime"] != "":
                    print('CBSD SUSPENDED_GRANT')
                    #msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response), "RESP")
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "SUSPENDED_GRANT", f"{{'message':'채널의 전송을 중지한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}", "REQ")

                    if "operationParam" in response:
                        # 만약 SAS 에서 operationParam 을 제시하면 이를 이용해서 grant 하고 relinquishment 한다.
                        self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "OPERATION_PARAM",
                                              f"{{'message':'operationParam을 고려해서 새로운 grant 를 보내고, 기존의 grant 는 relinquishment 한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                              "REQ")
                        lowFreq = response["operationParam"]["operationFrequencyRange"]["lowFrequency"]
                        highFreq = response["operationParam"]["operationFrequencyRange"]["highFrequency"]
                        grant_id = response["grantId"]

                        self.send_relinquishment(thread_id, grant_id)
                        self.send_grant(thread_id, lowFreq, highFreq)
                    else:
                        #self.cbsdEmulDao.grant_update_status(grant_id, "AUTHORIZED")
                        self.cbsdEmulDao.grant_update_status(grant_id, "GRANTED")
                        self.cbsdEmulDao.grant_update_suspend_at(grant_id, 1)


                    #asyncio.run(client_manager.send_message_to_clients(
                    #    '{"status":"SUSPENDED_GRANT", "cbsd_id":"' + payload["cbsdId"] + '"}'))


            elif responseCode == 500:  # TERMINATED_GRANT
                if response["transmitExpireTime"] != "":
                    print('CBSD TERMINATED_GRANT')

                    self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                    self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "TERMINATED_GRANT", f"{{'message':'채널의 전송을 중지한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}", "REQ")

                    if "operationParam" in response:
                        # 만약 SAS 에서 operationParam 을 제시하면 이를 이용해서 grant 하고 relinquishment 한다.
                        self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "OPERATION_PARAM",
                                              f"{{'message':'operationParam을 고려해서 새로운 grant 를 보내고, 기존의 grant 는 relinquishment 한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                              "REQ")
                        lowFreq = response["operationParam"]["operationFrequencyRange"]["lowFrequency"]
                        highFreq = response["operationParam"]["operationFrequencyRange"]["highFrequency"]
                        grant_id = response["grantId"]

                        self.send_relinquishment(thread_id, grant_id)
                        self.send_grant(thread_id, lowFreq, highFreq)

                    self.stop_heartbeat(grant_id)



            elif responseCode == 502:  # UNSYNC_OP_PARAM
                if response["transmitExpireTime"] != "":
                    print('CBSD UNSYNC_OP_PARAM')
                    self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                    self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "UNSYNC_OP_PARAM",
                                          f"{{'message':'채널의 전송을 중지한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                          "REQ")
                #msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response), "RESP")
        else:
            grant_data = self.cbsdEmulDao.grant_search(grant_id)
            if len(grant_data) > 0:
                self.cbsdEmulDao.grant_update_status(grant_id, "AUTHORIZED")
            if grantRenew:
                grantExpireTime = response["grantExpireTime"]
                interval = response["heartbeatInterval"]
                beforeTime = self.heartbeat_threads[grant_id]['expiration_time']

                self.heartbeat_threads[grant_id]['expiration_time'] = datetime.strptime(grantExpireTime, '%Y-%m-%dT%H:%M:%SZ')
                self.heartbeat_threads[grant_id]['interval'] = interval
                self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "GRANTRENEW",
                                      f"{{'message':'GRANT 의 grantExpireTime 을 갱신한다.', 'grantExpireTime':'{response['grantExpireTime']}', 'before':'{beforeTime}'}}", "REQ")
            print(responseMessage)

            #msgLogDao.insert(payload["cbsdId"], "SAS", "CBSD", "HEARTBEAT", json.dumps(response.json()), "RESP")

        self.heartbeat_threads[grant_id]['last_heartbeat_success_time'] = datetime.strptime(self.calcTime(0), '%Y-%m-%dT%H:%M:%SZ')

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

    def stop_heartbeat(self, grant_id):
        """특정 스레드 중지."""
        if grant_id in self.heartbeat_threads:
            self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
            self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)

            self.heartbeat_threads[grant_id]['running'] = False  # 실행 상태를 False로 변경
            #self.heartbeat_threads[grant_id]['thread'].join()  # 스레드가 종료될 때까지 대기
            #del self.heartbeat_threads[grant_id]  # 스레드 목록에서 제거

    def stop_all(self):
        """모든 스레드 중지."""
        for thread_id in list(self.heartbeat_threads.keys()):
            self.stop_heartbeat(thread_id)
            self.cbsdEmulDao.grant_delete(thread_id)

    def send_grant(self, cbsd_id, lowFreq, highFreq):
        try:
            response = requests.post("http://127.0.0.1:6543/api/grant", json={
                "cbsdId": cbsd_id,
                "operationParam": {
                    "maxEirp": 30,
                    "operationFrequencyRange": { "lowFrequency": lowFreq, "highFrequency": highFreq }
                }
            }, timeout=5)

            # response check
            responseCode = response.json()["response"]["responseCode"]
            responseMessage = response.json()["response"]["responseMessage"]
            if responseCode != 0:
                if responseCode == 401:  # GRANT_CONFLICT
                    print(responseMessage)

            else:
                # Create a PeriodicThread that runs every 5 seconds
                cbsdId = cbsd_id
                grantId = response.json()["grantId"]
                heartbeatInterval = response.json()["heartbeatInterval"]
                grantExpireTime = response.json()["grantExpireTime"]
                #heartbeatManager.start_heartbeat(cbsdId, grantId, heartbeatInterval, grantExpireTime)

                # 3. grant 정보 데이터베이스에 등록
                if not self.cbsdEmulDao.grant_exists(grantId) and responseCode == 0:
                    self.cbsdEmulDao.grant_insert(response.json(), grantId, cbsdId)
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

            responseCode = response.json()["response"]["responseCode"]
            responseMessage = response.json()["response"]["responseMessage"]
            if responseCode != 0:
                if responseCode == 401:  # GRANT_CONFLICT
                    print(responseMessage)

            else:
                # Create a PeriodicThread that runs every 5 seconds
                if self.cbsdEmulDao.grant_exists(grant_id):
                    self.cbsdEmulDao.grant_delete(grant_id)

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
    manager = HeartbeatManager()

    # 여러 스레드 시작
    expiration_time_1 = datetime.now() + timedelta(minutes=10)  # 초기 만료 시간 설정
    manager.start_heartbeat('thread_1', 'grant_id', 2, expiration_time_1)  # 2초마다 heartbeat 전송

    expiration_time_2 = datetime.now() + timedelta(minutes=10)
    manager.start_heartbeat('thread_2', 'grant_id', 3, expiration_time_2)  # 3초마다 heartbeat 전송

    # 일정 시간 후 모든 스레드 중지
    time.sleep(30)
    manager.stop_all()
    print("All heartbeat threads stopped.")
