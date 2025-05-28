import json
from typing import List

import aio_pika
import pandas as pd
from aio_pika import RobustChannel
from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from app.dependencies import (
    CurrentUser,
    get_session,
    get_redis,
    QUEUE_NAME,
    get_rabbitmq_channel,
)
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
    SimulationService, SingleStrategyService,
)
from app.strategy.utils import StrategyFormatter, RedisUtils

router = APIRouter(prefix='/strategies')


@router.post('/', response_model=StrategyResponse, status_code=HTTP_201_CREATED)
async def create_strategy(
        current_user: CurrentUser,
        strategy: StrategyInput,
        session: AsyncSession = Depends(get_session),
        redis: Redis = Depends(get_redis),
        channel: RobustChannel = Depends(get_rabbitmq_channel),
):
    if not bool(strategy.name) or not bool(strategy.asset_type):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Name or asset_type must not be empty.",
        )
    try:
        strategy_service = StrategyService(session)
        new_strategy = await strategy_service.add_strategy(strategy, current_user.id)
        if strategy.conditions:
            condition_service = ConditionService(session)
            await condition_service.add_conditions(strategy.conditions, new_strategy)
        else:
            new_strategy.conditions = []
        await redis.delete(RedisUtils.get_strategy_cached_name(current_user.id))
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(
                f'User {current_user.username} created strategy {new_strategy.name}'
            ).encode()
        ),
        routing_key=QUEUE_NAME,
    )
    return StrategyFormatter.format_strategy_response(new_strategy)


@router.get('/', response_model=List[StrategyResponse], status_code=HTTP_200_OK)
async def get_all_strategies(
        current_user: CurrentUser,
        session: AsyncSession = Depends(get_session),
        redis: Redis = Depends(get_redis),
):
    cached_value = await redis.get(
        RedisUtils.get_strategy_cached_name(current_user.id)
    )
    if cached_value:
        return json.loads(cached_value)

    strategy_service = StrategyService(session)
    user_strategies = await strategy_service.get_user_strategies(current_user.id)

    response = [
        StrategyFormatter.format_strategy_response(strategy)
        for strategy in user_strategies
    ]
    await redis.set(
        RedisUtils.get_strategy_cached_name(current_user.id),
        json.dumps([st.to_dict() for st in user_strategies]),
    )

    return response


@router.get(
    '/{strategy_id}', response_model=StrategyResponse, status_code=HTTP_200_OK
)
async def get_strategy(
        strategy_id,
        current_user: CurrentUser,
        session: AsyncSession = Depends(get_session),
):
    strategy_service = StrategyService(session)
    strategy = await strategy_service.get_single_strategy(current_user.id, strategy_id)
    return StrategyFormatter.format_strategy_response(strategy)


@router.patch(
    '/{strategy_id}', response_model=StrategyResponse, status_code=HTTP_200_OK
)
async def update_strategy(
        strategy_id,
        strategy_input: StrategyInputOptional,
        current_user: CurrentUser,
        session: AsyncSession = Depends(get_session),
        redis: Redis = Depends(get_redis),
        channel: aio_pika.RobustChannel = Depends(get_rabbitmq_channel),
):
    strategy_service = SingleStrategyService(session, strategy_id=strategy_id, user_id=current_user.id)
    try:
        strategy = await strategy_service.update(strategy_input)
        await session.commit()
        await session.refresh(strategy)
        await redis.delete(RedisUtils.get_strategy_cached_name(current_user.id))
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    f'User {current_user.username} updated strategy {strategy.name}'
                ).encode()
            ),
            routing_key=QUEUE_NAME,
        )
        return StrategyFormatter.format_strategy_response(strategy)
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
        redis: Redis = Depends(get_redis),
):
    strategy_service = SingleStrategyService(session, strategy_id=strategy_id, user_id=current_user.id)
    try:
        await strategy_service.delete()
        await session.commit()
        await redis.delete(RedisUtils.get_strategy_cached_name(current_user.id))
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
    strategy_service = SimulationService(session, strategy_id=strategy_id, user_id=current_user.id)

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
        result = await strategy_service.simulate_strategy(df)
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
