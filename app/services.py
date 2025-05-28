from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base


class ServiceFactory(ABC):
    model: Base

    def __init__(self, session: AsyncSession):
        self.session = session
