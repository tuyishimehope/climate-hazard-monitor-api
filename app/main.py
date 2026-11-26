from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.admin.router import ADMIN_ROUTER
from app.api.v1.drought.router import DROUGHT_ROUTER
from app.api.v1.rainfall.router import RAINFALL_ROUTER
from app.core.docs import register_docs

app = FastAPI(title="disaster management system", docs_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")
register_docs(app)

app.include_router(RAINFALL_ROUTER)
app.include_router(DROUGHT_ROUTER)
app.include_router(ADMIN_ROUTER)


@app.get("/")
def start() -> str:
    return "Starting..."
