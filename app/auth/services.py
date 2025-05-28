from datetime import timedelta, datetime

import jwt
from sqlalchemy import select

from app.auth.models import User
from app.config import settings
from app.services import ServiceFactory


class UserService(ServiceFactory):
    model = User


class SingleUserService(UserService):
    def __init__(self, username: str, *args):
        super().__init__(*args)
        self.username = username

    async def get_user(self) -> User:
        result = await self.session.execute(
            select(self.model).where(self.model.username == self.username)
        )
        user = result.scalars().first()
        return user


class AuthenticationUserService(SingleUserService):

    async def _create_token(self,
                            expires_delta: int,
                            ) -> str:
        try:
            data = {'sub': self.username}
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

    async def authorize_user(self):
        access_token = await self.create_access_token()
        refresh_token = await self.create_refresh_token()
        return {'access_token': access_token, 'refresh_token': refresh_token}

    async def create_access_token(self,
                                  expires_delta: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES):
        return await self._create_token(expires_delta)

    async def create_refresh_token(self,
                                   expires_delta: int = settings.REFRESH_TOKEN_EXPIRE_MINUTES):
        return await self._create_token(expires_delta)


class GlobalUserService(UserService):
    def __init__(self, *args):
        super().__init__(*args)

    async def add_user(
            self, username: str, password: str
    ):
        new_user = self.model(username, password)
        self.session.add(new_user)
        return new_user
