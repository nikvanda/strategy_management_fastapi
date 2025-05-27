from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from aio_pika import connect_robust
from fastapi import HTTPException, Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette import status
import redis.asyncio as redis

from app.auth.models import User
from app.auth.services import UserService
from app.config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    if settings.DEBUG == 0
    else 'sqlite+aiosqlite:///../mydb.sqlite3'
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await UserService.get_user_by_username(session, username)
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

async def get_redis():
    return redis_client

RABBITMQ_URL = "amqp://guest:guest@localhost/"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rabbitmq_connection = await connect_robust(RABBITMQ_URL)
    app.state.channel = await app.state.rabbitmq_connection.channel()
    await app.state.channel.declare_queue("task_queue", durable=True)
    yield
    await app.state.rabbitmq_connection.close()
