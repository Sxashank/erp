#!/usr/bin/env python3
"""Create superuser script."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory, engine, Base
from app.core.security import get_password_hash
from app.core.constants import UserStatus
from app.models.auth.user import User
from app.models.auth.role import Role, UserRole


async def create_superuser(
    username: str = "admin",
    email: str = "admin@smfc.com",
    password: str = "Admin@123",
    full_name: str = "System Administrator",
):
    """Create a superuser with SUPER_ADMIN role."""
    print("=" * 50)
    print("SMFC ERP - Create Superuser")
    print("=" * 50)

    async with async_session_factory() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"\nUser '{username}' already exists!")
            print(f"  Email: {existing.email}")
            print(f"  Status: {existing.status}")
            return existing

        # Get SUPER_ADMIN role
        result = await session.execute(
            select(Role).where(Role.code == "SUPER_ADMIN")
        )
        super_admin_role = result.scalar_one_or_none()

        if not super_admin_role:
            print("\nError: SUPER_ADMIN role not found!")
            print("Please run seed_data.py first.")
            return None

        # Get default organization
        from app.models.masters.organization import Organization
        result = await session.execute(
            select(Organization).where(Organization.is_primary == True)
        )
        org = result.scalar_one_or_none()

        # Create user
        password_hash = get_password_hash(password)
        password_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            password_changed_at=datetime.now(timezone.utc),
            password_expires_at=password_expires_at,
            status=UserStatus.ACTIVE.value,
            organization_id=org.id if org else None,
        )
        session.add(user)
        await session.flush()

        # Assign SUPER_ADMIN role
        user_role = UserRole(
            user_id=user.id,
            role_id=super_admin_role.id,
            effective_from=datetime.now(timezone.utc),
        )
        session.add(user_role)

        await session.commit()

        print(f"\nSuperuser created successfully!")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  Role: SUPER_ADMIN")
        print(f"\nPlease change the password after first login!")

        return user


async def main():
    """Run superuser creation."""
    # Create tables if not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Get input
    print("\nEnter superuser details (press Enter for defaults):\n")

    username = input("Username [admin]: ").strip() or "admin"
    email = input("Email [admin@smfc.com]: ").strip() or "admin@smfc.com"
    password = input("Password [Admin@123]: ").strip() or "Admin@123"
    full_name = input("Full Name [System Administrator]: ").strip() or "System Administrator"

    await create_superuser(username, email, password, full_name)


if __name__ == "__main__":
    asyncio.run(main())
