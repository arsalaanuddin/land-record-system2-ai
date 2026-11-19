"""FastAPI application for the Telangana land record digitisation system."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.documents import router as documents_router
from .api.meta import router as meta_router
from .database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001 - required signature
    init_db()
    yield


app = FastAPI(
    title="Land Record Digitization and Validation API",
    version="2.0.0",
    description=(
        "Telangana v1. Extraction output is rule-based until trained models are "
        "available; unreadable or missing values are returned as null."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router)
app.include_router(documents_router)
