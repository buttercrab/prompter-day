# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring

import logging

import dotenv
from fastapi import FastAPI

from .v1 import login, session

app = FastAPI()
app.include_router(v1.router, prefix="/api")
app.include_router(v1.router, prefix="/api/v1")
dotenv.load_dotenv()


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/api/healthy") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


@app.get("/api/healthy")
async def healthy() -> dict:
    return {"status": "ok"}
