from fastapi import APIRouter, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect, WebSocketException
from source.dependencies import get_db, get_autenticated_user_websocket, Database, Protocol, get_protocol
import time

websocket = APIRouter(prefix="/chat", tags=["chat"])

@websocket.websocket("/connect")
async def websocket_handler(ws: WebSocket, user: dict = Depends(get_autenticated_user_websocket), protocol: Protocol = Depends(get_protocol)):
    await protocol.handle_connection(user["id"], ws)
    try:
        while True:
            client_response: dict = await ws.receive_json()
            type_response = client_response.get("type")

            if type_response == "send_message":
                content = client_response.get("message")
                channel_id = client_response.get("channel_id")
                await protocol.broadcast(
                    channel_id=channel_id,
                    data={
                        "type": "message",
                        "channel_id": channel_id,
                        "sender_id": user["id"],
                        "sender_name": user["name"],
                        "timestamp": time.time(),
                        "content": content
                    }
                )

    except (WebSocketDisconnect, WebSocketException):
        await protocol.handle_disconnection(user["id"])
    except Exception as e:
        print(e)