from fastapi import FastAPI
from app.api.api_v1 import router as api_router
from app.api.auth import router as auth_router
from app.core.security import hash_password
from app.db import session
from app.db.session import SessionLocal, engine, Base
from app.core.config import settings
import os
from fastapi.middleware.cors import CORSMiddleware

from app.models.models import User

app = FastAPI(title="Restaurant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",     # Vite
        "http://localhost:3000",     # React (CRA)
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
         "file://",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router)


# Ensure uploads dir
os.makedirs(settings.IMAGE_UPLOAD_DIR, exist_ok=True)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    db: session = SessionLocal()
    try:
        admin = (
            db.query(User)
            .filter(User.username == settings.ADMIN_USERNAME)
            .first()
        )

        if not admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            print(
                f"✅ Admin created (username={settings.ADMIN_USERNAME})"
            )
        else:
            print("ℹ️ Admin already exists")

    finally:
        db.close()

