import json

class SettingsManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.settings = {}

    def load_settings(self):
        try:
            with open(self.file_path, 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            db_config = {
                'host': '192.168.0.166',
                'user': 'root',
                'password': 'delta5535',
                'database': '2024sas_dev'
            }
            print("설정 파일이 존재하지 않습니다. 새로운 설정 파일을 생성합니다.")
            self.settings["host"] = "192.168.0.166"
            self.settings["user"] = "root"
            self.settings["password"] = "delta5535"
            self.settings["database"] = "2024sas_dev"
            self.settings["sasurl"] = "http://127.0.0.1:8000/"


            self.save_settings()

    def save_settings(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_setting(self, key):
        return self.settings.get(key)

    def set_setting(self, key, value):
        self.settings[key] = value

        # 설정 값 변경 후 자동으로 저장
        self.save_settings()
