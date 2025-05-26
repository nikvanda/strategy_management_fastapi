from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str


class ResponseTokens(BaseModel):
    access_token: str
    refresh_token: str
