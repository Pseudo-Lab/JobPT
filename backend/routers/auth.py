from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from db.database import get_db
from db.models import User
from pydantic import BaseModel
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # token이 하루동안 유지됨

# Password hashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_password_hash(password: str) -> str:
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Router
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# Request/Response models
class SignupRequest(BaseModel):
    user_id: str
    password: str

class SignupResponse(BaseModel):
    id: int
    user_id: str
    message: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Signup endpoint
@router.post("/sign-up", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    회원가입 API
    - user_id: 로그인에 사용할 ID
    - password: 로그인에 사용할 비밀번호 (bcrypt로 해싱됨)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.user_id == request.user_id).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        user_id=request.user_id,
        password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return SignupResponse(
        id=new_user.id,
        user_id=new_user.user_id,
        message="User created successfully"
    )

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    로그인 API
    - username: user_id
    - password: password
    """
    user = db.query(User).filter(User.user_id == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
