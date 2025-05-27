from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services import ServiceFactory
from app.strategy.models import Strategy, Condition
from app.strategy.schemas import StrategyInput, ConditionData


class StrategyService(ServiceFactory):
    model = Strategy

    @classmethod
    async def add_strategy(
        cls,
        session: AsyncSession,
        strategy: StrategyInput,
        current_user_id: int,
    ):
        new_strategy = cls.model(
            name=strategy.name,
            description=strategy.description,
            asset_type=strategy.asset_type,
            user_id=current_user_id,
        )
        session.add(new_strategy)
        return new_strategy

    @classmethod
    async def get_user_strategies(cls, session: AsyncSession, user_id: int):
        result = await session.execute(
            select(cls.model)
            .where(cls.model.user_id == user_id)
            .filter(cls.model.status != 'closed')
            .options(selectinload(cls.model.conditions))
        )
        strategies = result.scalars().all()
        return strategies

    @classmethod
    async def get_single_strategy(
        cls, session: AsyncSession, user_id: int, strategy_id: int
    ):
        result = await session.execute(
            select(cls.model)
            .where(
                and_(
                    cls.model.user_id == user_id, cls.model.id == strategy_id
                )
            )
            .options(selectinload(cls.model.conditions))
        )

        strategy = result.scalars().first()
        return strategy


class ConditionService(ServiceFactory):
    model = Condition

    @classmethod
    async def add_conditions(
        cls,
        session: AsyncSession,
        conditions: List[ConditionData],
        strategy: Strategy,
    ):
        strategy.conditions = [
            cls.model(
                indicator=condition.indicator,
                threshold=condition.threshold,
                type=condition.type,
                strategy=strategy,
            )
            for condition in conditions
        ]
        session.add(strategy)
        return strategy
