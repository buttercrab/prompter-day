# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring

from fastapi import APIRouter

from . import login, session
from .db import Database

router = APIRouter()
router.include_router(login.router)
router.include_router(session.router)


@router.on_event("startup")
async def startup() -> None:
    await Database.init()


@router.on_event("shutdown")
async def shutdown() -> None:
    await Database.deinit()
