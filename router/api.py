from jose import jwt
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from source.dependencies import get_db, get_autenticated_user, server_config
from source.basemodels import LoginData, RegisterData
from source.database import Database
import datetime

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