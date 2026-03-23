import asyncio
class ClientManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientManager, cls).__new__(cls)
            cls._instance.clients = []
        return cls._instance

    def add_client(self, ws):
        self.clients.append(ws)

    def remove_client(self, ws):
        self.clients.remove(ws)

    async def send_message_to_clients(self, message):
        await asyncio.wait([client.send(message) for client in self.clients])
