import uuid

from db.postgres import Base
from models.models_types import GenderEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "profile"}

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    profile: Mapped["Profile"] = relationship(
        "Profile", back_populates="user", uselist=False, lazy="joined", cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Profile(Base):
    __tablename__ = "profile"
    __table_args__ = {"schema": "profile"}

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profile.user.id"), primary_key=True
    )
    user: Mapped["User"] = relationship("User", back_populates="profile", uselist=False)

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[GenderEnum]
