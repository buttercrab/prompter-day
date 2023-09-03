# pylint: disable=invalid-name, broad-exception-raised, broad-exception-caught, too-few-public-methods
# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring


import asyncio
import datetime
import json

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from server.env import get_env


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(primary_key=True)
    password: Mapped[str]
    nickname: Mapped[str]
    profile_img: Mapped[str]

    def to_response(self) -> "UserResponse":
        return UserResponse(
            username=self.username,
            nickname=self.nickname,
            profile_img=self.profile_img,
        )


class UserForm(BaseModel):
    username: str
    password: str
    nickname: str
    profile_img: str | None

    def to_user(self) -> User:
        return User(
            username=self.username,
            password=self.password,
            nickname=self.nickname,
            profile_img=self.profile_img,
        )


class UserResponse(BaseModel):
    username: str
    nickname: str
    profile_img: str


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    session_name: Mapped[str]

    def to_response(self) -> "SessionResponse":
        return SessionResponse(
            username=self.username,
            session_id=self.id,
            session_name=self.session_name,
        )


class SessionResponse(BaseModel):
    username: str
    session_id: int
    session_name: str


class AIResponse(BaseModel):
    score: int
    recommendation: str
    knowledge: str
    code_comment: str
    code: list[dict[str, str]]


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int]
    username: Mapped[str]
    question: Mapped[str]
    score: Mapped[int]
    recommendation: Mapped[str]
    knowledge: Mapped[str]
    code_comment: Mapped[str]
    code: Mapped[str]
    timestamp: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow
    )

    def to_response(self) -> "ChatResponse":
        return ChatResponse(
            id=self.id,
            session_id=self.session_id,
            username=self.username,
            question=self.question,
            score=self.score,
            recommendation=self.recommendation,
            knowledge=self.knowledge,
            code_comment=self.code_comment,
            code=json.loads(self.code),
            timestamp=self.timestamp,
        )

    def to_ai_request(self) -> list[dict[str, str]]:
        return [
            {
                "role": "user",
                "content": self.question,
            },
            {
                "role": "assistant",
                "content": f"score: {self.score}, recommendation: {self.recommendation}, knowledge: {self.knowledge}",
            },
        ]


class ChatResponse(BaseModel):
    id: int
    session_id: int
    username: str
    question: str
    score: int
    recommendation: str
    knowledge: str
    code_comment: str
    code: list[dict[str, str]]
    timestamp: datetime.datetime


class Database:
    """
    Database class
    """

    engine: AsyncEngine | None
    async_session: async_sessionmaker[AsyncSession] | None

    @classmethod
    async def init(cls) -> None:
        """
        This initializes the database

        This should be called before using the database
        """
        if hasattr(cls, "engine") and cls.engine is not None:
            return

        username = get_env("SQL_USER")
        password = get_env("SQL_PASSWORD")
        url = get_env("SQL_HOST")
        db = get_env("SQL_DB")

        for _ in range(int(get_env("SQL_RETRY"))):
            try:
                print("Connecting to database...")
                engine = create_async_engine(
                    f"postgresql+asyncpg://{username}:{password}@{url}/{db}", echo=True
                )
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                break
            except KeyboardInterrupt as err:
                raise KeyboardInterrupt from err
            except Exception:
                print("Failed to connect to database, retrying...")
                await asyncio.sleep(5)
        else:
            raise Exception("Unable to connect to database")
        cls.engine = engine
        cls.async_session = async_sessionmaker(cls.engine, expire_on_commit=False)

    @classmethod
    async def deinit(cls) -> None:
        """
        This deinitializes the database
        """
        if hasattr(cls, "engine") and cls.engine is not None:
            await cls.engine.dispose()
