# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from .ai import ask
from .db import Database, User, Session, Chat, ChatResponse, SessionResponse
from .login import manager

router = APIRouter(prefix="/session")


@router.get("/new")
async def new_session(name: str, user: User = Depends(manager)) -> SessionResponse:
    async with Database.async_session() as session:
        res = Session(username=user.username, session_name=name)
        session.add(res)
        await session.commit()

    return res.to_response()


@router.get("/get/{session_id}")
async def get_session(
    session_id: int, user: User = Depends(manager)
) -> SessionResponse:
    async with Database.async_session() as session:
        stmt = (
            select(Session)
            .where(Session.username == user.username)
            .where(Session.id == session_id)
        )
        res = (await session.execute(stmt)).scalar()
        if not res:
            raise HTTPException(404, "Session not found")

        return res.to_response()


@router.get("/list")
async def list_session(user: User = Depends(manager)) -> dict:
    async with Database.async_session() as session:
        stmt = select(Session).where(Session.username == user.username)
        res = (await session.execute(stmt)).scalars()
        return {"sessions": [r.to_response() for r in res]}


@router.get("/delete")
async def delete_session(session_id: int, user: User = Depends(manager)) -> dict:
    async with Database.async_session() as session:
        stmt = (
            select(Session)
            .where(Session.username == user.username)
            .where(Session.id == session_id)
        )
        res = (await session.execute(stmt)).scalar()
        if not res:
            raise HTTPException(404, "Session not found")

        await session.delete(res)
        await session.commit()

    return {"status": "ok"}


@router.get("/ask")
async def ask_session(
    session_id: int, question: str, user: User = Depends(manager)
) -> ChatResponse:
    async with Database.async_session() as session:
        stmt = (
            select(Session)
            .where(Session.username == user.username)
            .where(Session.id == session_id)
        )
        res = (await session.execute(stmt)).scalar()
        if not res:
            raise HTTPException(404, "Session not found")

        answer, advice = await ask(session_id, question)
        chat = Chat(
            session_id=session_id,
            username=user.username,
            question=question,
            answer=answer,
            advice=advice,
        )
        session.add(chat)
        await session.commit()

    return chat.to_response()
