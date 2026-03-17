from http import HTTPStatus
from typing import Annotated
from fastapi import Depends, Path, HTTPException, APIRouter
from pydantic import BaseModel, Field
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import markdown
from bs4 import BeautifulSoup
from models import Todo
from database import SessionLocal
from sqlalchemy.orm import Session
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["Todos"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
templates_path = os.path.join(PARENT_DIR, "templates")
templates = Jinja2Templates(directory=templates_path)

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3)
    priority: int = Field(gt=0,lt=6)
    completed: bool = Field(default=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response

@router.get("/todo-page")
def render_todo_page(request: Request, db: db_dependency):
    try:
        user = get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todo).filter(Todo.owner_id == user.get("id")).all()
        return templates.TemplateResponse("todo.html", {"request": request, "todos": todos, "user": user})
    except:
        return redirect_to_login()

@router.get("/add-todo-page")
def render_add_todo_page(request: Request):
    try:
        user = get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}", status_code=status.HTTP_200_OK)
def render_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})
    except:
        return redirect_to_login()


@router.get("/")
def read_all(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return db.query(Todo).filter(Todo.owner_id == user.get("id")).all()

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
def read_todo_by_id(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("id")).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Todo not found")

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    todo = Todo(**todo_request.model_dump(), owner_id=user.get("id"))
    todo.description = create_todo_description_with_gemini(todo.description)
    db.add(todo)
    db.commit()

@router.put("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("id")).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.completed = todo_request.completed

    db.add(todo)
    db.commit()

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get("id")).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    db.delete(todo)
    db.commit()

def markdown_to_text(markdown_str):
    html = markdown.markdown(markdown_str)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text


def create_todo_description_with_gemini(todo_desc: str):
    load_dotenv()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    response = llm.invoke(
        [
            HumanMessage(content="I will provide you a todo item to add my todo list. What I want you to do is create a longer and more comprehensive description of that todo item, my next message will be my todo: "),
            HumanMessage(content=todo_desc),
        ]
    )

    return markdown_to_text(response.content)