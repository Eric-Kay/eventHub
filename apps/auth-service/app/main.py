import os
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import User
from .schemas import RegisterRequest, LoginRequest, UserOut
from app.db import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
app = FastAPI(title="auth-service")
 # Use bcrypt_sha256 to avoid the 72-byte limit on bcrypt (it pre-hashes using SHA-256)
 
pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto"
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "change-me-too")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def make_access_token(user: User):
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

def make_refresh_token(user: User):
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        },
        REFRESH_TOKEN_SECRET,
        algorithm=JWT_ALGORITHM,
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}

@app.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="email already exists")
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}

@app.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {
        "access_token": make_access_token(user),
        "refresh_token": make_refresh_token(user),
        "token_type": "bearer",
    }

@app.post("/refresh")
def refresh_token(payload: dict):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    try:
        data = jwt.decode(token, REFRESH_TOKEN_SECRET, algorithms=[JWT_ALGORITHM])
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="invalid refresh token")
        access_token = jwt.encode(
            {
                "sub": data["sub"],
                "email": data.get("email"),
                "role": data.get("role", "customer"),
                "exp": datetime.now(timezone.utc) + timedelta(hours=12),
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="invalid refresh token")

@app.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db)):
    return db.query(User).all()
