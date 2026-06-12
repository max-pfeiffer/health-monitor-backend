import tomllib
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import v1

_pyproject = tomllib.loads(
    (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text()
)

app = FastAPI(title="Health Monitor Backend", version=_pyproject["project"]["version"])


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


app.include_router(v1.router)
