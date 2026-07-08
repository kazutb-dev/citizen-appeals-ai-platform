"""Создание первого администратора. Запуск:

    python -m app.scripts.create_admin

Email и пароль запрашиваются интерактивно — никаких дефолтных учёток в коде.
"""
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.core.auth import hash_password
from app.database import async_session_factory
from app.models.user import User


async def main() -> None:
    email = input("Email администратора: ").strip()
    full_name = input("ФИО: ").strip()
    password = getpass.getpass("Пароль (мин. 12 символов): ")
    if len(password) < 12:
        print("Пароль слишком короткий", file=sys.stderr)
        sys.exit(1)

    async with async_session_factory() as db:
        existing = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if existing is not None:
            print(f"Пользователь {email} уже существует", file=sys.stderr)
            sys.exit(1)
        db.add(
            User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                role="admin",
            )
        )
        await db.commit()
    print(f"Администратор {email} создан.")


if __name__ == "__main__":
    asyncio.run(main())
