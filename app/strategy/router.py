from typing import List

import pandas as pd
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
    StrategyInputOptional,
)
from app.strategy.services import (
    StrategyService,
    ConditionService,
    SimulationService,
)
from app.strategy.utils import StrategyFormatter

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
        new_strategy = await StrategyService.add_strategy(
            session, strategy, current_user.id
        )
        if strategy.conditions:
            await ConditionService.add_conditions(
                session, strategy.conditions, new_strategy
            )
        else:
            new_strategy.conditions = []
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return StrategyFormatter.format_strategy_response(new_strategy)


@router.get('/', response_model=List[StrategyResponse], status_code=HTTP_200_OK)
async def get_all_strategies(
    current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    user_strategies = await StrategyService.get_user_strategies(
        session, current_user.id
    )
    response = [
        StrategyFormatter.format_strategy_response(strategy)
        for strategy in user_strategies
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
    strategy = await StrategyService.get_single_strategy(
        session, current_user.id, strategy_id
    )
    return StrategyFormatter.format_strategy_response(strategy)


@router.patch(
    '/{strategy_id}', response_model=StrategyResponse, status_code=HTTP_200_OK
)
async def update_strategy(
    strategy_id,
    strategy: StrategyInputOptional,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    strategy_db = await StrategyService.get_single_strategy(
        session, current_user.id, strategy_id
    )
    try:
        await StrategyService.update(session, strategy, strategy_db)
        await session.commit()
        await session.refresh(strategy_db)
        return StrategyFormatter.format_strategy_response(strategy_db)
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete('/{strategy_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    strategy_db = await StrategyService.get_single_strategy(
        session, current_user.id, strategy_id
    )
    try:
        await StrategyService.delete(session, strategy_db)
        await session.commit()
    except Exception as e:
        print(e)
        await session.rollback()
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail='Unpredictable error',
        )


@router.post(
    '/{strategy_id}/simulate',
    response_model=SimulationResult,
    status_code=HTTP_200_OK,
)
async def simulate_strategy(
    strategy_id,
    data: List[HistoricalData],
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    strategy_db = await StrategyService.get_single_strategy(
        session, current_user.id, strategy_id
    )

    df = pd.DataFrame([item.model_dump() for item in data])
    try:
        df['date'] = pd.to_datetime(df['date'])
    except TypeError:
        raise HTTPException(
            detail='Some of your provided data does not have date.',
            status_code=HTTP_400_BAD_REQUEST,
        )
    try:
        df['momentum'] = df['close'] - df['close'].shift(1)
    except TypeError:
        raise HTTPException(
            detail='Impossible to calculate momentum. Check provided data.',
            status_code=HTTP_400_BAD_REQUEST,
        )

    try:
        result = SimulationService.simulate_strategy(df, strategy_db)
    except TypeError:
        raise HTTPException(
            detail='Some data is in incorrect format.',
            status_code=HTTP_400_BAD_REQUEST,
        )
    except IndexError:
        raise HTTPException(
            detail='To simulate your strategy you must provide buy and sell conditions of the same type',
            status_code=HTTP_400_BAD_REQUEST,
        )

    return result
