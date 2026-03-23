import pymysql
import json

from api.ApplyDao import ApplyDao
from api.CbsdDao import CbsdDao
from api.EscDao import EscDao
from api.SdDao import SdDao
from api.SnDao import SnDao
from apply_scheduler.ApplyScheduler import ApplyScheduler
from util.utils import get_channels


class ApplyApi:
    def __init__(self, db_config, connected_clients):
        self.db_config = db_config
        self.ApplyDao = ApplyDao(db_config)
        self.snDao = SnDao(db_config)
        self.SdDao = SdDao(db_config)
        self.CbsdDao = CbsdDao(db_config)
        self.applyScheduler = ApplyScheduler(connected_clients)
        self.connected_clients = connected_clients

        self.load_apply_scheduler()

    async def broadcast_message(self, message: str):
        for client in self.connected_clients:
            try:
                print(message)
                await client.send_text(message)
            except Exception as e:
                print("메시지 전송 실패:", e)

    def load_apply_scheduler(self):
        apply_list = self.ApplyDao.activate_apply_list()

        for apply in apply_list:
            if apply['PERIOD_TYPE'] == 'periodic':
                self.applyScheduler.add_periodic_event(apply['ID'], apply['PERIODIC_START'], apply['PERIODIC_END'], apply['PERIODIC_DAY'],
                                                        apply['PERIODIC_START_TIME'], apply['PERIODIC_END_TIME'],
                                                       self.periodic_on_day_start, self.periodic_on_day_end)
            else:
                non_periodic_list = self.ApplyDao.non_periodic_list_by_apply_id(apply['ID'])
                for non_periodic in non_periodic_list:
                    self.applyScheduler.add_non_periodic_event(apply['ID'], non_periodic['ID'], non_periodic['NON_PERIODIC_START'], non_periodic['NON_PERIODIC_END'], self.periodic_on_day_start, self.periodic_on_day_end)

        #self.applyScheduler.init_scheduler(apply_list)



    def create(self, apply):
        try:
            apply_id = self.ApplyDao.apply_insert_or_update(apply)
            non_periodic_times = apply.get('nonPeriodicTime', {})
            if non_periodic_times and apply_id:
                for item in non_periodic_times:
                    self.ApplyDao.non_periodic_insert_or_update(item, apply_id)

            periodType = apply.get('periodType', {})
            if periodType == 'periodic':
                self.applyScheduler.add_periodic_event(apply_id, apply['periodicStart'],
                                                       apply['periodicEnd'], apply['periodicDay'],
                                                       apply['startTime'], apply['endTime'],
                                                       self.periodic_on_day_start, self.periodic_on_day_end)
            else:
                non_periodic_list = self.ApplyDao.non_periodic_list_by_apply_id(apply_id)
                for non_periodic in non_periodic_list:
                    self.applyScheduler.add_non_periodic_event(apply_id, non_periodic['ID'],
                                                               non_periodic['NON_PERIODIC_START'],
                                                               non_periodic['NON_PERIODIC_END'],
                                                               self.periodic_on_day_start, self.periodic_on_day_end)
            return {
                "applyId": apply_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": ""
                }
            }
        except pymysql.MySQLError as e:
            return {
                    "applyId": 0,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": str(e)
                    }
                }

    def update(self, apply, apply_id):
        try:
            self.ApplyDao.apply_insert_or_update(apply, apply_id)
            non_periodic_times = apply.get('nonPeriodicTime', {})
            if non_periodic_times and apply_id:
                self.ApplyDao.non_periodic_delete_by_apply_id(apply_id)
                for item in non_periodic_times:
                    self.ApplyDao.non_periodic_insert_or_update(item, apply_id)

            self.applyScheduler.remove_event(apply_id)
            periodType = apply.get('periodType', {})

            if periodType == 'periodic':
                self.applyScheduler.add_periodic_event(apply_id, apply['periodicTime']['startDateTime'],
                                                       apply['periodicTime']['endDateTime'], apply['periodicTime']['weekday'],
                                                       apply['periodicTime']['startTime'],apply['periodicTime']['endTime'],
                                                       self.periodic_on_day_start, self.periodic_on_day_end)
            else:
                non_periodic_list = self.ApplyDao.non_periodic_list_by_apply_id(apply_id)
                for non_periodic in non_periodic_list:
                    self.applyScheduler.add_non_periodic_event(apply_id , non_periodic['ID'],
                                                               non_periodic['NON_PERIODIC_START'],
                                                               non_periodic['NON_PERIODIC_END'],
                                                               self.periodic_on_day_start, self.periodic_on_day_end)

            return {
                "applyId": apply_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": ""
                }
            }
        except pymysql.MySQLError as e:
            return {
                    "applyId": 0,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": str(e)
                    }
                }

    def get_applications(self, apply_id=None, start_date=None, end_date=None):
        try:
            applications = self.ApplyDao.get_applications(apply_id = apply_id, start_date=start_date, end_date=end_date)
            if apply_id:
                return {
                    "application": applications[0],
                    "response": {
                        "responseCode": 0,
                        "responseMessage": "Success"
                    }
                }
            # 전체 조회인 경우
            else:
                return {
                    "applications": applications,
                    "response": {
                        "responseCode": 0,
                        "responseMessage": "Success"
                    }
                }


        except pymysql.MySQLError as e:
            print("Exception : ", e)
            return {
                "applications": None,
                "response": {
                    "responseCode": 1,
                    "responseMessage": str(e)
                }
            }
    def delete(self, apply_id):
        try:
            self.ApplyDao.apply_delete(apply_id)
            return {
                "applyId": apply_id,
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }

            self.applyScheduler.remove_event(apply_id)

        except pymysql.MySQLError as e:
            return {
                    "applyId": apply_id,
                    "response": {
                        "responseCode": 1,
                        "responseMessage": str(e)
                    }
                }

    def periodic_on_day_start(self, apply_id):
        apply = self.ApplyDao.apply_get(apply_id)
        if apply is None:
            print(f"[WARN] apply_id={apply_id} 에 해당하는 신청 정보가 없습니다.")
            return
        cent_freq = apply['FREQUENCY']
        bw = apply['LIC_BAND']

        ch_list = get_channels(cent_freq, bw) # 신청 정보가 영향을 주는 채널 조회
        print(f"[INFO] apply_id={apply_id}, 중심주파수={cent_freq}, 대역폭={bw}, 채널목록={ch_list}")

        move_list = self.ApplyDao.apply_move_list(apply_id)
        print(f"[INFO] 이동 리스트 조회됨: {len(move_list)}건")

        for mfsd in move_list:
            print(f"[DEBUG] 처리 중: FCC_ID={mfsd['FCC_ID']}, CBSD_ID={mfsd['CBSD_ID']}")
            is_mfsd_exist = self.snDao.sn_exists(mfsd["CBSD_ID"])
            if is_mfsd_exist == 0:
                print(f"[INFO] 신규 CBSD_ID 발견 → sn_insert 실행")
                self.snDao.sn_insert(mfsd["FCC_ID"], mfsd["CBSD_ID"])

            print(f"[INFO] 채널 상태를 non-available 로 업데이트: {ch_list}")
            self.snDao.update_channels_to_nonavail(mfsd["FCC_ID"], mfsd["CBSD_ID"], ch_list)

            print(f"[ACTION] mfsd_suspend 호출: CBSD_ID={mfsd['CBSD_ID']}, 채널={ch_list}")
            self.mfsd_suspend( mfsd, ch_list)
            self.broadcast_message( mfsd)
        self.SdDao.merge_sd()

    def periodic_on_day_end(self, apply_id):
        apply = self.ApplyDao.apply_get(apply_id)
        if apply is None:
            return
        cent_freq = apply['FREQUENCY']
        bw = apply['LIC_BAND']

        ch_list = get_channels(cent_freq, bw) # 신청 정보가 영향을 주는 채널 조회

        move_list = self.ApplyDao.apply_move_list(apply_id)

        for mfsd in move_list:
            is_mfsd_exist = self.snDao.sn_exists(mfsd["CBSD_ID"])
            if is_mfsd_exist == 0:
                self.snDao.sn_insert(mfsd["FCC_ID"], mfsd["CBSD_ID"])
            # 신청정보가 영향을 주는 채널의 상태를 다시 가용 상태로 해야하는데, 이 시점에 해당 mfsd 에 영향을 주는 다른 신청정보가 Active 인게 있는지 확인해서,
            # 만약 있다면 가용으로 하지 못하고 불용으로 둬야 한다.
            # 그러려면 mfsd가 속하는 다른 신청정보가 있는지 찾아야 하고..
            for ch in ch_list:
                # 1. 먼저 MFSD 의 위치 정보와 ch 정보를 이용해서 활성화 되어 있는 다른 신청정보가 있는지 확인한다.
                # TD_SN 테이블 업데이트를 하기위한 조건.
                active_apply = self.ApplyDao.get_active_apply_emul_by_channel_and_mfsd(mfsd['LAT'], mfsd['LNG'], ch)
                if len(active_apply) == 0:
                    self.snDao.update_channels_to_avail(mfsd["FCC_ID"], mfsd["CBSD_ID"], ch)
                # mfsd의 GRANT를 재개한다.
                self.mfsd_resume(mfsd, [ch])
                self.broadcast_message(mfsd)

        self.SdDao.merge_sd()

    def mfsd_suspend(self, mfsd, ch_list):

        for ch in ch_list:
            lowFrequency = (3300 + (10 * (ch - 1))) * 1000000
            highFrequency = (3300 + (10 * (ch)))  * 1000000
            print(f"[INFO] CBSD_ID={mfsd['CBSD_ID']} → 채널={ch}, 주파수범위={lowFrequency}~{highFrequency} MHz")

            try:
                # 해당 채널에 대한 low, high frequency 를 구한다.
                # 1. 해당 주파수 대역에 grant 받은 cbsd가 있는지 조회한다.
                grant_list = self.CbsdDao.grant_list_by_freq_and_cbsd_id(lowFrequency, highFrequency, "AUTHORIZED", 0, mfsd['CBSD_ID'])

                print(f"[DEBUG] 조회된 grant 개수: {len(grant_list)} (채널={ch})")
                # 2. 각 CBSD 의 조회 된 grant 상태를 suspend 로 바꾸고,
                for grant in grant_list:
                    self.CbsdDao.grant_update_suspend_at(grant["GRANT_ID"], 1)
                    self.CbsdDao.grant_update_status(grant["GRANT_ID"], "GRANTED")

            except Exception as e:
                print(f"[ERROR] CBSD_ID={mfsd['CBSD_ID']}, 채널={ch}, 주파수={lowFrequency}~{highFrequency} MHz 처리 중 오류 발생 → {e}")

    def mfsd_resume(self, mfsd, ch_list):
        try:
            for ch in ch_list:
                lowFrequency = (3300 + (10 * (ch - 1))) * 1000000
                highFrequency = (3300 + (10 * (ch)))  * 1000000
                # 해당 채널에 대한 low, high frequency 를 구한다.
                # 1. 해당 주파수 대역에 grant 받은 cbsd가 있는지 조회한다.
                grant_list = self.CbsdDao.grant_list_by_freq_and_cbsd_id(lowFrequency, highFrequency, "GRANTED", 1, mfsd['CBSD_ID'])

                for grant in grant_list:
                    self.CbsdDao.grant_update_status(grant["GRANT_ID"], "AUTHORIZED")
                    self.CbsdDao.grant_update_suspend_at(grant["GRANT_ID"], 0)

        except Exception as e:
            print(f"[ERROR] CBSD_ID={mfsd['CBSD_ID']}, 채널={ch}, 주파수={lowFrequency}~{highFrequency} MHz 처리 중 오류 발생 → {e}")
    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")