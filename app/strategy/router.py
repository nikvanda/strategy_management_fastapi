from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from app.dependencies import CurrentUser, get_session
from app.strategy.schemas import (
    StrategyInput,
    StrategyResponse,
    HistoricalData,
    SimulationResult,
)
from app.strategy.services import (
    add_strategy,
    add_conditions,
    get_user_strategies,
    get_single_strategy,
)
from app.strategy.utils import format_strategy_response

router = APIRouter(prefix='/strategies')


@router.post('/', response_model=StrategyResponse, status_code=HTTP_201_CREATED)
async def create_strategy(
    current_user: CurrentUser,
    strategy: StrategyInput,
    session: AsyncSession = Depends(get_session),
):
    if not bool(strategy.name) or not bool(strategy.asset_type):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Name or asset_type must not be empty.",
        )
    try:
        new_strategy = await add_strategy(session, strategy, current_user.id)
        await add_conditions(session, strategy.conditions, new_strategy)
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Unpredictable error.",
        )
    return format_strategy_response(new_strategy)


@router.get('/', response_model=List[StrategyResponse], status_code=HTTP_200_OK)
async def get_all_strategies(
    current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    user_strategies = await get_user_strategies(session, current_user.id)
    response = [
        format_strategy_response(strategy) for strategy in user_strategies
    ]
    return response


@router.get(
    '/{strategy_id}', response_model=StrategyResponse, status_code=HTTP_200_OK
)
async def get_strategy(
    strategy_id,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    strategy = await get_single_strategy(session, current_user.id, strategy_id)
    return format_strategy_response(strategy)


@router.patch(
    '/{strategy_id}', response_model=StrategyResponse, status_code=HTTP_200_OK
)
async def update_strategy(
    strategy: StrategyInput,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    pass


@router.delete('/{strategy_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_strategy(
    current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    pass


@router.post(
    '/{strategy_id}/simulate',
    response_model=SimulationResult,
    status_code=HTTP_200_OK,
)
async def get_strategy(
    data: List[HistoricalData],
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    pass
