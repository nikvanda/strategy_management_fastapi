from app.strategy.models import Strategy
from app.strategy.schemas import StrategyResponse, BaseCondition, ConditionData


def format_strategy_response(strategy: Strategy) -> StrategyResponse:
    return StrategyResponse(
        name=strategy.name,
        description=strategy.description,
        asset_type=strategy.asset_type,
        sell_conditions=[
            BaseCondition(
                indicator=condition.indicator, threshold=condition.threshold
            )
            for condition in strategy.conditions
            if condition.type == 'sell_conditions'
        ],
        buy_conditions=[
            BaseCondition(
                indicator=condition.indicator, threshold=condition.threshold
            )
            for condition in strategy.conditions
            if condition.type == 'buy_conditions'
        ],
        status=strategy.status,
    )


class ConditionFormatter:

    @staticmethod
    def condition_data_formatter(data: dict):
        return ConditionData(
            indicator=data['indicator'],
            threshold=data['threshold'],
            type=data['type'],
        )
