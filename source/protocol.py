import asyncio, time
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

    async def broadcast(self, sender_id: int, channel_id: int, message: str, username: str):
        participants = self.db.get_channel_participants(channel_id)

        if not sender_id in participants: return
        if not sender_id in self.actives: return

        tasks = []
        p_ids = []

        payload = {
            "type": "message",
            "channel_id": channel_id,
            "sender_id": sender_id,
            "sender_name": username, 
            "timestamp": time.time(),
            "content": message
        }

        for participant in participants:
            p_id = participant["id"]
            if p_id in self.actives and p_id != sender_id:
                socket = self.actives[p_id]
                p_ids.append(p_id)
                tasks.append(socket.send_json(payload))
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for p_id, result in zip(p_ids, results):
                if isinstance(result, Exception):
                    await self.handle_disconnection(p_id)
