from decimal import Decimal, InvalidOperation
from typing import List

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.status import HTTP_400_BAD_REQUEST

from app.services import ServiceFactory
from app.strategy.models import (
    Strategy,
    Condition,
    STATUS_TYPES,
    CONDITION_TYPES,
)
from app.strategy.schemas import (
    StrategyInput,
    ConditionData,
    StrategyInputOptional,
)
from app.strategy.utils import ConditionFormatter


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
    async def update(
        cls,
        session: AsyncSession,
        strategy_input: StrategyInputOptional,
        strategy: Strategy,
    ):
        for key, value in strategy_input.model_dump(exclude_unset=True).items():
            if key == 'conditions':
                await ConditionService.delete(session, strategy.conditions)
                formatted_value = [
                    ConditionFormatter.condition_data_formatter(item)
                    for item in value
                ]
                await ConditionService.add_conditions(
                    session, formatted_value, strategy
                )
                continue
            if key == 'status':
                if value not in STATUS_TYPES:
                    raise ValueError('Incorrect status type.')

            setattr(strategy, key, value)

        return strategy_input

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
                and_(cls.model.user_id == user_id, cls.model.id == strategy_id)
            )
            .options(selectinload(cls.model.conditions))
        )

        strategy = result.scalars().first()
        if strategy is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="No such a strategy.",
            )
        return strategy

    @classmethod
    async def delete(cls, session: AsyncSession, strategy: Strategy):
        await session.delete(strategy)


class ConditionService(ServiceFactory):
    model = Condition

    @classmethod
    async def add_conditions(
        cls,
        session: AsyncSession,
        conditions: List[ConditionData],
        strategy: Strategy,
    ):
        new_conditions = []
        for condition in conditions:
            if condition.type not in CONDITION_TYPES:
                raise ValueError('Incorrect condition types.')

            new_conditions.append(
                cls.model(
                    indicator=condition.indicator,
                    threshold=condition.threshold,
                    type=condition.type,
                    strategy=strategy,
                )
            )

        strategy.conditions = new_conditions
        session.add(strategy)
        return strategy

    @classmethod
    async def delete(
        cls, session: AsyncSession, conditions: list[int] | list[Condition]
    ):
        if not conditions:
            return

        if isinstance(conditions[0], int):
            await session.execute(
                delete(Strategy).where(Strategy.id.in_(conditions))
            )

        if isinstance(conditions[0], Condition):
            for condition in conditions:
                await session.delete(condition)


class SimulationService:

    @staticmethod
    def simulate_strategy(
        df: pd.DataFrame, strategy: Strategy, indicator: str = 'momentum'
    ):
        balance, position, entry_price = 0, 0, 0
        trades = []

        st_dict = strategy.to_dict()
        st_dict['buy_conditions'] = list(
            filter(
                lambda x: x['indicator'] == indicator, st_dict['buy_conditions']
            )
        )[0]
        st_dict['sell_conditions'] = list(
            filter(
                lambda x: x['indicator'] == indicator,
                st_dict['sell_conditions'],
            )
        )[0]

        for index, row in df.iterrows():
            momentum = Decimal(row[indicator])
            close_price = Decimal(row['close'])
            try:
                if (
                    momentum > st_dict['buy_conditions']['threshold']
                    and position == 0
                ):
                    position = 1
                    entry_price = close_price
                    trades.append(
                        {
                            'action': 'buy',
                            'date': row['date'],
                            'price': close_price,
                        }
                    )
                elif (
                    momentum < st_dict['sell_conditions']['threshold']
                    and position == 1
                ):
                    profit = close_price - entry_price
                    balance += profit
                    position = 0
                    trades.append(
                        {
                            'action': 'sell',
                            'date': row['date'],
                            'price': close_price,
                            'profit': profit,
                        }
                    )
            except InvalidOperation:
                continue

        sell_trades = [
            trade.get('profit', 0)
            for trade in trades
            if trade['action'] == 'sell'
        ]
        max_drawdown = min(sell_trades) if sell_trades else 0

        return {
            'strategy_id': strategy.id,
            'total_trades': len(trades),
            'profit_loss': balance,
            'win_rate': (
                sum(
                    1
                    for trade in trades
                    if trade['action'] == 'sell' and trade.get('profit', 0) > 0
                )
                / len(trades)
                * 100
                if trades
                else 0
            ),
            'max_drawdown': max_drawdown,
        }
