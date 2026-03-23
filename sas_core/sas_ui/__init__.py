from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.renderers import render_to_response
import json
from aiohttp import web

from websocket.ClientManager import ClientManager

client_manager = ClientManager()
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 클라이언트를 목록에 추가
    client_manager.add_client(ws)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            print(f"Received message: {msg.data}")
            await ws.send_str("Server response: Message received.")
            return Response('Hello world!')
        elif msg.type == web.WSMsgType.CLOSE:
            client_manager.remove_client(ws)

            break

    return Response('Hello world!')

def hello(request):
    ws = web.WebSocketResponse()
    client_manager.add_client(ws)
    for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            print(f"Received message: {msg.data}")
            ws.send_str("Server response: Message received.")

        elif msg.type == web.WSMsgType.CLOSE:
            client_manager.remove_client(ws)
    return Response('Hello world!')

def main(global_config, **settings):
    config = Configurator(settings=settings)

    config.add_route('index', '/')
    config.add_route('msglog', '/msglog/{device_id}')
    config.add_route('msglogview', '/msglogview/{device_id}')

    config.add_route('get_data', '/get_data')
    config.add_route('update_form', '/update_form')
    config.add_route('api/cbsd_list', '/api/data')
    config.add_route('api/esc_list', '/api/esc_list')
    config.add_route('api/esc_ch_list', '/api/esc_ch_list')
    config.add_route('api/msg_list', '/api/msg_list')
    config.add_route('api/grant_list', '/api/grant_list')
    config.add_route('api/regist', '/api/regist')
    config.add_route('api/deregist', '/api/deregist')
    config.add_route('api/sensing', '/api/sensing')
    config.add_route('api/release', '/api/release')
    config.add_route('ws', '/ws')
    config.include('pyramid_jinja2')
    # 정적 파일 서빙 경로 설정
    config.add_static_view(name='static', path='app:static', cache_max_age=3600)

    #config.add_static_view(name='static', path='v2_0/static')

    config.scan('.views')
    return config.make_wsgi_app()
