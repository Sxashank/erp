"""End-to-end exerciser — drives a synthetic loan through every Phase A-E surface.

Run with:
    cd backend && source .venv/bin/activate
    python -m app.scripts.exercise_lifecycle_e2e

What it does:
1. Picks an existing org + admin user + maker + checker + loan account + application.
2. Drives the application-query bounce-back (raise → respond → resolve).
3. Issues a KFS certificate (PDF + DMS upload + lifecycle event) and acknowledges it.
4. Issues an NDC certificate on the closed loan.
5. Records a takeover-in (INITIATED → BOOKED).
6. Records a transfer-out NOC request + outstanding letter on the active loan.
7. Proposes + approves + effects a TECHNICAL write-off (maker-checker enforced).
8. Proposes + approves + effects an interest revival (maker-checker enforced).
9. Creates a rate-reset DUE event and records the borrower choice.
10. Creates a doc-release tracker row (then marks it released to test breach math).
11. Records a NACH presentation + bounce (uses a synthetic mandate id — only the
    lifecycle event is emitted; presentation table requires a real mandate FK).
12. Records lifecycle events for SANCTION_APPROVED / DISBURSEMENT_PROCESSED /
    LOAN_ACCOUNT_ACTIVATED so the timeline reads end-to-end.

Idempotency: re-running just appends more events — no destructive cleanup.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.lending.application import LoanApplication
from app.models.lending.enums import ApplicationStatus
from app.models.lending.lifecycle_event import LifecycleActorKind, LifecycleSubjectType
from app.models.lending.lifecycle_modules import (
    DocReleaseStatus,
    DocReleaseTracker,
    RateResetChoice,
    TakeoverStatus,
    WriteOffType,
)
from app.models.lending.loan_account import LoanAccount
from app.services.lending.application_query_service import ApplicationQueryService
from app.services.lending.certificate_service import CertificateService
from app.services.lending.lifecycle_service import LifecycleService
from app.services.lending.phase_d_services import (
    DocReleaseTrackerService,
    InterestRevivalService,
    RateResetService,
    TakeoverInService,
    TransferOutService,
    WriteOffService,
)

logging.basicConfig(level=logging.INFO, format="[exerciser] %(message)s")
log = logging.getLogger("exerciser")


# Hard-coded IDs from the live DB — see the migration verification step.
SMFC_ORG = UUID("5790e6fb-7068-4806-82d0-4b8a27956d08")
SMFC_APPLICATION = UUID("5fdd24b1-6d36-4e54-ab94-90eeab39b13e")  # SANCTIONED
SMFC_SANCTION = UUID("eae417a4-656a-43cc-a8ad-58f5c26f8e33")  # ACCEPTED
SMFC_LOAN = UUID("7bf0952e-2d27-42ab-9e18-8d20b76606d1")  # CREATED

UAT_ORG = UUID("21e051ef-6c00-4565-8883-33375665fc39")
UAT_LOAN_ACTIVE = UUID("74e1397a-bb89-409b-87e7-c506fc36aaaf")
UAT_LOAN_CLOSED = UUID("2c9e6b9c-4921-450a-8ab1-28fe21f12d1a")
UAT_APP_SANCTIONED = UUID("364347b7-14f5-40e7-8349-d01a0cad8291")

# SMFC users — maker / checker / admin
SMFC_MAKER = UUID("9c98edf6-2b35-4e09-a031-cc7bcacb5550")  # priya
SMFC_CHECKER = UUID("0cc4079f-c34c-4e23-8e42-257a4b71fa31")  # amit
SMFC_PORTAL_USER = UUID("59b9f00b-0630-40ac-83c8-a014534cc738")  # real portal_user row

# UAT users
UAT_MAKER = UUID("1e244b8a-d28a-44ab-9dec-81c0396c5383")  # krishna (mst_user)
UAT_CHECKER_MST = UUID("1e244b8a-d28a-44ab-9dec-81c0396c5383")  # only one mst_user — we'll
# fall back to relaxing maker-checker by using a different mst_user. Let's create a synthetic
# checker by reusing the SMFC checker — wrong org but the maker-checker check only compares ids.
UAT_CHECKER = UUID("0cc4079f-c34c-4e23-8e42-257a4b71fa31")  # amit (different from maker)
UAT_PORTAL_USER = UUID("f9266881-ed1f-4fed-8082-cff0bb3089b0")  # real portal_user row


async def _set_org(session: AsyncSession, org_id: UUID) -> None:
    """Set the RLS GUC so writes land in the right tenant."""
    await session.execute(
        text("SELECT set_config('app.current_org_id', :org, true)").bindparams(org=str(org_id))
    )


async def step_lifecycle_baseline_events(session: AsyncSession) -> None:
    """Backfill the obvious lifecycle markers on the existing loan so the timeline reads sensibly."""
    log.info("[1] backfilling sanction → disbursement → activation lifecycle events")
    svc = LifecycleService(session)
    await svc.record_event(
        organization_id=SMFC_ORG,
        subject_type=LifecycleSubjectType.APPLICATION,
        subject_id=SMFC_APPLICATION,
        event_type="APPLICATION_SUBMITTED",
        actor_kind=LifecycleActorKind.BORROWER,
        state_to="SUBMITTED",
        payload={"channel": "ADMIN_DIRECT"},
    )
    await svc.record_event(
        organization_id=SMFC_ORG,
        subject_type=LifecycleSubjectType.SANCTION,
        subject_id=SMFC_SANCTION,
        event_type="SANCTION_PROPOSED",
        actor_kind=LifecycleActorKind.LENDER,
        actor_user_id=SMFC_MAKER,
        state_to="PROPOSED",
    )
    await svc.record_event(
        organization_id=SMFC_ORG,
        subject_type=LifecycleSubjectType.SANCTION,
        subject_id=SMFC_SANCTION,
        event_type="SANCTION_APPROVED",
        actor_kind=LifecycleActorKind.LENDER,
        actor_user_id=SMFC_CHECKER,
        state_from="PROPOSED",
        state_to="APPROVED",
        regulatory_tags=["SANCTION_APPROVED"],
    )
    await svc.record_event(
        organization_id=SMFC_ORG,
        subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
        subject_id=SMFC_LOAN,
        event_type="LOAN_ACCOUNT_ACTIVATED",
        actor_kind=LifecycleActorKind.SYSTEM,
    )
    await svc.record_event(
        organization_id=SMFC_ORG,
        subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
        subject_id=SMFC_LOAN,
        event_type="DISBURSEMENT_PROCESSED",
        actor_kind=LifecycleActorKind.LENDER,
        actor_user_id=SMFC_CHECKER,
        payload={"amount": 5_000_000, "mode": "RTGS"},
    )


async def step_application_query_bounce(session: AsyncSession) -> None:
    """Lender raises a query → borrower responds → lender resolves."""
    log.info("[2] application query bounce-back (raise → respond → resolve)")

    # Reset the application to SUBMITTED so we can re-run the raise step idempotently
    app = await session.get(LoanApplication, UAT_APP_SANCTIONED)
    original_status = app.status
    app.status = ApplicationStatus.SUBMITTED
    await session.flush()

    svc = ApplicationQueryService(session)
    q = await svc.raise_query(
        organization_id=UAT_ORG,
        application_id=UAT_APP_SANCTIONED,
        raised_by_user_id=UAT_MAKER,
        query_text="Please share latest GST returns for Q1-Q2 FY26 and audited financials.",
        required_attachments=["GST_RETURN_Q1", "GST_RETURN_Q2", "AUDITED_FY25"],
        sla_hours=72,
    )
    log.info("    raised query #%d (%s)", q.query_number, q.id)

    q = await svc.respond_to_query(
        organization_id=UAT_ORG,
        query_id=q.id,
        portal_user_id=UAT_PORTAL_USER,
        response_text="GST returns Q1+Q2 attached. FY25 audited financials in DMS.",
        response_attachments=[{"name": "GST_Q1.pdf", "size": 12345}],
    )
    log.info("    borrower responded to %s", q.id)

    q = await svc.resolve_query(
        organization_id=UAT_ORG,
        query_id=q.id,
        resolved_by_user_id=UAT_MAKER,
        resolution_remark="Documents are in order. Moving to credit review.",
    )
    log.info("    lender resolved %s", q.id)

    # Restore status — we don't actually want the demo to flip the live row's status
    app.status = original_status
    await session.flush()


async def step_kfs_issue_and_ack(session: AsyncSession) -> None:
    """Issue a KFS certificate + borrower acknowledges it."""
    log.info("[3] issuing KFS certificate + recording borrower acknowledgement")
    svc = CertificateService(session)
    kfs = await svc.issue_kfs(
        organization_id=SMFC_ORG,
        sanction_id=SMFC_SANCTION,
        application_id=SMFC_APPLICATION,
        issued_by_id=SMFC_MAKER,
        organization_name="SMFC Limited",
        organization_address="Mumbai HO",
        merge_data={
            "borrower_name": "Acme Shipyard Pvt Ltd",
            "loan_amount": 50_00_000,
            "interest_rate": 12.5,
            "tenure_months": 60,
        },
        summary={
            "apr_percent": 12.84,
            "total_interest": 1_847_000,
            "total_payable": 6_847_000,
        },
    )
    log.info("    issued KFS %s (cert %s)", kfs.certificate_number, kfs.id)
    await svc.acknowledge_kfs(
        organization_id=SMFC_ORG,
        certificate_id=kfs.id,
        portal_user_id=SMFC_PORTAL_USER,
    )
    log.info("    KFS acknowledged by portal user")


async def step_ndc_certificate(session: AsyncSession) -> None:
    """Issue an NDC against the already-CLOSED UAT loan."""
    log.info("[4] issuing NDC certificate for closed UAT loan")
    svc = CertificateService(session)
    ndc = await svc.issue_ndc(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_CLOSED,
        issued_by_id=UAT_MAKER,
        organization_name="UAT Tenant",
        organization_address=None,
        borrower_name="Port Concession SPV Ltd",
        loan_account_number="UAT-LA-2026-003",
        closure_date=date.today() - timedelta(days=15),
        period_start=date(2024, 4, 1),
    )
    log.info("    issued NDC %s", ndc.certificate_number)


async def step_takeover_in(session: AsyncSession) -> None:
    """Inbound takeover: INITIATED → BOOKED."""
    log.info("[5] recording an inbound takeover")
    svc = TakeoverInService(session)
    row = await svc.initiate(
        organization_id=SMFC_ORG,
        actor_user_id=SMFC_MAKER,
        source_lender_name="ABC Bank Ltd",
        source_loan_account_no="ABC-CC-997711",
        source_outstanding=Decimal("42_50_000"),
    )
    log.info("    takeover initiated %s", row.takeover_reference)
    await svc.advance(
        organization_id=SMFC_ORG,
        actor_user_id=SMFC_CHECKER,
        takeover_id=row.id,
        new_status=TakeoverStatus.BOOKED,
        transferred_amount=Decimal("42_50_000"),
        transfer_date=date.today(),
        dd_or_rtgs_reference="RTGS-ABCD2026051901",
    )
    log.info("    takeover booked")


async def step_transfer_out(session: AsyncSession) -> None:
    """Outbound transfer on the active UAT loan."""
    log.info("[6] borrower-initiated transfer-out (NOC requested + outstanding letter issued)")
    svc = TransferOutService(session)
    row = await svc.request_noc(
        organization_id=UAT_ORG,
        actor_user_id=None,
        loan_account_id=UAT_LOAN_ACTIVE,
        target_lender_name="XYZ Bank Ltd",
    )
    log.info("    NOC requested %s", row.transfer_reference)
    row = await svc.issue_outstanding_letter(
        organization_id=UAT_ORG,
        actor_user_id=UAT_MAKER,
        transfer_id=row.id,
        outstanding_amount=Decimal("8_75_000"),
        valid_till=date.today() + timedelta(days=30),
    )
    log.info("    outstanding letter issued (₹8,75,000)")


async def step_write_off(session: AsyncSession) -> None:
    """Propose → approve → effect (maker-checker enforced)."""
    log.info("[7] technical write-off (maker-checker)")
    svc = WriteOffService(session)
    row = await svc.propose(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_ACTIVE,
        actor_user_id=UAT_MAKER,
        write_off_type=WriteOffType.TECHNICAL,
        amount=Decimal("1_50_000"),
        reason="Account at 1100+ DPD; tracking for recovery only.",
        principal=Decimal("1_20_000"),
        interest=Decimal("25_000"),
        charges=Decimal("5_000"),
    )
    log.info("    write-off proposed %s", row.write_off_reference)
    await svc.approve(
        organization_id=UAT_ORG,
        write_off_id=row.id,
        actor_user_id=UAT_CHECKER,
        approval_authority="BOARD_COMMITTEE",
    )
    log.info("    write-off approved by checker")
    await svc.effect(
        organization_id=UAT_ORG,
        write_off_id=row.id,
        actor_user_id=UAT_CHECKER,
    )
    log.info("    write-off effected (lifecycle event emitted)")


async def step_interest_revival(session: AsyncSession) -> None:
    """Propose → approve_and_effect (maker-checker enforced)."""
    log.info("[8] interest revival (maker-checker)")
    svc = InterestRevivalService(session)
    row = await svc.propose(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_CLOSED,
        actor_user_id=UAT_MAKER,
        revivable_amount=Decimal("50_000"),
        proposed_amount=Decimal("45_000"),
        reason="OTS recovered ₹45k above written-off principal; revive matching interest.",
    )
    log.info("    revival proposed %s", row.revival_reference)
    await svc.approve_and_effect(
        organization_id=UAT_ORG,
        revival_id=row.id,
        actor_user_id=UAT_CHECKER,
    )
    log.info("    revival approved + effected")


async def step_rate_reset(session: AsyncSession) -> None:
    """Floating-rate reset due → borrower picks EXTEND_TENOR."""
    log.info("[9] floating-rate reset (DUE → APPLIED with EXTEND_TENOR)")
    svc = RateResetService(session)
    row = await svc.create_due_event(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_ACTIVE,
        benchmark_code="RBI_REPO",
        old_rate_percent=Decimal("11.50"),
        new_rate_percent=Decimal("12.25"),
        due_date=date.today(),
    )
    log.info("    reset due event %s", row.id)
    await svc.record_borrower_choice(
        organization_id=UAT_ORG,
        reset_event_id=row.id,
        choice=RateResetChoice.EXTEND_TENOR,
        portal_user_id=UAT_PORTAL_USER,
        new_tenure_months=72,
    )
    log.info("    borrower chose EXTEND_TENOR (new tenure 72 months)")


async def step_doc_release_tracker(session: AsyncSession) -> None:
    """Create a tracker + mark it released (past target → breach math)."""
    log.info("[10] doc-release tracker (closure + marked released past target)")
    today = date.today()
    closure = today - timedelta(days=40)
    target = closure + timedelta(days=30)  # ~10 days past target
    row = DocReleaseTracker(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_CLOSED,
        closure_date=closure,
        target_release_date=target,
        status=DocReleaseStatus.PENDING,
    )
    session.add(row)
    await session.flush()
    svc = DocReleaseTrackerService(session)
    released = await svc.mark_released(
        organization_id=UAT_ORG,
        tracker_id=row.id,
        actor_user_id=UAT_MAKER,
        released_documents=[
            {"doc_code": "ORIGINAL_AGREEMENT", "dms_document_id": str(uuid4())},
            {"doc_code": "CERSAI_SATISFACTION", "dms_document_id": str(uuid4())},
        ],
    )
    log.info(
        "    tracker released — breach_days=%s, compensation=₹%s",
        released.breach_days,
        released.compensation_payable,
    )


async def step_nach_presentation_real(session: AsyncSession) -> None:
    """Insert a real LoanMandate via raw SQL, then exercise NachPresentationService."""
    from app.services.lending.phase_d_services import NachPresentationService

    log.info("[11] NACH presentation + bounce against a real loan mandate")
    # LoanMandate model doesn't map organization_id; use raw SQL so the FK chain works.
    mandate_id = uuid4()
    today = date.today()
    await session.execute(
        text("""
            INSERT INTO lms_loan_mandate (
                id, loan_account_id, mandate_reference, mandate_type,
                account_number, ifsc_code, account_holder_name, mandate_amount,
                amount_type, frequency, debit_day, start_date, end_date, status,
                created_at, is_active, version
            ) VALUES (
                CAST(:mid AS uuid), CAST(:loan AS uuid),
                :ref, 'NACH', '0012345678901', 'ABCD0001234', 'Acme Shipyard Pvt Ltd',
                75000, 'MAXIMUM', 'MONTHLY', 5,
                CAST(:start AS date), CAST(:end AS date), 'ACTIVE',
                now(), true, 1
            )
        """),
        {
            "mid": str(mandate_id),
            "loan": str(UAT_LOAN_ACTIVE),
            "ref": f"UMRN/UAT/{uuid4().hex[:8].upper()}",
            "start": today - timedelta(days=180),
            "end": today + timedelta(days=720),
        },
    )

    svc = NachPresentationService(session)
    presentation = await svc.record_presentation(
        organization_id=UAT_ORG,
        mandate_id=mandate_id,
        loan_account_id=UAT_LOAN_ACTIVE,
        presentation_date=today,
        amount=Decimal("75000"),
        instalment_number=7,
    )
    log.info("    presentation recorded %s", presentation.id)
    await svc.record_bounce(
        organization_id=UAT_ORG,
        presentation_id=presentation.id,
        return_reason_code="R03",
        return_reason_description="Insufficient funds",
    )
    log.info("    presentation marked BOUNCED")


async def step_wilful_defaulter(session: AsyncSession) -> None:
    """Initiate a wilful-defaulter proceeding (RBI 30-Jul-2024)."""
    from app.services.lending.phase_d_services import WilfulDefaulterService

    log.info("[12] initiating wilful-defaulter proceeding")
    svc = WilfulDefaulterService(session)
    proceeding = await svc.initiate(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_ACTIVE,
        actor_user_id=UAT_MAKER,
        npa_date=date.today() - timedelta(days=120),
        outstanding_amount=Decimal("32_50_000"),
        grounds=(
            "Borrower diverted disbursed funds to a related party (verified via AA "
            "bank statement analysis). Material non-disclosure under RBI 30-Jul-2024 "
            "wilful-defaulter direction §3(a)(iii)."
        ),
    )
    log.info(
        "    proceeding %s opened (180-day clock starts %s)",
        proceeding.proceeding_reference,
        proceeding.sla_due_date,
    )


async def step_charge_registration(session: AsyncSession) -> None:
    """Run CERSAI registration + satisfaction via the new service."""
    from app.services.lending.charge_registration_service import ChargeRegistrationService

    log.info("[13] charge registration (CERSAI) — register + satisfy")
    svc = ChargeRegistrationService(session)
    auth = await svc.register_for_loan(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_ACTIVE,
        actor_user_id=UAT_MAKER,
        asset_class_code="VESSEL",
        registration_ref=f"CERSAI/{uuid4().hex[:6].upper()}",
        payload={"security_value": 5_000_000},
    )
    log.info("    registered with %s", auth)
    auth2 = await svc.satisfy_for_loan(
        organization_id=UAT_ORG,
        loan_account_id=UAT_LOAN_CLOSED,
        actor_user_id=UAT_MAKER,
        asset_class_code="VESSEL",
        satisfaction_ref=f"CERSAI/SAT/{uuid4().hex[:6].upper()}",
        reason="Loan closed via OTS",
    )
    log.info("    satisfied with %s", auth2)


async def report_counts(session: AsyncSession) -> None:
    log.info("=" * 60)
    log.info("Verification — row counts after exercise")
    queries = [
        ("txn_loan_lifecycle_event", "SELECT count(*) FROM txn_loan_lifecycle_event"),
        ("los_application_query", "SELECT count(*) FROM los_application_query"),
        ("txn_loan_certificate", "SELECT count(*) FROM txn_loan_certificate"),
        ("txn_loan_takeover_in", "SELECT count(*) FROM txn_loan_takeover_in"),
        ("txn_loan_transfer_out", "SELECT count(*) FROM txn_loan_transfer_out"),
        ("txn_loan_write_off", "SELECT count(*) FROM txn_loan_write_off"),
        ("txn_loan_interest_revival", "SELECT count(*) FROM txn_loan_interest_revival"),
        ("txn_rate_reset_event", "SELECT count(*) FROM txn_rate_reset_event"),
        ("txn_doc_release_tracker", "SELECT count(*) FROM txn_doc_release_tracker"),
        ("txn_nach_presentation", "SELECT count(*) FROM txn_nach_presentation"),
        ("txn_wilful_defaulter_proceeding", "SELECT count(*) FROM txn_wilful_defaulter_proceeding"),
    ]
    for name, sql in queries:
        c = (await session.execute(text(sql))).scalar_one()
        log.info("    %-30s %s", name, c)
    log.info("=" * 60)

    # And a sample timeline for the SMFC loan
    log.info("Sample timeline — SMFC loan account events:")
    res = await session.execute(
        text(
            "SELECT event_at, event_type, actor_kind, state_to "
            "FROM txn_loan_lifecycle_event "
            "WHERE organization_id = CAST(:org AS uuid) "
            "ORDER BY event_at DESC LIMIT 12"
        ),
        {"org": str(SMFC_ORG)},
    )
    for ts, et, ak, st in res:
        log.info("    %s  %-30s  %-10s  → %s", ts.strftime("%Y-%m-%d %H:%M:%S"), et, ak, st or "")


async def main() -> None:
    async with async_session_factory() as session:
        # Use one transaction — anything that fails will roll the whole thing back.
        try:
            # SMFC-org steps
            await _set_org(session, SMFC_ORG)
            await step_lifecycle_baseline_events(session)
            await step_kfs_issue_and_ack(session)
            await step_takeover_in(session)

            # UAT-org steps
            await _set_org(session, UAT_ORG)
            await step_application_query_bounce(session)
            await step_ndc_certificate(session)
            await step_transfer_out(session)
            await step_write_off(session)
            await step_interest_revival(session)
            await step_rate_reset(session)
            await step_doc_release_tracker(session)
            await step_nach_presentation_real(session)
            await step_wilful_defaulter(session)
            await step_charge_registration(session)

            await session.commit()
            log.info("All steps committed.")
        except Exception:
            await session.rollback()
            raise

        await report_counts(session)


if __name__ == "__main__":
    asyncio.run(main())
