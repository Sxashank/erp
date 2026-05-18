from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.lending.iif import SubventionClaimResponse
from app.schemas.portal.claim import BorrowerClaimItem
from app.services.portal.reporting_service import PortalReportingService


def _claim(
    *,
    status: str,
    amount: str,
    claim_reference: str,
    release_initiated_date: date | None = None,
    released_date: date | None = None,
    release_instruction_reference: str | None = None,
    release_instruction_notes: str | None = None,
    release_reference: str | None = None,
    documents: list[dict[str, object]] | None = None,
):
    entity = SimpleNamespace(id=uuid4(), legal_name="Acme Maritime Limited")
    loan_account = SimpleNamespace(
        id=uuid4(),
        loan_account_number="LN-0001",
        entity=entity,
    )
    scheme = SimpleNamespace(
        id=uuid4(),
        scheme_code="SMFCL-IIF",
        scheme_name="Interest Incentivization Fund",
    )
    enrollment = SimpleNamespace(loan_account=loan_account, scheme=scheme)
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        enrollment_id=uuid4(),
        enrollment=enrollment,
        claim_reference=claim_reference,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 6, 30),
        claim_frequency="QUARTERLY",
        interest_paid_in_period=Decimal("250000.00"),
        applicable_subvention_amount=Decimal(amount),
        status=status,
        submitted_date=date(2026, 7, 1),
        verified_date=date(2026, 7, 5),
        release_initiated_date=release_initiated_date,
        paid_date=released_date,
        rejection_reason=None,
        release_instruction_reference=release_instruction_reference,
        release_instruction_notes=release_instruction_notes,
        utr_reference=release_reference,
        declaration_signed_by=None,
        declaration_signed_at=None,
        documents=documents or [],
        created_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        is_active=True,
        version=1,
    )


def test_claim_summary_and_recent_releases_follow_release_states() -> None:
    service = PortalReportingService(db=None)  # type: ignore[arg-type]
    released = _claim(
        status="RELEASED",
        amount="75000.00",
        claim_reference="IIF/2026Q1/00001",
        release_initiated_date=date(2026, 7, 8),
        released_date=date(2026, 7, 15),
        release_instruction_reference="SMFCL/REL/2026/041",
        release_reference="SBIN20260715XYZ",
    )
    in_progress = _claim(
        status="RELEASE_IN_PROGRESS",
        amount="50000.00",
        claim_reference="IIF/2026Q1/00002",
        release_initiated_date=date(2026, 7, 10),
        release_instruction_reference="SMFCL/REL/2026/042",
    )

    summary = service._claim_summary(
        [released, in_progress],
        [released.status, in_progress.status],
    )
    assert summary.total == 2
    assert summary.verified == 0
    assert summary.release_in_progress == 1
    assert summary.released == 1
    assert summary.released_amount == Decimal("75000.00")

    recent = service._recent_releases([released, in_progress])
    assert len(recent) == 1
    assert recent[0].claim_reference == "IIF/2026Q1/00001"
    assert recent[0].released_date == date(2026, 7, 15)
    assert recent[0].release_reference == "SBIN20260715XYZ"


def test_claim_response_mapping_exposes_release_metadata_and_download_urls() -> None:
    document_id = uuid4()
    claim = _claim(
        status="RELEASED",
        amount="64000.00",
        claim_reference="IIF/2026Q1/00003",
        release_initiated_date=date(2026, 7, 11),
        released_date=date(2026, 7, 18),
        release_instruction_reference="SMFCL/REL/2026/099",
        release_instruction_notes="Treasury batch 4",
        release_reference="UTR-2026-0009",
        documents=[
            {
                "document_id": document_id,
                "name": "Signed lender statement",
                "file_name": "signed-lender-statement.pdf",
                "document_category": "LENDER_STATEMENT",
                "uploaded_at": datetime(
                    2026,
                    7,
                    11,
                    10,
                    30,
                    tzinfo=UTC,
                ),
            }
        ],
    )

    portal_payload = BorrowerClaimItem.model_validate(claim)
    assert portal_payload.release_initiated_date == date(2026, 7, 11)
    assert portal_payload.released_date == date(2026, 7, 18)
    assert portal_payload.release_instruction_reference == "SMFCL/REL/2026/099"
    assert portal_payload.release_instruction_notes == "Treasury batch 4"
    assert portal_payload.release_reference == "UTR-2026-0009"
    assert portal_payload.documents[0].download_url == (
        f"/api/v1/portal/claims/{claim.id}/documents/{document_id}/download"
    )

    admin_payload = SubventionClaimResponse.model_validate(claim)
    assert admin_payload.release_initiated_date == date(2026, 7, 11)
    assert admin_payload.released_date == date(2026, 7, 18)
    assert admin_payload.release_instruction_reference == "SMFCL/REL/2026/099"
    assert admin_payload.release_instruction_notes == "Treasury batch 4"
    assert admin_payload.release_reference == "UTR-2026-0009"
