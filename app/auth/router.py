from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import services
from app.auth.schemas import UserSchema, ResponseTokens
from app.auth.services import authorize_user
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
            new_user = await services.add_user(
                session, user.username, user.password
            )
            await session.commit()
            return await authorize_user(new_user)
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


@router.post('/login')
async def login():
    pass


@router.get('/')
async def review_current_user():
    pass


@router.post('/refresh')
async def refresh_access_token():
    pass
