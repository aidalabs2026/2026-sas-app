import sys
from wsgiref.simple_server import make_server

from aiohttp import web
import asyncio
import websockets
import threading

from esc_emul_std_alone_v1_0 import main
from websocket.ClientManager import ClientManager

sys.path.append('.')

client_manager = ClientManager()

clients = set()

async def websocket_handler(websocket, path):
    client_manager.add_client(websocket)
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            # 모든 클라이언트에게 에코 메시지 전송
            for client in clients:
                if client != websocket:  # 자신에게는 보내지 않음
                    await client.send(f"Echo: {message}")
    finally:
        client_manager.remove_client(websocket)

def start_websocket_server():
    # 새로운 이벤트 루프 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  # 현재 스레드에 이벤트 루프 설정
    start_server = websockets.serve(websocket_handler, "localhost", 8766)

    loop.run_until_complete(start_server)
    print("WebSocket server started on ws://localhost:8765")
    loop.run_forever()

if __name__ == '__main__':
    app = main({})
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.start()

    server = make_server('0.0.0.0', 6544, app)
    print("Starting ESC Emulator server on http://127.0.0.1:6544")
    server.serve_forever()

"""
if __name__ == '__main__':
    #app = main({})

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
"""