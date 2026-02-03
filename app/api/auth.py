from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.models.models import User, Restaurant
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):

    # 1️⃣ Try admin login
    admin = db.query(User).filter(User.username == payload.username).first()
    if admin and verify_password(payload.password, admin.hashed_password):
        token = create_access_token({
            "sub": admin.username,
            "role": "admin",
            "admin_id": admin.id
        })
        return {
            "access_token": token,
            "role": "admin",
            "admin_id": admin.id
        }

    # 2️⃣ Try restaurant login
    restaurant = db.query(Restaurant).filter(Restaurant.email == payload.username).first()
    if restaurant and verify_password(payload.password, restaurant.password_hash):
        token = create_access_token({
            "sub": restaurant.email,
            "role": "restaurant",
            "restaurant_id": restaurant.id
        })
        return {
            "access_token": token,
            "role": "restaurant",
            "restaurant_id": restaurant.id
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")
