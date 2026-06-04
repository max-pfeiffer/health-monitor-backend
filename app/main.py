from fastapi import FastAPI

from app.routers import blood_glucose, blood_pressure, ketones

app = FastAPI(title="Health Monitor Backend")

app.include_router(blood_pressure.router)
app.include_router(blood_glucose.router)
app.include_router(ketones.router)
