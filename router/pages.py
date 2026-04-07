from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from source.dependencies import get_db, get_autenticated_user, server_config
from jose import jwt
from datetime import datetime, timedelta
from source.database import Database

pages = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@pages.get("/")
async def index(request: Request, user: dict = Depends(get_autenticated_user), db: Database = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user["name"],
            "channels": db.get_user_channels(user["id"])
        }
    )

@pages.get("/access")
async def index(request: Request, db: Database = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="access.html",
        context={}
    )
