from typing import List, Optional

from pydantic import BaseModel


class BaseCondition(BaseModel):
    indicator: str
    threshold: float


class ConditionData(BaseCondition):
    type: str


class BaseStrategy(BaseModel):
    name: str
    description: Optional[str] | None = None
    asset_type: str
    status: str


class BaseStrategyOptional(BaseModel):
    name: str | None = None
    description: Optional[str] | None = None
    asset_type: str | None = None
    status: str | None = None


class StrategyInputOptional(BaseStrategyOptional):
    conditions: List[ConditionData] | None = None


class StrategyInput(BaseStrategy):
    conditions: List[ConditionData] | None = None


class StrategyResponse(BaseStrategy):
    buy_conditions: List[BaseCondition]
    sell_conditions: List[BaseCondition]


class HistoricalData(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float


class SimulationResult(BaseModel):
    strategy_id: int
    total_trades: int
    profit_loss: float
    win_rate: float
    max_drawdown: float
