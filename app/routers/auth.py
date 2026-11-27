# app/routers/auth.py
# Вход администратора с защитой от подбора пароля.

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.ratelimit import limit_login
from app.security import create_access_token

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    _: bool = Depends(limit_login),  # <-- защита от брутфорса
):
    if form_data.username != ADMIN_USERNAME or form_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}