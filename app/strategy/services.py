from decimal import InvalidOperation
from typing import List

import pandas as pd
from sqlalchemy import select, and_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services import ServiceFactory
from app.strategy.exeptions import IncorrectConditionTypeError, IncorrectStatusTypesError, InvalidConditionData, \
    InvalidStrategyField, StrategyNotExistError, InvalidConditionDataStructureError, \
    ConditionFailToCreateError
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


class ConditionService(ServiceFactory):
    model = Condition

    async def add_conditions(
            self,
            conditions: List[ConditionData],
            strategy: Strategy,
    ):
        try:
            new_conditions = []
            for condition in conditions:
                if condition.type not in CONDITION_TYPES:
                    raise IncorrectConditionTypeError()

                try:
                    new_conditions.append(
                        self.model(
                            indicator=condition.indicator,
                            threshold=condition.threshold,
                            type=condition.type,
                            strategy=strategy,
                        )
                    )
                except IntegrityError:
                    raise ConditionFailToCreateError(condition_data=condition)

            strategy.conditions = new_conditions
            self.session.add(strategy)
            return strategy
        except IncorrectConditionTypeError as e:
            raise e

    async def delete(self, conditions: list[int] | list[Condition]):
        try:
            if not conditions:
                return

            if isinstance(conditions[0], int):
                await self.session.execute(
                    delete(Strategy).where(Strategy.id.in_(conditions))
                )
                return

            if isinstance(conditions[0], Condition):
                for condition in conditions:
                    await self.session.delete(condition)
                return

            raise InvalidConditionDataStructureError(structure_type=str(type(conditions)))

        except InvalidConditionDataStructureError as e:
            raise e


class StrategyService(ServiceFactory):
    model = Strategy

    async def get_single_strategy(self, user_id: int, strategy_id: int | str) -> Strategy:
        try:
            result = await self.session.execute(
                select(self.model)
                .where(
                    and_(self.model.user_id == user_id, self.model.id == int(strategy_id))
                )
                .options(selectinload(self.model.conditions))
            )

            strategy = result.scalars().first()
            if strategy is None:
                raise StrategyNotExistError()
            return strategy
        except StrategyNotExistError as e:
            raise e

    async def get_user_strategies(self, user_id: int):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .filter(self.model.status != 'closed')
            .options(selectinload(self.model.conditions))
        )
        strategies = result.scalars().all()
        return strategies

    async def add_strategy(
            self,
            strategy: StrategyInput,
            current_user_id: int,
    ):
        new_strategy = self.model(
            name=strategy.name,
            description=strategy.description,
            asset_type=strategy.asset_type,
            user_id=current_user_id,
        )
        self.session.add(new_strategy)
        return new_strategy


class SingleStrategyService(StrategyService):

    def __init__(self, session: AsyncSession,
                 strategy: Strategy | None = None,
                 strategy_id: int | None = None,
                 user_id: int | None = None):
        super().__init__(session)
        self.strategy_id = strategy_id
        self.user_id = user_id

        self._strategy = strategy if strategy else None
        self.condition_service = ConditionService(session) if strategy or (strategy_id and user_id) else None

    async def get_instance(self):
        try:
            return self._strategy if self._strategy else await self.get_single_strategy(self.user_id, self.strategy_id)
        except StrategyNotExistError as e:
            raise e

    async def update(self, strategy_input: StrategyInputOptional):
        try:
            strategy = await self.get_instance()
            for key, value in strategy_input.model_dump(exclude_unset=True).items():
                if key == 'conditions':
                    await self.condition_service.delete(strategy.conditions)
                    formatted_value = [
                        ConditionFormatter(item).condition_data_formatter()
                        for item in value
                    ]
                    await self.condition_service.add_conditions(formatted_value, strategy)
                    continue
                if key == 'status':
                    if value not in STATUS_TYPES:
                        raise IncorrectStatusTypesError()

                if hasattr(strategy, key) is False:
                    raise InvalidStrategyField(key)

                setattr(strategy, key, value)

            return strategy
        except (InvalidConditionData, IncorrectStatusTypesError, InvalidStrategyField,
                InvalidConditionDataStructureError) as e:
            raise e

    async def delete(self):
        try:
            strategy = await self.get_instance()
            if strategy is None:
                raise StrategyNotExistError()
            await self.session.delete(strategy)
        except StrategyNotExistError as e:
            raise e


class SimulationService(SingleStrategyService):

    async def simulate_strategy(self,
                                df: pd.DataFrame, indicator: str = 'momentum'
                                ):
        balance, position, entry_price = 0, 0, 0
        trades = []

        try:
            strategy = await self.get_instance()
        except StrategyNotExistError as e:
            raise e
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
            momentum = float(row[indicator])
            close_price = float(row['close'])
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
