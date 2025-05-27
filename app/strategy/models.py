from typing import Optional

from sqlalchemy import String, Numeric, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.models import Base

CONDITION_TYPES = ['buy_conditions', 'sell_conditions']

class Condition(Base):
    __tablename__ = 'condition'

    id: Mapped[int] = mapped_column(primary_key=True)
    indicator: Mapped[str] = mapped_column(String(100), nullable=False)
    threshold: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum(*CONDITION_TYPES, name='action_type_enum'),
        nullable=False,
    )

    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategy.id"), nullable=False
    )

    strategy: Mapped["Strategy"] = relationship(
        "Strategy", backref=backref("conditions", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return self.indicator

STATUS_TYPES = ["active", "closed", "paused"]

class Strategy(Base):
    __tablename__ = "strategy"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        String(250), nullable=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*STATUS_TYPES, name="status_type_enum"),
        default="active",
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    user: Mapped["User"] = relationship( # noqa F821
        "User", backref=backref("strategies", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f'Strategy: {self.name}'
