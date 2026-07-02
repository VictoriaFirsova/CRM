from app.models.enums import UserRole
from app.models.user import User


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def is_viewer(user: User) -> bool:
    return user.role == UserRole.VIEWER


def can_edit_client(user: User, owner_id: int) -> bool:
    if is_admin(user):
        return True
    if is_viewer(user):
        return False
    return user.id == owner_id


def can_edit_contract(user: User, owner_id: int, responsible_manager_id: int) -> bool:
    if is_admin(user):
        return True
    if is_viewer(user):
        return False
    return user.id == owner_id or user.id == responsible_manager_id
