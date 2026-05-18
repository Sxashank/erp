"""Pytest configuration and fixtures."""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import ARRAY, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.masters.organization import Organization
from app.models.auth.user import User
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.core.constants import (
    AssetType,
    DepreciationMethod,
    AssetStatus,
    AssetAcquisitionType,
)

# Test database URL (in-memory SQLite for unit tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(_type, _compiler, **_kw):
    """Allow PostgreSQL JSONB columns to compile under SQLite test metadata."""
    return "JSON"


@compiles(ARRAY, "sqlite")
def compile_array_sqlite(_type, _compiler, **_kw):
    """Allow ARRAY columns to compile under SQLite test metadata."""
    return "JSON"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_organization(session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(
        id=uuid4(),
        name="Test Organization",
        legal_name="Test Organization Private Limited",
        code="TESTORG",
        pan="AAAAA0000A",
        gstin="27AAAAA0000A1Z5",
        email="test@example.com",
        is_active=True,
    )
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_user(session: AsyncSession, test_organization: Organization) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        organization_id=test_organization.id,
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        password_hash="hashed_password",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_category(session: AsyncSession, test_organization: Organization) -> AssetCategory:
    """Create a test asset category."""
    category = AssetCategory(
        id=uuid4(),
        organization_id=test_organization.id,
        category_code="COMP",
        category_name="Computer Equipment",
        asset_type=AssetType.TANGIBLE,
        depreciation_method=DepreciationMethod.SLM,
        useful_life_years=5,
        residual_value_pct=Decimal("5.00"),
        depreciation_rate_slm=Decimal("20.00"),
        depreciation_rate_wdv=Decimal("40.00"),
        capitalization_threshold=Decimal("5000.00"),
        is_active=True,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_asset(
    session: AsyncSession,
    test_organization: Organization,
    test_category: AssetCategory,
) -> FixedAsset:
    """Create a test fixed asset."""
    asset = FixedAsset(
        id=uuid4(),
        organization_id=test_organization.id,
        category_id=test_category.id,
        asset_code="FA/COMP/2024/00001",
        asset_name="Dell Laptop",
        acquisition_date=date(2024, 1, 1),
        acquisition_type=AssetAcquisitionType.PURCHASE,
        acquisition_cost=Decimal("75000.00"),
        installation_cost=Decimal("0.00"),
        other_costs=Decimal("0.00"),
        total_cost=Decimal("75000.00"),
        residual_value=Decimal("3750.00"),
        depreciable_value=Decimal("71250.00"),
        useful_life_months=60,
        depreciation_method=DepreciationMethod.SLM,
        depreciation_rate=Decimal("20.00"),
        accumulated_depreciation=Decimal("0.00"),
        wdv_value=Decimal("75000.00"),
        status=AssetStatus.DRAFT,
        quantity=1,
        is_active=True,
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset


@pytest_asyncio.fixture
async def active_asset(
    session: AsyncSession,
    test_organization: Organization,
    test_category: AssetCategory,
) -> FixedAsset:
    """Create an active (capitalized) test fixed asset."""
    asset = FixedAsset(
        id=uuid4(),
        organization_id=test_organization.id,
        category_id=test_category.id,
        asset_code="FA/COMP/2024/00002",
        asset_name="HP Desktop",
        acquisition_date=date(2024, 1, 1),
        put_to_use_date=date(2024, 1, 15),
        depreciation_start_date=date(2024, 1, 15),
        acquisition_type=AssetAcquisitionType.PURCHASE,
        acquisition_cost=Decimal("50000.00"),
        installation_cost=Decimal("1000.00"),
        other_costs=Decimal("500.00"),
        total_cost=Decimal("51500.00"),
        residual_value=Decimal("2575.00"),
        depreciable_value=Decimal("48925.00"),
        useful_life_months=60,
        depreciation_method=DepreciationMethod.SLM,
        depreciation_rate=Decimal("20.00"),
        accumulated_depreciation=Decimal("0.00"),
        wdv_value=Decimal("51500.00"),
        status=AssetStatus.ACTIVE,
        quantity=1,
        is_active=True,
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset


# Helper functions for tests
def assert_decimal_equal(actual: Decimal, expected: Decimal, places: int = 2):
    """Assert two decimals are equal to specified decimal places."""
    actual_rounded = round(actual, places)
    expected_rounded = round(expected, places)
    assert actual_rounded == expected_rounded, f"Expected {expected_rounded}, got {actual_rounded}"
