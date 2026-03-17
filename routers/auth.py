import os
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
templates_path = os.path.join(PARENT_DIR, "templates")
templates = Jinja2Templates(directory=templates_path)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str, db: db_dependency):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    return user

def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get("sub")
        user_id = payload.get("id")
        user_role = payload.get("role")
        if username is None or user_id is None or user_role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or ID is invalid")
        return {"username": username, "id": user_id, "role": user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")

@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        phone_number=create_user_request.phone_number
    )

    db.add(user)
    db.commit()

@router.post("/token", status_code=status.HTTP_200_OK, response_model=Token)
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}

