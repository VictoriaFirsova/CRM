"""Создать/повысить ADMIN из env BOOTSTRAP_ADMIN_* при старте приложения."""
import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User

logger = logging.getLogger(__name__)


async def ensure_bootstrap_admin() -> None:
    email = (settings.BOOTSTRAP_ADMIN_EMAIL or "").strip().lower()
    password = settings.BOOTSTRAP_ADMIN_PASSWORD or ""
    if not email or not password:
        return

    full_name = (settings.BOOTSTRAP_ADMIN_NAME or "").strip() or "Administrator"

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.role = UserRole.ADMIN
            user.is_active = True
            user.hashed_password = get_password_hash(password)
            if full_name != "Administrator":
                user.full_name = full_name
            await db.commit()
            logger.info("Bootstrap: %s повышен до ADMIN", email)
            return

        db.add(
            User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        await db.commit()
        logger.info("Bootstrap: создан ADMIN %s", email)
