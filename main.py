from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette import status
from models import Base, Todo
from database import engine
from routers.auth import router as auth_router
from routers.todo import router as todo_router
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)

app.include_router(auth_router)
app.include_router(todo_router)

Base.metadata.create_all(bind=engine)