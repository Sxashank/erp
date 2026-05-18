"""Scheme-portal rules and status translation helpers.

This module keeps the Sagar Mala scheme's borrower-eligibility and
borrower-facing status semantics in one place so both services and tests
use the same rules.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.models.lending.enums import ApplicationStage, ApplicationStatus, EntityType

INSTITUTIONAL_ENTITY_TYPES: frozenset[EntityType] = frozenset(
    {
        EntityType.CORPORATE,
        EntityType.LLP,
        EntityType.PARTNERSHIP,
        EntityType.TRUST,
        EntityType.SOCIETY,
    }
)


def is_scheme_eligible_entity_type(entity_type: EntityType) -> bool:
    """Return ``True`` only for institutional scheme borrowers."""

    return entity_type in INSTITUTIONAL_ENTITY_TYPES


def derive_scheme_application_status(
    raw_status: ApplicationStatus,
    raw_stage: ApplicationStage,
    extra_data: Mapping[str, Any] | None = None,
) -> str:
    """Translate LOS application state into scheme-facing milestones.

    The current data model does not yet persist separate lender-vs-SMFCL
    review stages. We therefore expose the closest stable borrower-facing
    milestone while preserving the canonical raw LOS ``status``/``stage``
    alongside it.
    """

    explicit_state = None
    if extra_data:
        value = extra_data.get("scheme_review_state")
        if isinstance(value, str) and value.strip():
            explicit_state = value.strip().upper()

    if raw_status == ApplicationStatus.DRAFT:
        return "DRAFT"
    if raw_status == ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
        return "QUERY_PENDING"
    if raw_status == ApplicationStatus.REJECTED:
        return "REJECTED"
    if raw_status in {
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.CANCELLED,
        ApplicationStatus.EXPIRED,
    }:
        return "CLOSED"
    if raw_stage == ApplicationStage.LEAD:
        return "DRAFT"
    if explicit_state:
        return explicit_state
    if raw_stage == ApplicationStage.APPLICATION:
        return (
            "LENDER_REVIEW" if raw_status == ApplicationStatus.SUBMITTED else "SMFCL_PRELIM_REVIEW"
        )
    if raw_stage == ApplicationStage.APPRAISAL:
        return "SMFCL_APPRAISAL"
    if raw_stage == ApplicationStage.SANCTION:
        return "APPROVED"
    if raw_stage == ApplicationStage.POST_SANCTION:
        return "SANCTION_ISSUED"
    if raw_stage == ApplicationStage.DISBURSED:
        return "CLAIM_OPEN"
    if raw_stage == ApplicationStage.CLOSED:
        return "CLOSED"
    return raw_status.value
