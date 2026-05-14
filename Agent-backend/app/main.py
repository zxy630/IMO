from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth as auth_router
from app.routers import user_features as user_features_router
from app.routers import wallet as wallet_router

app = FastAPI(title="Agent Backend Login Demo")

settings.AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.BASE_DIR / "uploads")), name="uploads")

app.include_router(auth_router.router)
app.include_router(user_features_router.router)
app.include_router(wallet_router.router)

@app.get("/")
def read_root():
    return {"message": "OK", "status": "running"}

