import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from source.config import Config
import pathlib, uvicorn

SERVER_PATH = pathlib.Path(__file__).resolve().parent
server_config = Config(SERVER_PATH, "server.json")
database_config = Config(SERVER_PATH, "database.json")
app = FastAPI()

# Setup inicial de la configuracion del servidor
if not "port" in server_config.data: server_config.set_key("port", 80)
if not "host" in server_config.data: server_config.set_key("host", "0.0.0.0")
if not "workers" in server_config.data: server_config.set_key("workers", 4)
if not "secret" in server_config.data: server_config.set_key("secret", "secret")
if not "reload" in server_config.data: server_config.set_key("reload", False)

# Setup inicial de la configuracion de la base de datos
if not "host" in database_config.data: database_config.set_key("host", "127.0.0.1")
if not "user" in database_config.data: database_config.set_key("user", "root")
if not "password" in database_config.data: database_config.set_key("password", "password")
if not "database" in database_config.data: database_config.set_key("database", "database")

# Añadir routers
from router.pages import pages
from router.api import api
from router.websocket import websocket

app.include_router(pages)
app.include_router(api)
app.include_router(websocket)

# Añadir handlers
@app.exception_handler(403)
async def error_403(request: Request, exc: Exception):
    return RedirectResponse("/access")

if __name__ == "__main__":
    uvicorn.run("main:app",
        host=server_config.get_key("host"),
        port=server_config.get_key("port"),
        workers=server_config.get_key("workers"),
        reload=server_config.get_key("reload")
    )