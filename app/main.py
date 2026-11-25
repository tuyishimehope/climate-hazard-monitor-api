from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.docs import register_docs


app = FastAPI(title= "disaster management system", docs_url=None)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)
register_docs(app)

@app.get("")
def start():
    return "Starting..."