import threading
import time

import requests
from datetime import datetime, timedelta

from api.MsgLogDao import MsgLogDao
from api.property import SettingsManager
from cbsd_emul_v1_0.views.CbsdEmulDao import CbsdEmulDao

class HeartbeatManager:
    def __init__(self):
        self.heartbeat_threads = {}
        config_file_path = 'config.json'

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

        self.settings_manager = SettingsManager(config_file_path)
        self.settings_manager.load_settings()

    def restore_heartbeats(self):
        """프로세스 재시작 시 DB의 활성 Grant에 대해 Heartbeat 스레드를 복구한다."""
        active_grants = self.cbsdEmulDao.grant_list_active_detail()
        if not active_grants:
            print("[HeartbeatManager] No active grants to restore.")
            return

        now = datetime.utcnow()
        restored = 0
        expired = 0

        for grant in active_grants:
            cbsd_id = grant["CBSD_ID"]
            grant_id = grant["GRANT_ID"]
            interval = grant.get("HB_IINTV") or 60
            expire_time = grant.get("GRANT_EXPIRETIME")

            if interval <= 0:
                interval = 60

            # GRANT_EXPIRETIME이 없거나 파싱 불가하면 스킵
            if not expire_time:
                print(f"[HeartbeatManager] Grant {grant_id}: no expireTime, setting to IDLE")
                self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                expired += 1
                continue

            # datetime 객체이면 그대로, 문자열이면 파싱
            if isinstance(expire_time, str):
                try:
                    expire_dt = datetime.strptime(expire_time, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    try:
                        expire_dt = datetime.strptime(expire_time, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        print(f"[HeartbeatManager] Grant {grant_id}: invalid expireTime format '{expire_time}'")
                        self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                        expired += 1
                        continue
            else:
                expire_dt = expire_time

            # 이미 만료된 Grant는 IDLE로 변경
            if now >= expire_dt:
                print(f"[HeartbeatManager] Grant {grant_id}: expired ({expire_dt}), setting to IDLE")
                self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)
                expired += 1
                continue

            # 유효한 Grant — Heartbeat 스레드 시작
            expire_str = expire_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            self.start_heartbeat(cbsd_id, grant_id, interval, expire_str)
            restored += 1
            print(f"[HeartbeatManager] Grant {grant_id}: restored (expires {expire_dt}, interval {interval}s)")

        print(f"[HeartbeatManager] Restore complete: {restored} restored, {expired} expired")

    def start_heartbeat(self, thread_id, grant_id, interval, expiration_time):
        """주기적으로 heartbeat 메시지를 보내는 스레드 시작."""
        if interval <= 0:
            interval = 60
        expiration_time_t = datetime.strptime(expiration_time, '%Y-%m-%dT%H:%M:%SZ')
        self.heartbeat_threads[grant_id] = {
            'cbsd_id': thread_id,
            'grant_id': grant_id,
            'thread': None,
            'interval': interval,
            'shared_data': {},
            'runcount': 0,
            'running': True,
            'expiration_time': expiration_time_t,
            'last_heartbeat_success_time': ''
        }
        thread = threading.Thread(target=self.heartbeat_thread, args=(thread_id, grant_id, interval))
        thread.daemon = True
        thread.start()
        self.heartbeat_threads[grant_id]['thread'] = thread

    def heartbeat_thread(self, thread_id, grant_id, interval):
        """주기적으로 heartbeat 메시지를 보내는 메서드."""
        while grant_id in self.heartbeat_threads and self.heartbeat_threads[grant_id]['running']:
            expiration_time = self.heartbeat_threads[grant_id]['expiration_time']
            current_time = datetime.utcnow()

            # C3 수정: 5초 전(만료 임박)을 먼저 체크해야 elif에 도달 가능
            if current_time >= expiration_time - timedelta(seconds=5):
                # grantExpireTime 만료 — 스레드 종료
                self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "GRANT EXPIRED",
                                      f"{{'message':'grantExpiredTime 만료 되었다.', 'grantExpireTime':'{expiration_time}', 'currentTime':'{current_time}'}}",
                                      "REQ")
                self.heartbeat_threads[grant_id]['running'] = False
                break

            elif current_time >= expiration_time - timedelta(minutes=5):
                # grantExpireTime 5분 전 — grantRenew 요청
                self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "GRANT EXPIRE IMMINENT",
                                      f"{{'message':'grantExpiredTime 만료 5분전이다.', 'grantExpireTime':'{expiration_time}', 'currentTime':'{current_time}'}}",
                                      "REQ")
                self.send_heartbeat(thread_id, grant_id, True)

            else:
                # 일반 heartbeat
                self.send_heartbeat(thread_id, grant_id)

            # interval 재확인 (grantRenew 응답에서 변경될 수 있음)
            if grant_id not in self.heartbeat_threads:
                break
            interval = self.heartbeat_threads[grant_id]['interval']
            if interval <= 0:
                interval = 60
            time.sleep(interval)

        # 스레드 종료 시 정리
        if grant_id in self.heartbeat_threads:
            del self.heartbeat_threads[grant_id]

    def send_heartbeat(self, thread_id, grant_id, grantRenew=False):
        """REST API 호출로 heartbeat 메시지 전송."""
        if grant_id not in self.heartbeat_threads:
            return
        shared_data = self.heartbeat_threads[grant_id]['shared_data']
        runcount = self.heartbeat_threads[grant_id]['runcount']

        operationState = "GRANTED" if runcount == 0 else "AUTHORIZED"
        self.heartbeat_threads[grant_id]['runcount'] = runcount + 1

        try:
            response = requests.post(f"{self.settings_manager.get_setting('sasurl')}heartbeat", json={
                "cbsdId": thread_id,
                "grantId": grant_id,
                "grantRenew": grantRenew,
                "operationState": operationState,
                "measReport": {}
            }, timeout=5)
            self.receive_message(thread_id, grant_id, response.json())
        except requests.exceptions.Timeout as e:
            print(f"Timeout {thread_id}: {e}")
        except Exception as e:
            print(f"Error sending heartbeat from thread {thread_id}: {e}")

    def receive_message(self, thread_id, grant_id, response):
        """수신한 메시지에 따라 동작 수행."""
        # C5 수정: stop 후 dict 접근 방어
        if grant_id not in self.heartbeat_threads:
            return

        responseCode = response["response"]["responseCode"]
        responseMessage = response["response"]["responseMessage"]
        grantRenew = response.get("grantRenew", False)

        if responseCode != 0:
            if responseCode == 501:  # SUSPENDED_GRANT
                if response.get("transmitExpireTime", "") != "":
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "SUSPENDED_GRANT",
                                          f"{{'message':'채널의 전송을 중지한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                          "REQ")

                    if "operationParam" in response:
                        self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "OPERATION_PARAM",
                                              f"{{'message':'operationParam을 고려해서 새로운 grant 를 보내고, 기존의 grant 는 relinquishment 한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                              "REQ")
                        lowFreq = response["operationParam"]["operationFrequencyRange"]["lowFrequency"]
                        highFreq = response["operationParam"]["operationFrequencyRange"]["highFrequency"]
                        grant_id_resp = response["grantId"]

                        self.send_relinquishment(thread_id, grant_id_resp)
                        self.send_grant(thread_id, lowFreq, highFreq)
                    else:
                        self.cbsdEmulDao.grant_update_status(grant_id, "GRANTED")
                        self.cbsdEmulDao.grant_update_suspend_at(grant_id, 1)

            elif responseCode == 500:  # TERMINATED_GRANT
                if response.get("transmitExpireTime", "") != "":
                    self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                    self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "TERMINATED_GRANT",
                                          f"{{'message':'채널의 전송을 중지한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                          "REQ")

                    if "operationParam" in response:
                        self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "OPERATION_PARAM",
                                              f"{{'message':'operationParam을 고려해서 새로운 grant 를 보내고, 기존의 grant 는 relinquishment 한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                              "REQ")
                        lowFreq = response["operationParam"]["operationFrequencyRange"]["lowFrequency"]
                        highFreq = response["operationParam"]["operationFrequencyRange"]["highFrequency"]
                        grant_id_resp = response["grantId"]

                        self.send_relinquishment(thread_id, grant_id_resp)
                        self.send_grant(thread_id, lowFreq, highFreq)

                    self.stop_heartbeat(grant_id)

            elif responseCode == 502:  # UNSYNC_OP_PARAM
                if response.get("transmitExpireTime", "") != "":
                    self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
                    self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "UNSYNC_OP_PARAM",
                                          f"{{'message':'채널의 전송을 중지한다.', 'transmitExpireTime':'{response['transmitExpireTime']}'}}",
                                          "REQ")
                # 502: 스레드 종료
                self.stop_heartbeat(grant_id)

        else:
            # SUCCESS
            if grant_id not in self.heartbeat_threads:
                return
            grant_data = self.cbsdEmulDao.grant_search(grant_id)
            if grant_data and len(grant_data) > 0:
                self.cbsdEmulDao.grant_update_status(grant_id, "AUTHORIZED")
            if grantRenew and grant_id in self.heartbeat_threads:
                grantExpireTime = response.get("grantExpireTime", "")
                interval = response.get("heartbeatInterval", 60)
                if interval <= 0:
                    interval = 60
                if grantExpireTime:
                    beforeTime = self.heartbeat_threads[grant_id]['expiration_time']
                    self.heartbeat_threads[grant_id]['expiration_time'] = datetime.strptime(grantExpireTime, '%Y-%m-%dT%H:%M:%SZ')
                    self.heartbeat_threads[grant_id]['interval'] = interval
                    self.msgLogDao.insert(thread_id, "CBSD", "CBSD", "GRANTRENEW",
                                          f"{{'message':'GRANT 의 grantExpireTime 을 갱신한다.', 'grantExpireTime':'{grantExpireTime}', 'before':'{beforeTime}'}}",
                                          "REQ")

        # C5 수정: dict 존재 확인 후 접근
        if grant_id in self.heartbeat_threads:
            self.heartbeat_threads[grant_id]['last_heartbeat_success_time'] = datetime.utcnow()

    def stop_heartbeat(self, grant_id):
        """특정 스레드 중지."""
        if grant_id in self.heartbeat_threads:
            self.cbsdEmulDao.grant_update_status(grant_id, "IDLE")
            self.cbsdEmulDao.grant_update_suspend_at(grant_id, 0)
            self.heartbeat_threads[grant_id]['running'] = False

    def stop_all(self):
        """모든 스레드 중지."""
        for thread_id in list(self.heartbeat_threads.keys()):
            self.stop_heartbeat(thread_id)
            self.cbsdEmulDao.grant_delete(thread_id)

    # 자기 자신(cbsd_emul)의 grant 핸들러를 재사용하여 새 Grant 요청
    def send_grant(self, cbsd_id, lowFreq, highFreq):
        try:
            response = requests.post("http://127.0.0.1:6543/api/grant", json={
                "cbsdId": cbsd_id,
                "operationParam": {
                    "maxEirp": 30,
                    "operationFrequencyRange": {"lowFrequency": lowFreq, "highFrequency": highFreq}
                }
            }, timeout=5)

            responseCode = response.json()["response"]["responseCode"]
            if responseCode == 0:
                cbsdId = cbsd_id
                grantId = response.json()["grantId"]
                if not self.cbsdEmulDao.grant_exists(grantId):
                    self.cbsdEmulDao.grant_insert(response.json(), grantId, cbsdId)
        except requests.exceptions.Timeout as e:
            print(f"Timeout send_grant {cbsd_id}: {e}")
        except Exception as e:
            print(f"Error send_grant {cbsd_id}: {e}")

    # 자기 자신(cbsd_emul)의 relinquishment 핸들러를 재사용
    def send_relinquishment(self, cbsd_id, grant_id):
        try:
            response = requests.post("http://127.0.0.1:6543/api/relinquishment", json={
                "cbsdId": cbsd_id,
                "grantId": grant_id
            }, timeout=5)

            responseCode = response.json()["response"]["responseCode"]
            if responseCode == 0:
                if self.cbsdEmulDao.grant_exists(grant_id):
                    self.cbsdEmulDao.grant_delete(grant_id)
        except requests.exceptions.Timeout as e:
            print(f"Timeout send_relinquishment {cbsd_id}: {e}")
        except Exception as e:
            print(f"Error send_relinquishment {cbsd_id}: {e}")

    def calcTime(self, sec):
        now = datetime.utcnow()
        future_time = now + timedelta(seconds=sec)
        return future_time.strftime('%Y-%m-%dT%H:%M:%SZ')
