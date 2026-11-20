from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.repositories.user import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.user_admin import UserCreateAdmin, UserUpdateAdmin
from app.services.users import UserAdminService

router = APIRouter(prefix="/users", tags=["users"])


def _service(db: DbSession) -> UserAdminService:
    return UserAdminService(UserRepository(db))


@router.get("", response_model=list[UserResponse])
async def list_users(current_user: CurrentUser, db: DbSession):
    return await _service(db).list_users(current_user)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreateAdmin, current_user: CurrentUser, db: DbSession):
    return await _service(db).create_user(current_user, data, db)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, data: UserUpdateAdmin, current_user: CurrentUser, db: DbSession
):
    return await _service(db).update_user(current_user, user_id, data, db)
