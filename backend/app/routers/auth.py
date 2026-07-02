from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.repositories.user import UserRepository
from app.schemas.auth import RefreshRequest, TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserRegister, db: DbSession):
    service = AuthService(UserRepository(db))
    user = await service.register(data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: DbSession):
    service = AuthService(UserRepository(db))
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DbSession):
    service = AuthService(UserRepository(db))
    return await service.refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user
