from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginRequest):
    return {"access_token": "demo", "token_type": "bearer"}

@router.post("/register")
def register():
    return {"ok": True}
