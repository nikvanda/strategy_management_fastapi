from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exeptions import UserNotExists, IncorrectPasswordError, BaseUserException, JWTError, UsernameIsDoubleError
from app.auth.schemas import (
    UserSchema,
    ResponseTokens,
    CurrentUserSchema,
    Token,
)
from app.auth.services import AuthenticationUserService, GlobalUserService
from app.dependencies import get_session, CurrentUser, get_current_user

router = APIRouter(prefix='/auth')


@router.post(
    '/register',
    response_model=ResponseTokens,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
        user_input: UserSchema, session: AsyncSession = Depends(get_session)
):
    if user_input.username and user_input.password:
        try:
            global_user_service = GlobalUserService(session)
            await global_user_service.add_user(user_input.username, user_input.password)
            try:
                await session.commit()
            except IntegrityError:
                raise UsernameIsDoubleError()
            authentication_service = AuthenticationUserService(user_input.username, session)
            return await authentication_service.authorize_user()
        except UsernameIsDoubleError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username and password are required",
    )


@router.post(
    '/login',
    response_model=ResponseTokens,
    status_code=status.HTTP_200_OK,
)
async def login(user: UserSchema, session: AsyncSession = Depends(get_session)):
    try:
        user_service = AuthenticationUserService(user.username, session)
        db_user = await user_service.get_user()
    except UserNotExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    try:
        if db_user.check_password(user.password):
            tokens = await user_service.authorize_user()
            return tokens
        raise IncorrectPasswordError
    except IncorrectPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    '/me',
    response_model=CurrentUserSchema,
    status_code=status.HTTP_200_OK,
)
async def review_current_user(current_user: CurrentUser):
    return current_user


@router.post(
    '/refresh',
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
async def refresh_access_token(
        token: Token, session: AsyncSession = Depends(get_session)
):
    try:
        user = await get_current_user(token.token, session)
        authentication_service = AuthenticationUserService(user.username, session)
        access_token = await authentication_service.create_access_token()
        return Token(token=access_token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
