from datetime import timedelta, datetime
from functools import partial

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings


async def create_token(
    expires_delta: int,
    data: dict,
) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.now().replace(tzinfo=None) + timedelta(
            minutes=expires_delta
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except jwt.ExpiredSignatureError:
        print("Error: JWT token expired.")
        raise
    except jwt.PyJWTError as e:
        print(f"Error creating JWT: {e}")
        raise


create_access_token = partial(
    create_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES
)
create_refresh_token = partial(
    create_token, settings.REFRESH_TOKEN_EXPIRE_MINUTES
)

async def get_user_by_username( session: AsyncSession, username: str) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalars().first()
    return user


async def add_user(session: AsyncSession, username: str, password: str):
    new_user = User(username, password)
    session.add(new_user)
    return new_user


async def authorize_user(username: str):
    access_token = await create_access_token(data={"sub": username})
    refresh_token = await create_refresh_token(data={"sub": username})
    return {'access_token': access_token, 'refresh_token': refresh_token}
