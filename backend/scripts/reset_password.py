"""One-off admin password reset.

Usage:
    .venv/bin/python -m scripts.reset_password <email> <new_password>

Resets:
  - password_hash (Argon2 via app.core.security.get_password_hash)
  - password_changed_at = now
  - password_expires_at = now + PASSWORD_EXPIRY_DAYS (renews the 90-day clock)
  - failed_login_attempts = 0
  - locked_until = None

Not committed as a feature — operational tool. Safe to re-run.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import settings
from app.core.security import get_password_hash
from app.database import async_session_factory
from app.models.auth.user import User


async def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python -m scripts.reset_password <email> <new_password>")
        sys.exit(2)
    email, new_password = sys.argv[1], sys.argv[2]

    if len(new_password) < settings.PASSWORD_MIN_LENGTH:
        print(f"ERROR: password must be >= {settings.PASSWORD_MIN_LENGTH} chars.")
        sys.exit(2)

    async with async_session_factory() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            print(f"ERROR: no user found for {email}")
            sys.exit(1)

        now = datetime.now(UTC)
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = now
        user.password_expires_at = now + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)
        user.failed_login_attempts = 0
        user.locked_until = None

        await db.commit()
        print(
            f"OK: password reset for {email}. "
            f"Expires {user.password_expires_at:%Y-%m-%d %H:%M %Z}. "
            f"Failed-attempts cleared, lockout cleared."
        )


if __name__ == "__main__":
    asyncio.run(main())
