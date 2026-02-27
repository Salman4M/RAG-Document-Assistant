from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime,timedelta

from core.security import get_current_user
from models.user import User

from core.database import get_db
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from core.config import settings 
from models.user import User, RefreshToken
from schemas.user import UserRegister,UserResponse,UserLogin,TokenResponse


router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/register",response_model=UserResponse,status_code=201)
async def register(data: UserRegister, db:AsyncSession = Depends(get_db)):
    #username check
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    #email check
    result = await db.execute(select(User).where(User.email==data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login",response_model=TokenResponse)
async def login(form_data:OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username==form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=201,detail="Invail credenticals")
    
    access_token = create_access_token({"sub":str(user.id)})
    refresh_token = create_refresh_token({"sub":str(user.id)})

    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    ))
    await db.commit()

    return TokenResponse(access_token=access_token,refresh_token=refresh_token)


@router.post("/refresh",response_model=TokenResponse)
async def refresh(refresh_token: str, db:AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") !="refresh":
        raise HTTPException(status_code=401, detail="Invaild refresh token")
    
    result = await db.execute(select(RefreshToken).where(RefreshToken.token==refresh_token))
    token_record = result.scalar_one_or_none()

    if not token_record or token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401,detail ="Refresh token expired or not found")

    user_id = payload.get("sub")
    #delete old token
    await db.delete(token_record)
    #new tokens
    access_token = create_access_token({"sub":user_id})
    new_refresh_token = create_refresh_token({"sub":user_id})

    #store new tokens
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(
        token=new_refresh_token,
        user_id=int(user_id),
        expires_at=expires_at
    ))
    await db.commit()
    
    return TokenResponse(access_token = access_token, refresh_token=new_refresh_token)
    
    
@router.post("/logout")
async def logout(
    refresh_token: str,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token==refresh_token))
    token_record = result.scalar_one_or_none()

    if token_record:
        await db.delete(token_record)
        await db.commit()

    return {"message":"Logged out successfully"}



@router.get("/me",response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user