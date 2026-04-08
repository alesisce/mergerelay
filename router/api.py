from jose import jwt
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from source.dependencies import get_db, get_autenticated_user, server_config, get_protocol, Protocol
from source.basemodels import LoginData, RegisterData, CreateChannel
from fastapi.responses import JSONResponse
from source.database import Database
import datetime, time

api = APIRouter(prefix="/api", tags=["api"])

@api.post("/login")
async def login(data: LoginData, db: Database = Depends(get_db)):
    user_id = db.verify_user_login(data.username, data.password)
    
    if not user_id:
        raise HTTPException(detail="Invalid credentials", status_code=403)
    
    to_encode = {
        "sub": str(user_id),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    token = jwt.encode(to_encode, server_config.get_key("secret"), algorithm="HS256")
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400
    )
    return response

@api.post("/register")
async def register(data: RegisterData, db: Database = Depends(get_db)):
    user_id = db.create_user(name=data.username, password=data.password)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="The user already exists.")
        
    return {"message": "Registered. You can now login.", "id": user_id}

@api.post("/create_channel")
async def create_channel(data: CreateChannel, db: Database = Depends(get_db), user: dict = Depends(get_autenticated_user)):
    channel_id = db.create_channel(data.channel_name, data.channel_description)
    
    if not channel_id:
        return JSONResponse({
            "message": "Channel not created, name already in use or something else happend." # No se que poner bro
        }, status_code=400)

    joined_status = db.add_channel_participant(channel_id, user["id"], "owner")
    if not joined_status:
        db.delete_channel(channel_id)
        return JSONResponse({
            "message": "Channel not created, internal error."
        }, status_code=500)
    
    return JSONResponse({
        "message": "Created."
    })

@api.delete("/delete_channel/{id}")
async def delete_channel(id: int, db: Database = Depends(get_db), user: dict = Depends(get_autenticated_user)):
    channel = db.get_channel_by_id(id)
    if not channel:
        return JSONResponse({
            "message": "Can't delete. There is no channel."
        })
    
    role = db.get_user_role(id, user["id"])
    if role != "owner":
        return JSONResponse({
            "message": "Permission denied."
        }, status_code=403)

    db.delete_channel(id)

@api.post("/leave_channel/{id}")
async def leave_channel(id: int, db: Database = Depends(get_db), user: dict = Depends(get_autenticated_user), protocol: Protocol = Depends(get_protocol)):
    status = db.remove_channel_participant(id, user["id"])
    if not status:
        return JSONResponse({
            "message": "failed"
        }, status_code=400)

    await protocol.broadcast(id, {
        "type": "user_left",
        "timestamp": time.time(),
        "user": user["name"]
    })

    if not db.has_participants(id):
        db.delete_channel(id)

    return JSONResponse({
        "message": "ok",
    })
    
@api.post("/join_channel/{channel_name}")
async def join_channel(channel_name: str, db: Database = Depends(get_db), user: dict = Depends(get_autenticated_user), protocol: Protocol = Depends(get_protocol)):
    channel = db.get_channel_by_name(channel_name)
    if not channel:
        return JSONResponse({
            "message": "No channel with that name",
        }, status_code=404)
    
    banned = db.get_ban(channel["id"], user["id"])
    if banned:
        return JSONResponse({
            "banned": True,
            "reason": banned["reason"]
        }, status_code=403)

    joined_status = db.add_channel_participant(channel["id"], user["id"])
    if not joined_status:
        return JSONResponse({
            "message": "failed"
        }, status_code=400)
    
    await protocol.broadcast(channel["id"], {
        "type": "user_joined",
        "timestamp": time.time(),
        "user": user["name"]
    })

    return JSONResponse({
        "message": "ok",
    })


@api.get("/channel/{channel_id}/participants")
async def get_channel_participants(
    channel_id: int,
    db: Database = Depends(get_db),
    user: dict = Depends(get_autenticated_user)
):
    channel = db.get_channel_by_id(channel_id)

    if not channel:
        return JSONResponse({"message": "channel not found"}, status_code=404)

    if not db.is_channel_participant(channel_id, user["id"]):
        return JSONResponse({"message": "not in channel"}, status_code=403)

    participants = db.get_channel_participants(channel_id)
    return JSONResponse({
        "participants": participants
    })

