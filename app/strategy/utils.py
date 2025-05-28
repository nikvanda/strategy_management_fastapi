from app.strategy.exeptions import InvalidConditionData
from app.strategy.models import Strategy
from app.strategy.schemas import StrategyResponse, BaseCondition, ConditionData


class StrategyFormatter:

    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    def format_strategy_response(self) -> StrategyResponse:
        return StrategyResponse(
            name=self.strategy.name,
            description=self.strategy.description,
            asset_type=self.strategy.asset_type,
            sell_conditions=[
                BaseCondition(
                    indicator=condition.indicator, threshold=condition.threshold
                )
                for condition in self.strategy.conditions
                if condition.type == 'sell_conditions'
            ],
            buy_conditions=[
                BaseCondition(
                    indicator=condition.indicator, threshold=condition.threshold
                )
                for condition in self.strategy.conditions
                if condition.type == 'buy_conditions'
            ],
            status=self.strategy.status,
        )


class ConditionFormatter:

    def __init__(self, data: dict):
        try:
            self.indicator = data['indicator']
            self.threshold = data['threshold']
            self.type = data['type']
        except KeyError:
            raise InvalidConditionData()

    def condition_data_formatter(self):
        return ConditionData(
            indicator=self.indicator,
            threshold=self.threshold,
            type=self.type,
        )


class RedisUtils:

    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_strategy_cached_name(self):
        return f'strategies_{self.user_id}'
