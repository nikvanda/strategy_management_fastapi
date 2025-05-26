import bcrypt
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True)
    password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)

    def __init__(self, username: str, password: str):
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        super().__init__(
            **{'username': username, 'password': pw_hash.decode('utf-8')}
        )

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'), self.password.encode('utf-8')
        )

    def __repr__(self):
        return self.username
