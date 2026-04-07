import asyncio
from fastapi import WebSocket
from source.database import Database

class Protocol(object):
    def __init__(self, database: Database):
        self.db = database
        self.actives: dict[int, WebSocket] = {} # id: websocket
    
    async def handle_connection(self, user_id: int, socket: WebSocket):
        if user_id in self.actives: # No pueden haber mas de dos conexiones simultáneas
            return False
        self.actives[user_id] = socket
        await socket.accept()
        return True
    
    async def handle_disconnection(self, user_id: int):
        if user_id in self.actives:
            del self.actives[user_id]

    async def broadcast(self, channel_id: int, data: dict):
        participants = self.db.get_channel_participants(channel_id)

        tasks = []
        p_ids = []

        for participant in participants:
            p_id = participant["id"]
            if p_id in self.actives:
                socket = self.actives[p_id]
                p_ids.append(p_id)
                tasks.append(socket.send_json(data))
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for p_id, result in zip(p_ids, results):
                if isinstance(result, Exception):
                    await self.handle_disconnection(p_id)
