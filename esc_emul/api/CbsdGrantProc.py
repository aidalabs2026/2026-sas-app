class CbsdGrantProc:
    def grant(self, grant):
        try:
            with self.connection.cursor() as cursor:
                query = """INSERT INTO TD_GRANT (CBSD_ID, MAX_EIRP, LOW_FREQ, HIGH_FREQ, STATUS, HB_DUR, HB_IINTV, CH_TYPE) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

                values = tuple(map(cbsd.get, [
                    'fccId', 'cbsdCategory', 'callSign', 'userId', 'radioTechnology', 'supportedSpec', 'vendor', 'model','softwareVersion', 'hardwareVersion',
                    'firmwareVersion', 'cbsdSerialNumber', 'measCapability', 'latitude', 'longitude', 'height', 'heightType','horizontalAccuracy', 'verticalAccuracy', 'indoorDeployment',
                    'antennaAzimuth', 'antennaDowntilt', 'antennaGain', 'eirpCapability', 'antennaBeamwidth', 'antennaModel', 'CBSD_ID'
                ]))

                cursor.execute(query, values)
                self.connection.commit()
                return {
                    "cbsdId": cbsd_id,
                    "measReportConfig": ["EutraCarrierRssiAlways"],
                    "response": {
                        "responseCode": 0,
                        "responseMessage": "SUCCESS"
                    }
                }
        except pymysql.MySQLError as e:
            print(e)
            return {
                "cbsdId": cbsd_id,
                "measReportConfig": ["EutraCarrierRssiAlways"],
                "response": {
                    "responseCode": 0,
                    "responseMessage": "SUCCESS"
                }
            }