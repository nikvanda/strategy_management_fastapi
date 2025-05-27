from abc import ABC

from app.models import Base


class ServiceFactory(ABC):
    model: Base
