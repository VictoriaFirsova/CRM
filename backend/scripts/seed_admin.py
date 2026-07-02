"""Create admin user: python -m scripts.seed_admin"""
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
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@crm.local"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"User {email} already exists")
            return
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Administrator",
            role=UserRole.ADMIN,
        )
        db.add(user)
        await db.commit()
        print(f"Admin created: {email} / {password}")


if __name__ == "__main__":
    asyncio.run(main())
