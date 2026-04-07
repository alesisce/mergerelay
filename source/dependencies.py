from source.database import Database
from source.config import Config
from source.protocol import Protocol
from fastapi import Request, HTTPException, WebSocket
from jose import jwt, JWTError
from pathlib import Path

database_config = Config(Path(__file__).resolve().parent.parent, "database.json")
server_config = Config(Path(__file__).resolve().parent.parent, "server.json")
db = Database(
    host=database_config.get_key("host"),
    user=database_config.get_key("user"),
    password=database_config.get_key("password"),
    database=database_config.get_key("database")
)
protocol = Protocol(db)

def get_db() -> Database: return db
def get_protocol() -> Protocol: return protocol

def get_autenticated_user(request: Request):
    token = request.cookies.get("token")
    if not token: raise HTTPException(detail="Unauthorized", status_code=403)

    try:
        payload = jwt.decode(token, server_config.get_key("secret"), algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(detail="Unauthorized", status_code=403)
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(detail="Unauthorized", status_code=403)
        return user_data
    except JWTError:
        raise HTTPException(detail="Unauthorized", status_code=403)
    
def get_autenticated_user_websocket(ws: WebSocket):
    token = ws.cookies.get("token")
    if not token: raise HTTPException(detail="Unauthorized", status_code=403)

    try:
        payload = jwt.decode(token, server_config.get_key("secret"), algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(detail="Unauthorized", status_code=403)
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(detail="Unauthorized", status_code=403)
        return user_data
    except JWTError:
        raise HTTPException(detail="Unauthorized", status_code=403)