from pydantic import BaseModel

class LoginData(BaseModel):
    username: str
    password: str

class RegisterData(BaseModel):
    username: str
    password: str

class CreateChannel(BaseModel):
    channel_name: str
    channel_description: str