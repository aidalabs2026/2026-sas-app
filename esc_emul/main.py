import webbrowser
import asyncio
import threading
from wsgiref.simple_server import make_server

from esc_emul_v1_0 import main
from esc_emul_v1_0.websocket.ClientManager import ClientManager

client_manager = ClientManager()

clients = set()


def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("WebSocket server started on ws://localhost:8766")
    loop.run_forever()


def open_browser():
    webbrowser.open("http://127.0.0.1:6544")


if __name__ == '__main__':
    app = main({})
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.start()

    server = make_server('0.0.0.0', 6544, app)
    print("Starting ESC Emulator server on http://127.0.0.1:6544")
    open_browser()
    server.serve_forever()

# PyInstaller build command:
# venv\Scripts\pyinstaller --noconfirm --onefile --console
#   --add-data "E:\python_projects\2026-sas-app\esc_emul\esc_emul_v1_0;esc_emul_v1_0/"
#   --add-data "E:\python_projects\2026-sas-app\esc_emul\api;api/"
#   --hidden-import "pyramid_jinja2" --hidden-import "pymysql"
#   --hidden-import "pytz" --hidden-import "requests" --hidden-import "cryptography"
#   --name "esc_emul"
#   "E:\python_projects\2026-sas-app\esc_emul\main.py"
