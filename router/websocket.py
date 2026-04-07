from fastapi import APIRouter, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect, WebSocketException
from source.dependencies import get_db, get_autenticated_user_websocket, Database, Protocol, get_protocol

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
                    sender_id=user["id"],
                    channel_id=channel_id,
                    message=content,
                    username=user["name"]
                )

    except (WebSocketDisconnect, WebSocketException):
        await protocol.handle_disconnection(user["id"])