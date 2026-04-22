r"""
Set a new password for the built-in admin user (username=admin).

Usage (from the backend folder, with your venv active):
  python -m scripts.set_admin_password
  python -m scripts.set_admin_password --password "YourNewStrongPass!1"
  python -m scripts.set_admin_password --ensure-seed

If --password is omitted, a random strong password is generated and printed once.

--ensure-seed runs the full database seed first (creates admin if missing), then sets the password.

Requires DATABASE_URL in backend/.env (same as the running app).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import _async_postgres_url
from app.core.auth.models import User, PasswordHistory
from app.core.auth.service import AuthService


def _random_password(length: int = 18) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _run(new_password: str, username: str) -> None:
    url = _async_postgres_url(settings.DATABASE_URL)
    engine = create_async_engine(url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(
                f"ERROR: No user with username={username!r} found.",
                file=sys.stderr,
            )
            print(
                "Fix: run the seed once, then retry, e.g.",
                file=sys.stderr,
            )
            print(
                "  python -m scripts.seed",
                file=sys.stderr,
            )
            print(
                "  python -m scripts.set_admin_password --ensure-seed",
                file=sys.stderr,
            )
            sys.exit(1)

        hashed = AuthService.hash_password(new_password)
        user.hashed_password = hashed
        user.must_change_password = True
        user.failed_login_attempts = 0
        user.locked_until = None
        user.password_changed_at = datetime.now(timezone.utc)

        session.add(
            PasswordHistory(
                user_id=user.id,
                hashed_password=hashed,
                set_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    await engine.dispose()
    print(f"Password updated for user {username!r}. must_change_password=True (change after login).")


async def _main_async(args: argparse.Namespace) -> None:
    if args.ensure_seed:
        from scripts.seed import seed

        await seed()

    pwd = args.password
    if not pwd:
        pwd = _random_password()
        print("=" * 60, file=sys.stderr)
        print("NEW PASSWORD (copy now — not stored in plain text elsewhere):", file=sys.stderr)
        print(pwd, file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    errors = AuthService.validate_password_strength(pwd)
    if errors:
        print("ERROR: Password does not meet policy:", errors, file=sys.stderr)
        sys.exit(1)

    await _run(pwd, args.username)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset admin password in the database.")
    parser.add_argument("--username", default="admin", help="Username (default: admin)")
    parser.add_argument(
        "--password",
        default=None,
        help="New password. If omitted, a random one is generated and printed.",
    )
    parser.add_argument(
        "--ensure-seed",
        action="store_true",
        help="Run scripts.seed first (creates org, site, roles, admin if missing).",
    )
    args = parser.parse_args()

    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
