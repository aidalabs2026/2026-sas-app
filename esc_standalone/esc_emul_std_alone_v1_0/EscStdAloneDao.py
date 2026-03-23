import sqlite3
import json
from datetime import datetime, timedelta

class EscStdAloneDao:
    def __init__(self, db_path):
        self.db_path = "esc_std_alone.sqlite3"#db_path
        self.connection = None
        self.connect()
        self.initialize_tables()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            print("Connected to SQLite database")
        except sqlite3.Error as e:
            print(f"Connection error: {e}")

    def initialize_tables(self):
        try:
            with self.connection as conn:
                cursor = conn.cursor()

                # TD_ESC_REGIST
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS TD_ESC_REGIST (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    SENSOR_ID TEXT UNIQUE,
                    LAT REAL,
                    LNG REAL,
                    HEIGHT REAL,
                    HEIGHT_TYPE TEXT,
                    ANTENNA_AZIMUTH INTEGER,
                    ANTENNA_DOWNTILT INTEGER,
                    AZIMUTH_RAD_PATTERN TEXT,
                    ELEVATION_RAD_PATTERN TEXT,
                    STATUS TEXT,
                    PROTECT_LEVEL TEXT,
                    DPA_ID TEXT,
                    DELETE_AT TEXT DEFAULT 'N'
                )
                """)

                # TD_ESC_CHANNELS
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS TD_ESC_CHANNELS (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    SENSOR_ID TEXT,
                    CH_NO TEXT,
                    LOW_FREQ TEXT,
                    HIGH_FREQ TEXT,
                    INCUMBENT_USER INTEGER DEFAULT 0
                )
                """)

                # TD_GRANT
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS TD_GRANT (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CBSD_ID TEXT,
                    GRANT_ID TEXT,
                    STATUS TEXT
                    -- 필요한 다른 필드가 있다면 여기에 추가하세요
                )
                """)

                print("Tables initialized successfully")
        except sqlite3.Error as e:
            print(f"Error initializing tables: {e}")

    def esc_exists(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM TD_ESC_REGIST WHERE SENSOR_ID = ? AND DELETE_AT = 'N'", (sensor_id,))
                result = cursor.fetchone()
                return result['count']
        except sqlite3.Error as e:
            print(f"Error checking sensor existence: {e}")
            return False

    def esc_search(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TD_ESC_REGIST WHERE SENSOR_ID = ? AND DELETE_AT = 'N'", (sensor_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return False

    def esc_ch_exists(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM TD_ESC_CHANNELS WHERE SENSOR_ID = ?", (sensor_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return False

    def esc_list(self):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TD_ESC_REGIST WHERE DELETE_AT='N' ORDER BY SENSOR_ID ASC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]  # Row 객체를 dict로 변환
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None

    def esc_insert(self, esc):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO TD_ESC_REGIST (SENSOR_ID, LAT, LNG, HEIGHT, HEIGHT_TYPE, ANTENNA_AZIMUTH, ANTENNA_DOWNTILT,
                                    AZIMUTH_RAD_PATTERN, ELEVATION_RAD_PATTERN, STATUS, PROTECT_LEVEL, DPA_ID)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (esc.escSensorId, esc.installationParam["latitude"], esc.installationParam["longitude"],
                                esc.installationParam["height"], esc.installationParam["heightType"],
                                esc.installationParam["antennaAzimuth"], esc.installationParam["antennaDowntilt"],
                                json.dumps(esc.installationParam["azimuthRadiationPattern"]),
                                json.dumps(esc.installationParam["elevationRadiationPattern"]), "REGIST",
                                esc.protectionLevel, esc.dpaId))
                return True
        except sqlite3.Error as e:
            print(e)
            return False

    def esc_update(self, esc):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE TD_ESC_REGIST
                    SET LAT = ?, LNG = ?, HEIGHT = ?, HEIGHT_TYPE = ?, ANTENNA_AZIMUTH = ?, ANTENNA_DOWNTILT = ?,
                        AZIMUTH_RAD_PATTERN = ?, ELEVATION_RAD_PATTERN = ?, STATUS = ?, PROTECT_LEVEL = ?, DPA_ID = ?
                    WHERE SENSOR_ID = ? AND DELETE_AT = 'N'
                """, (
                    esc.installationParam["latitude"],
                    esc.installationParam["longitude"],
                    esc.installationParam["height"],
                    esc.installationParam["heightType"],
                    esc.installationParam["antennaAzimuth"],
                    esc.installationParam["antennaDowntilt"],
                    json.dumps(esc.installationParam["azimuthRadiationPattern"]),
                    json.dumps(esc.installationParam["elevationRadiationPattern"]),
                    "REGIST",
                    esc.protectionLevel,
                    esc.dpaId,
                    esc.escSensorId
                ))
                return True
        except sqlite3.Error as e:
            print(e)
            return False

    def esc_channels_insert(self, esc):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                for i in range(10):
                    ch_no = str(i + 1)
                    low_freq = str(3300000000 + i * 10000000)
                    high_freq = str(3300000000 + (i + 1) * 10000000)
                    cursor.execute("INSERT INTO TD_ESC_CHANNELS (SENSOR_ID, CH_NO, LOW_FREQ, HIGH_FREQ) VALUES (?, ?, ?, ?)",
                                   (esc.escSensorId, ch_no, low_freq, high_freq))
                return True
        except sqlite3.Error as e:
            print(e)
            return False

    def sensor_channel_list(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TD_ESC_CHANNELS WHERE SENSOR_ID = ? ORDER BY CH_NO ASC", (sensor_id,))
                #return cursor.fetchall()
                rows = cursor.fetchall()
                return [dict(row) for row in rows]  # Row 객체를 dict로 변환
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return []

    def esc_ch_update_status(self, sensor_id, low_freq, high_freq, status):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("""UPDATE TD_ESC_CHANNELS SET INCUMBENT_USER=? 
                                  WHERE SENSOR_ID = ? AND LOW_FREQ=? AND HIGH_FREQ=?""",
                               (status, sensor_id, low_freq, high_freq))
                return True
        except sqlite3.Error as e:
            return False

    def esc_delete(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE TD_ESC_REGIST SET STATUS='DEREGIST' WHERE SENSOR_ID = ?", (sensor_id,))
                return True
        except sqlite3.Error as e:
            return False

    def esc_delete_all(self):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM TD_ESC_REGIST")
                return True
        except sqlite3.Error as e:
            return False

    def esc_sensor_delete(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE TD_ESC_REGIST SET DELETE_AT='Y' WHERE ID = ?", (sensor_id,))
                return True
        except sqlite3.Error as e:
            return False

    def esc_channels_delete(self, sensor_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM TD_ESC_CHANNELS WHERE SENSOR_ID=?", (sensor_id,))
                return True
        except sqlite3.Error as e:
            return False

    def esc_channels_delete_all(self):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM TD_ESC_CHANNELS")
                return True
        except sqlite3.Error as e:
            return False

    def grant_list_by_freq(self, lowFreq, highFreq):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TD_GRANT LIMIT 1")
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return False

    def grant_list(self, cbsd_id):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TD_GRANT WHERE CBSD_ID = ? ORDER BY GRANT_ID ASC", (cbsd_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None

    def grant_update_status(self, grant_id, status):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE TD_GRANT SET STATUS = ? WHERE GRANT_ID = ?", (status, grant_id))
                return True
        except sqlite3.Error as e:
            return False

    def esc_sensing_channel_status(self, row_freq=None, high_freq=None):
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                if row_freq is None:
                    query = """SELECT CH_NO, LOW_FREQ, HIGH_FREQ,
                                      SUM(CASE WHEN INCUMBENT_USER = 1 THEN 1 ELSE 0 END) AS COUNT_USER_1,
                                      SUM(CASE WHEN INCUMBENT_USER = 0 THEN 1 ELSE 0 END) AS COUNT_USER_0
                               FROM TD_ESC_CHANNELS
                               GROUP BY CH_NO
                               ORDER BY CH_NO ASC"""
                    cursor.execute(query)
                else:
                    query = """SELECT CH_NO, LOW_FREQ, HIGH_FREQ,
                                      SUM(CASE WHEN INCUMBENT_USER = 1 THEN 1 ELSE 0 END) AS COUNT_USER_1,
                                      SUM(CASE WHEN INCUMBENT_USER = 0 THEN 1 ELSE 0 END) AS COUNT_USER_0
                               FROM TD_ESC_CHANNELS
                               WHERE LOW_FREQ=? AND HIGH_FREQ=?
                               GROUP BY CH_NO
                               ORDER BY CH_NO ASC"""
                    cursor.execute(query, (row_freq, high_freq))
                #return cursor.fetchall()
                rows = cursor.fetchall()
                return [dict(row) for row in rows]  # Row 객체를 dict로 변환
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return None

    def close(self):
        if self.connection:
            self.connection.close()
