from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from aio_pika import RobustChannel, RobustConnection, connect_robust
from fastapi import HTTPException, Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette import status
import redis.asyncio as redis

from app.auth.models import User
from app.auth.services import UserService, SingleUserService
from app.config import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

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
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    single_user_service = SingleUserService(username, session)
    user = await single_user_service.get_user()
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)


async def get_redis():
    return redis_client


RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"
QUEUE_NAME = "task_queue"


_connection: RobustConnection | None = None
_channel: RobustChannel | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _connection, _channel
    _connection = await connect_robust(RABBITMQ_URL)
    _channel = await _connection.channel()
    await _channel.declare_queue(QUEUE_NAME, durable=True)
    yield
    await _connection.close()


async def get_rabbitmq_channel() -> RobustChannel:
    if _channel is None:
        raise HTTPException(status_code=500, detail="RabbitMQ channel is not initialized")
    return _channel
