from fastapi import FastAPI, APIRouter
from app.routes import articles, suppliers, pos, auth
from app.core.config import settings

app = FastAPI(
    title="Backend/App Starter",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(pos.router, prefix="/pos", tags=["pos"])

app.include_router(api_router, prefix=settings.API_V1_STR)
