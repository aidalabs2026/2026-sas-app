import webbrowser
import asyncio
import threading
from wsgiref.simple_server import make_server

from cbsd_emul_v1_0 import main
from cbsd_emul_v1_0.websocket.ClientManager import ClientManager

client_manager = ClientManager()

clients = set()


def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("WebSocket server started on ws://localhost:8765")
    loop.run_forever()


def open_browser():
    webbrowser.open("http://127.0.0.1:6543")


if __name__ == '__main__':
    app = main({})

    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.start()

    server = make_server('0.0.0.0', 6543, app)
    print("Starting CBSD Emulator server on http://127.0.0.1:6543")
    open_browser()
    server.serve_forever()

# PyInstaller build command:
# venv\Scripts\pyinstaller --noconfirm --onefile --console
#   --add-data "E:\python_projects\2026-sas-app\cbsd_emul\cbsd_emul_v1_0;cbsd_emul_v1_0/"
#   --add-data "E:\python_projects\2026-sas-app\cbsd_emul\api;api/"
#   --hidden-import "pyramid_jinja2" --hidden-import "pymysql"
#   --hidden-import "pytz" --hidden-import "requests" --hidden-import "cryptography"
#   --name "cbsd_emul"
#   "E:\python_projects\2026-sas-app\cbsd_emul\main.py"
