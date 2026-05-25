from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import models
from app.database import Base, close_db_connection, engine
from app.routers.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await close_db_connection()


app = FastAPI(
    title="alatoo-doc",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(documents_router)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"message": "Welcome to Alatoo-Doc API"}


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
