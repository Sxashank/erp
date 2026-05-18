from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import noload
from sqlalchemy.pool import StaticPool

from app.api.v1.gst.gstn import (
    fetch_manual_gstr2b,
    file_manual_gstr1,
    generate_manual_gstr1,
    get_manual_gstr1,
    get_manual_session_status,
    get_manual_statistics,
    request_otp,
    run_manual_itc_reconciliation,
    submit_manual_gstr1,
    verify_otp,
)
from app.database import Base
from app.models.auth.user import User
from app.models.gst.gst_registration import GSTRegistration
from app.models.gst.gstn_models import (
    GSTR2BData,
    GSTItcMismatch,
    GSTNSession,
    GSTNSessionStatus,
    GSTReturnFiling,
    GSTReturnStatus,
    GSTReturnType,
)
from app.models.masters.organization import Organization
from app.schemas.gst.gstn import GSTNOTPRequest, GSTNOTPVerify

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(_type, _compiler, **_kwargs):
    return "JSON"


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    tables = [
        Organization.__table__,
        User.__table__,
        GSTRegistration.__table__,
        GSTNSession.__table__,
        GSTReturnFiling.__table__,
        GSTR2BData.__table__,
        GSTItcMismatch.__table__,
    ]

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=list(reversed(tables))))

    await engine.dispose()


@pytest_asyncio.fixture
async def session(async_engine) -> AsyncSession:
    session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as db_session:
        yield db_session
        await db_session.rollback()


@pytest_asyncio.fixture
async def test_organization(session: AsyncSession) -> Organization:
    organization = Organization(
        id=uuid4(),
        name="Test Organization",
        legal_name="Test Organization Private Limited",
        code="TESTORG",
        pan="AAAAA0000A",
        gstin="27AAAAA0000A1Z5",
        email="test@example.com",
        is_active=True,
    )
    session.add(organization)
    await session.commit()
    return organization


@pytest_asyncio.fixture
async def test_user(session: AsyncSession, test_organization: Organization) -> User:
    user = User(
        id=uuid4(),
        organization_id=test_organization.id,
        username="gst-tester",
        email="gst-tester@example.com",
        full_name="GST Tester",
        password_hash="hashed_password",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_manual_session_workflow_persists_state(session, test_organization, test_user):
    registration = GSTRegistration(
        id=uuid4(),
        organization_id=test_organization.id,
        gstin='27ABCDE1234F1Z5',
        legal_name='Test GST Registration',
        state_code='27',
        state_name='Maharashtra',
    )
    session.add(registration)
    await session.commit()

    request_result = await request_otp(
        request=GSTNOTPRequest(gstin=registration.gstin),
        organization_id=None,
        gst_registration_id=None,
        db=session,
        current_user=test_user,
    )

    assert request_result['success'] is True
    assert request_result['session_id'] is not None

    verify_result = await verify_otp(
        request=GSTNOTPVerify(gstin=registration.gstin, otp='123456', otp_reference=None),
        session_id=None,
        db=session,
        current_user=test_user,
    )

    assert verify_result['success'] is True
    session_result = await session.execute(
        select(GSTNSession)
        .options(noload("*"))
        .where(GSTNSession.id == UUID(request_result['session_id']))
    )
    session_row = session_result.scalar_one()
    assert session_row is not None
    assert session_row.status == GSTNSessionStatus.ACTIVE

    status_result = await get_manual_session_status(
        gstin=registration.gstin,
        db=session,
        current_user=test_user,
    )
    assert status_result['is_authenticated'] is True


@pytest.mark.asyncio
async def test_manual_gstr1_workflow_persists_filing(session, test_organization, test_user):
    registration = GSTRegistration(
        id=uuid4(),
        organization_id=test_organization.id,
        gstin='29ABCDE1234F1Z5',
        legal_name='Second GST Registration',
        state_code='29',
        state_name='Karnataka',
    )
    session.add(registration)
    await session.commit()

    generated = await generate_manual_gstr1(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert generated['status'] == GSTReturnStatus.DRAFT.value

    submitted = await submit_manual_gstr1(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert submitted['status'] == GSTReturnStatus.SUBMITTED.value

    filed = await file_manual_gstr1(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert filed['status'] == GSTReturnStatus.FILED.value
    assert filed['filing_id']

    result = await session.execute(
        select(GSTReturnFiling)
        .options(noload("*"))
        .where(
            GSTReturnFiling.gstin == registration.gstin,
            GSTReturnFiling.return_type == GSTReturnType.GSTR1,
            GSTReturnFiling.return_period == '042026',
        ),
    )
    filing = result.scalar_one()
    assert filing.status == GSTReturnStatus.FILED
    assert filing.arn == 'MANUAL-GSTR1-042026'

    get_result = await get_manual_gstr1(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert get_result['status'] == GSTReturnStatus.FILED.value


@pytest.mark.asyncio
async def test_manual_gstr2b_and_stats_use_persisted_records(session, test_organization, test_user):
    registration = GSTRegistration(
        id=uuid4(),
        organization_id=test_organization.id,
        gstin='24ABCDE1234F1Z5',
        legal_name='Third GST Registration',
        state_code='24',
        state_name='Gujarat',
    )
    session.add(registration)
    await session.commit()

    fetch_result = await fetch_manual_gstr2b(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert fetch_result['status'] == 'FETCHED'

    reconcile_result = await run_manual_itc_reconciliation(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert reconcile_result['status'] == 'COMPLETED'

    stats = await get_manual_statistics(
        gstin=registration.gstin,
        return_period='042026',
        db=session,
        current_user=test_user,
    )
    assert stats['pending_filings'] >= 0
    assert stats['itc_mismatches'] >= 0
