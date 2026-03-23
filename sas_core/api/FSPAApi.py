import pymysql
import json
from datetime import datetime, timedelta
import pytz

from api.CBSDErrorCodes import CBSDErrorCodes
from api.CbsdDao import CbsdDao
from api.EscDao import EscDao
from api.FspaDao import FspaDao
from api.SdDao import SdDao
from api.SfDao import SfDao
from api.SysPropDao import SysPropDao
from util.utils import get_channels


class FSPAApi:
    def __init__(self, db_config):
        self.fspaDao = FspaDao(db_config)
        self.sfDao = SfDao(db_config)
        self.SdDao = SdDao(db_config)


    def cbsd_exists(self, cbsd_id):
        return self.CbsdDao.cbsd_exists(cbsd_id)


    def spa_update(self):
        # get spa list
        try:
            spa_list = self.fspaDao.fspa_list()

            if spa_list != None:

                self.sfDao.sf_delete_all()
                for spa in spa_list:
                    lat = spa["RX_LATITUDE"]
                    lng = spa["RX_LONGITUDE"]
                    move_list = self.fspaDao.move_list(lat,lng)

                    ch_list = get_channels(spa["CENTER_FREQUENCY"], spa["LICENSED_BANDWIDTH"])

                    for mfsd in move_list:
                        is_mfsd_exist = self.sfDao.sf_exists(mfsd["CBSD_ID"])
                        if is_mfsd_exist == 0:
                            self.sfDao.sf_insert(mfsd["FCC_ID"], mfsd["CBSD_ID"])
                        self.sfDao.update_channels(mfsd["FCC_ID"], mfsd["CBSD_ID"], ch_list)
            self.SdDao.merge_sd()

        except Exception as e:
            # 그 외 파일 처리 중 오류 발생 시
            print(f"An error occurred while processing the file: {e}")

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")




