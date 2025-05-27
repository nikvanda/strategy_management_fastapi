from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.strategy.models import Strategy, Condition
from app.strategy.schemas import StrategyInput, ConditionData


async def add_strategy(
    session: AsyncSession, strategy: StrategyInput, current_user_id: int
):
    new_strategy = Strategy(
        name=strategy.name,
        description=strategy.description,
        asset_type=strategy.asset_type,
        user_id=current_user_id,
    )
    session.add(new_strategy)
    return new_strategy


async def add_conditions(
    session: AsyncSession, conditions: List[ConditionData], strategy: Strategy
):
    strategy.conditions = [
        Condition(
            indicator=condition.indicator,
            threshold=condition.threshold,
            type=condition.type,
            strategy=strategy,
        )
        for condition in conditions
    ]
    session.add(strategy)
    return strategy


async def get_user_strategies(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(Strategy)
        .where(Strategy.user_id == user_id)
        .filter(Strategy.status != 'closed')
        .options(selectinload(Strategy.conditions))
    )
    strategies = result.scalars().all()
    return strategies


async def get_single_strategy(session: AsyncSession, user_id: int, strategy_id: int):
    result = await session.execute(
        select(Strategy)
        .where(and_(Strategy.user_id == user_id, Strategy.id == strategy_id))
        .options(selectinload(Strategy.conditions))
    )

    strategy = result.scalars().first()
    return strategy
