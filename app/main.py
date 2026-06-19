import tomllib
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.diagrams.base import configure_global_style
from app.routers import v1

_pyproject = tomllib.loads(
    (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text()
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Apply global matplotlib/seaborn styling once, instead of on every request.
    configure_global_style()
    yield


app = FastAPI(
    title="Health Monitor Backend",
    version=_pyproject["project"]["version"],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


app.include_router(v1.router)
