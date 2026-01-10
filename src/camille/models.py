from datetime import datetime
from enum import StrEnum
from typing import Optional

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS_BEDROCK = "aws_bedrock"
    MISTRAL_AI = "mistral_ai"


class LLMProviderCredential(Base):
    __tablename__ = "llm_provider_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("users.id"))
    provider: LLMProvider
    api_key: Mapped[str] = mapped_column(sqlalchemy.String)

    def __repr__(self) -> str:
        return f"<LLMProviderCredential(id={self.id}, provider={self.provider})>"


class MMUser(Base):
    __tablename__ = "mm_users"

    id: Mapped[int] = mapped_column(primary_key=True)

    mm_id: Mapped[str] = mapped_column(
        sqlalchemy.String, unique=True
    )  # Mattermost User ID
    created_at: Mapped[datetime] = mapped_column(sqlalchemy.DateTime)
    update_at: Mapped[datetime] = mapped_column(sqlalchemy.DateTime)
    delete_at: Mapped[Optional[datetime]] = mapped_column(
        sqlalchemy.DateTime, nullable=True
    )
    username: Mapped[str] = mapped_column(sqlalchemy.String)
    nickname: Mapped[str] = mapped_column(sqlalchemy.String)
    first_name: Mapped[str] = mapped_column(sqlalchemy.String)
    last_name: Mapped[str] = mapped_column(sqlalchemy.String)

    def __repr__(self) -> str:
        return f"<MMUser(id={self.id}, mm_id={self.mm_id}, username={self.username})>"
