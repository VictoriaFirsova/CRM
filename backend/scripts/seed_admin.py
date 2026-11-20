"""Создать или сделать админом: python -m scripts.seed_admin email password [Имя]

Если пользователь с таким email уже есть — роль станет ADMIN, пароль обновится.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import async_session, Base, engine
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User


async def main():
    if len(sys.argv) < 3:
        print("Использование: python -m scripts.seed_admin email password [полное_имя]")
        print("Пример: python -m scripts.seed_admin you@company.ru SecretPass123 'Виктория Фирсова'")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    full_name = sys.argv[3].strip() if len(sys.argv) > 3 else "Administrator"

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.role = UserRole.ADMIN
            user.is_active = True
            user.hashed_password = get_password_hash(password)
            if full_name and full_name != "Administrator":
                user.full_name = full_name
            await db.commit()
            print(f"OK: {email} теперь ADMIN (пароль обновлён)")
            return

        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"OK: создан ADMIN {email}")


if __name__ == "__main__":
    asyncio.run(main())
