from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import services
from app.auth.schemas import UserSchema, ResponseTokens
from app.auth.services import authorize_user, get_user_by_username
from app.dependencies import get_session

router = APIRouter(prefix='/auth')


@router.post(
    '/register',
    response_model=ResponseTokens,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserSchema, session: AsyncSession = Depends(get_session)
):
    if user.username and user.password:
        try:
            await services.add_user(session, user.username, user.password)
            await session.commit()
            return await authorize_user(user.username)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username has already taken",
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
    db_user = (
        await get_user_by_username(session, user.username)
        if user.username
        else None
    )
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No such a user.",
        )
    if db_user.check_password(user.password):
        tokens = await authorize_user(user.username)
        return tokens
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect password.",
    )


@router.get('/')
async def review_current_user():
    pass


@router.post('/refresh')
async def refresh_access_token():
    pass
