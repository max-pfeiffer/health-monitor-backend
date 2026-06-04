from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import v1

app = FastAPI(title="Health Monitor Backend")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


app.include_router(v1.router)
