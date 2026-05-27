"""Lending master-data tables — the "no-code-edit per client" promise.

All values that could vary between NBFC tenants live in here. Every model
ships with sensible default rows via ``app/db/seeds/lending_masters.py``.
Tenants override via the admin UI; the seed script never overwrites
operator-edited rows.

Tables in this file (22 total):

1. ``AssetClass`` — ships, ports, shipyards, highways, airports, etc.
2. ``LifecycleEventCatalog`` — human-readable labels for event_type codes.
3. ``InsuranceType`` — Hull, P&I, Property, CAR-Third-Party, etc.
4. ``RegistrationAuthority`` — CERSAI, ROC, NeSL, DG_SHIPPING, MORTH, NHAI.
5. ``FeeType`` — operator-defined fee categories.
6. ``PenalChargePolicy`` — RBI-compliant penal-charge rules.
7. ``ChecklistItemCatalog`` — KYC / financials / property / vessel / etc.
8. ``NpaBucket`` — DPD-range thresholds (replaces hardcoded 0/31/61/91).
9. ``ProvisioningRate`` — secured/unsecured × bucket → rate.
10. ``DayCountConvention`` — ACT/365, ACT/360, 30/360.
11. ``ApprovalMatrix`` — amount-band × action × authority.
12. ``SLAMatrix`` — TAT per stage + escalation chain.
13. ``DocumentTemplate`` — letter / certificate body + merge fields.
14. ``CommunicationTemplate`` — SMS / email / WhatsApp templates.
15. ``RateResetBenchmark`` — EBLR / repo / MCLR / T-Bill / internal-COF.
16. ``ChargeTriggerRule`` — event → charge rule.
17. ``ClassificationOverridePolicy`` — COVID-special, infra-grace, etc.
18. ``WilfulDefaulterCommittee`` — ID + Review committee membership.
19. ``RecoveryAgent`` — empanelled agents per RBI norms.
20. ``FeeGlMapping`` — fee type → income/receivable GL.
21. ``NachReturnReason`` — NPCI bounce reason codes.
22. ``LendingOption`` — governed option sets for LOS/treasury dropdowns.

Design rules (CLAUDE.md flexibility memo):
- Domain-specific category fields are TEXT, not enum, so operators can add
  new values without code edits.
- Every master has ``effective_from`` / ``effective_to`` for time-travel
  (changing a rate doesn't break historical reports).
- Every master has ``organization_id`` for tenant isolation, plus a
  ``is_system`` flag indicating seeded rows (some are protected from
  deletion via service layer).
"""

from __future__ import annotations

from datetime import date as date_type
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

# ============================================================================
# 1. Asset class master — hero for asset-class-agnostic design
# ============================================================================


class AssetClass(BaseModel):
    """Catalog of asset classes the NBFC lends against.

    Seeded with VESSEL / PORT_CONCESSION / SHIPYARD_LEASEHOLD / etc.
    Adding ROAD_HIGHWAY for future port-connecting roads is one INSERT.
    """

    __tablename__ = "mst_asset_class"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_asset_class_org_code"),
        Index("ix_mst_asset_class_org", "organization_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # JSON Schema describing the attribute fields the FE form should render
    # for a security row of this asset class. Example for VESSEL:
    #   {"imo_number": {"type": "string"}, "tonnage_gross": {"type": "number"}}
    details_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    valuation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valuation_frequency_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)

    insurance_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mandatory_insurance_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, default=list
    )

    registration_authority_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="FK by code into mst_registration_authority — text not strict FK for flexibility.",
    )
    default_provisioning_band: Mapped[Optional[str]] = mapped_column(String(40))

    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ============================================================================
# 2. Lifecycle event catalog
# ============================================================================


class LifecycleEventCatalog(BaseModel):
    """Human-readable labels + visibility flags for each event_type.

    The lifecycle_event table stores event_type as TEXT; this catalog
    gives the UI a localisable label, an icon hint, and the default
    borrower-visible flag for new event types added by operators.
    """

    __tablename__ = "mst_lifecycle_event_catalog"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_lifecycle_catalog_org_code"),
        Index("ix_mst_lifecycle_catalog_org", "organization_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    phase: Mapped[Optional[str]] = mapped_column(
        String(30),
        comment="application | sanction | disbursement | servicing | closure",
    )
    icon: Mapped[Optional[str]] = mapped_column(String(40))
    is_borrower_visible_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    regulatory_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(60)), nullable=False, default=list
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 3. Insurance type master
# ============================================================================


class InsuranceType(BaseModel):
    __tablename__ = "mst_insurance_type"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_insurance_type_org_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 4. Registration authority master
# ============================================================================


class RegistrationAuthority(BaseModel):
    __tablename__ = "mst_registration_authority"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_reg_authority_org_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    portal_url: Mapped[Optional[str]] = mapped_column(String(500))
    integration_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="If wired via IntegrationConfig, the provider code goes here.",
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 5. Fee type master
# ============================================================================


class FeeType(BaseModel):
    """Operator-defined fee categories. Extends FeeMaster's enum-style."""

    __tablename__ = "mst_fee_type"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_fee_type_org_code"),)

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_gst_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gst_rate_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("18")
    )
    is_refundable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_charged_to_borrower: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    collection_stage: Mapped[Optional[str]] = mapped_column(
        String(40),
        comment="APPLICATION | SANCTION | DISBURSEMENT | EMI | PREPAYMENT | CLOSURE | EVENT",
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 6. Penal charge policy
# ============================================================================


class PenalChargePolicy(BaseModel):
    """RBI-Apr-2024 compliant penal-charge rules.

    Penal charges (post Apr-2024) are flat fees on missed instalments,
    NOT additional interest. They cannot be capitalised. Policy is per
    NBFC, board-approved.
    """

    __tablename__ = "mst_penal_charge_policy"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_penal_charge_policy_org_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    flat_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    percent_of_overdue: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    cap_per_instalment: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_capitalisable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="RBI Apr-2024: penal charges must NOT be capitalised. Defaults to False.",
    )
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date_type]] = mapped_column(Date)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 7. Checklist item catalog
# ============================================================================


class ChecklistItemCatalog(BaseModel):
    """Reusable checklist items operators can attach to product templates.

    Different from ``mst_approval_checklist_item`` which is per-template.
    This is the master catalog: "KYC PAN", "Vessel valuation", "NHAI
    concession letter", etc. Operators add new ones.
    """

    __tablename__ = "mst_checklist_item_catalog"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_checklist_catalog_org_code"),
        Index("ix_mst_checklist_catalog_category", "category"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="KYC | FINANCIAL | PROPERTY | VESSEL | PORT | LEGAL | INSURANCE | REGULATORY | OTHER",
    )
    stage: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="APPLICATION",
        comment="APPLICATION | APPRAISAL | SANCTION | PRE_DISBURSEMENT | POST_DISBURSEMENT | ONGOING",
    )
    is_mandatory_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expiry_days: Mapped[Optional[int]] = mapped_column(Integer)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 7b. Lending option sets
# ============================================================================


class LendingOption(BaseModel):
    """Tenant-controlled option sets for lending and treasury dropdowns.

    This replaces hardcoded frontend arrays for values such as lender type,
    borrowing instrument type, repayment frequency, security type, rating
    agency, and rate benchmark category. Operational records still store the
    selected code as text for audit stability, but the available options come
    from this table.
    """

    __tablename__ = "mst_lending_option"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "option_group",
            "code",
            name="uq_lending_option_org_group_code",
        ),
        Index("ix_mst_lending_option_group", "organization_id", "option_group"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_group: Mapped[str] = mapped_column(String(80), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 8. NPA bucket master
# ============================================================================


class NpaBucket(BaseModel):
    """DPD-range thresholds. Replaces hardcoded 0/31/61/91 in NPAService.

    Order is the priority — first match wins. min_dpd inclusive, max_dpd
    inclusive; max_dpd NULL means open-ended.
    """

    __tablename__ = "mst_npa_bucket"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            "effective_from",
            name="uq_npa_bucket_org_code_from",
        ),
        Index("ix_mst_npa_bucket_org_effective", "organization_id", "effective_from"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    asset_classification: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="Maps to AssetClassification enum: STANDARD | SMA_0 | SMA_1 | SMA_2 | NPA | SUBSTANDARD | DOUBTFUL_1 | DOUBTFUL_2 | DOUBTFUL_3 | LOSS",
    )
    min_dpd: Mapped[int] = mapped_column(Integer, nullable=False)
    max_dpd: Mapped[Optional[int]] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date_type]] = mapped_column(Date)
    loan_segment: Mapped[Optional[str]] = mapped_column(
        String(40),
        comment="Optional: restrict this bucket to a specific segment (e.g. INFRA, MSME).",
    )
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 9. Provisioning rate master
# ============================================================================


class ProvisioningRate(BaseModel):
    """Provisioning percentage per (bucket × security-class × segment)."""

    __tablename__ = "mst_provisioning_rate"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "asset_classification",
            "secured_unsecured",
            "loan_segment",
            "effective_from",
            name="uq_provisioning_rate_unique",
        ),
        Index(
            "ix_mst_provisioning_rate_lookup",
            "organization_id",
            "asset_classification",
            "secured_unsecured",
            "effective_from",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_classification: Mapped[str] = mapped_column(String(40), nullable=False)
    secured_unsecured: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="SECURED | UNSECURED",
    )
    loan_segment: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="DEFAULT",
        comment="DEFAULT for the catch-all; or INFRA / MSME / etc.",
    )
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    nbfc_layer: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="BL | ML | UL | TL — applies only when the rate varies by NBFC layer.",
    )
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date_type]] = mapped_column(Date)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 10. Day count convention master
# ============================================================================


class DayCountConvention(BaseModel):
    __tablename__ = "mst_day_count_convention"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_day_count_org_code"),)

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    days_in_year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 11. Approval matrix
# ============================================================================


class ApprovalMatrix(BaseModel):
    """Amount-band × action × authority for maker-checker / sanction approval."""

    __tablename__ = "mst_approval_matrix"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "action_code",
            "band_min",
            "effective_from",
            name="uq_approval_matrix_unique",
        ),
        Index("ix_mst_approval_matrix_lookup", "organization_id", "action_code", "band_min"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_code: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        comment="SANCTION_APPROVE | DISBURSEMENT_APPROVE | OTS_APPROVE | RESTRUCTURE_APPROVE | WRITE_OFF_APPROVE | INTEREST_REVIVAL_APPROVE",
    )
    band_min: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    band_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    authority_role: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="The role/title required to approve at this band (e.g. CREDIT_OFFICER, GM, CMD, BOARD).",
    )
    requires_maker_checker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    escalation_role: Mapped[Optional[str]] = mapped_column(String(80))
    sla_hours: Mapped[Optional[int]] = mapped_column(Integer)
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date_type]] = mapped_column(Date)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 12. SLA matrix
# ============================================================================


class SLAMatrix(BaseModel):
    """TAT per (stage × action × product) with escalation chain."""

    __tablename__ = "mst_sla_matrix"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "stage",
            "action_code",
            "product_code",
            name="uq_sla_matrix_unique",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    action_code: Mapped[str] = mapped_column(String(60), nullable=False)
    product_code: Mapped[str] = mapped_column(String(40), nullable=False, default="DEFAULT")
    tat_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_role: Mapped[Optional[str]] = mapped_column(String(80))
    escalation_after_hours: Mapped[Optional[int]] = mapped_column(Integer)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 13. Document template master
# ============================================================================


class DocumentTemplate(BaseModel):
    """Letter / certificate template body + merge-field schema."""

    __tablename__ = "mst_document_template"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            "template_version",
            "locale",
            name="uq_doc_template_unique",
        ),
        Index("ix_mst_doc_template_org_code", "organization_id", "code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        comment="SANCTION_LETTER | KFS | NDC | FORECLOSURE_LETTER | etc.",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MARKDOWN",
        comment="MARKDOWN | HTML",
    )
    merge_fields_schema: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="JSON Schema of expected merge fields.",
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    template_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 14. Communication template master
# ============================================================================


class CommunicationTemplate(BaseModel):
    """SMS / email / WhatsApp / push body per (event × channel × locale)."""

    __tablename__ = "mst_communication_template"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "event_code",
            "channel",
            "locale",
            "template_version",
            name="uq_comm_template_unique",
        ),
        Index("ix_mst_comm_template_event", "organization_id", "event_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_code: Mapped[str] = mapped_column(String(80), nullable=False)
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="SMS | EMAIL | WHATSAPP | PUSH | IN_APP",
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    template_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    subject: Mapped[Optional[str]] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    requires_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 15. Rate-reset benchmark master
# ============================================================================


class RateResetBenchmark(BaseModel):
    __tablename__ = "mst_rate_reset_benchmark"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            "effective_from",
            name="uq_rate_benchmark_unique",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="EBLR | RBI_REPO | MCLR_6M | T_BILL_3M | INTERNAL_COF",
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    current_value_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 16. Charge auto-trigger rule
# ============================================================================


class ChargeTriggerRule(BaseModel):
    """Map a lifecycle event (NACH_BOUNCED, FORECLOSED, etc.) to an auto-charge."""

    __tablename__ = "mst_charge_trigger_rule"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "trigger_event_code",
            "fee_type_code",
            name="uq_charge_trigger_unique",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_event_code: Mapped[str] = mapped_column(String(80), nullable=False)
    fee_type_code: Mapped[str] = mapped_column(String(60), nullable=False)
    flat_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    percent_of_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 4))
    apply_gst: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # ``is_active`` inherited from BaseModel.SoftDeleteMixin.


# ============================================================================
# 17. Classification override policy
# ============================================================================


class ClassificationOverridePolicy(BaseModel):
    """Special asset-class overrides (COVID, infra-grace, regulatory exception)."""

    __tablename__ = "mst_classification_override_policy"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    applies_to_segment: Mapped[Optional[str]] = mapped_column(String(40))
    grace_days_addition: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revivable_interest_cap_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        comment="Cap on revivable interest under this policy. NULL = no cap.",
    )
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date_type]] = mapped_column(Date)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 18. Wilful defaulter committee composition
# ============================================================================


class WilfulDefaulterCommittee(BaseModel):
    """ID Committee + Review Committee membership per tenant.

    Per RBI 30-Jul-2024 Directions. Each row = one committee member with
    role (CHAIR / MEMBER / SECRETARY), committee_type (ID / REVIEW),
    user_id, validity window.
    """

    __tablename__ = "mst_wilful_defaulter_committee"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    committee_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="ID | REVIEW",
    )
    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="CHAIR | MEMBER | SECRETARY",
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    effective_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date_type]] = mapped_column(Date)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ============================================================================
# 19. Recovery agent panel
# ============================================================================


class RecoveryAgent(BaseModel):
    """Empanelled recovery agents per RBI norms."""

    __tablename__ = "mst_recovery_agent"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_code: Mapped[str] = mapped_column(String(40), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    agency_name: Mapped[Optional[str]] = mapped_column(String(200))
    id_card_number: Mapped[Optional[str]] = mapped_column(String(80))
    id_card_validity: Mapped[Optional[date_type]] = mapped_column(Date)
    training_cert_validity: Mapped[Optional[date_type]] = mapped_column(Date)
    allowed_contact_from_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    allowed_contact_to_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=19)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))
    # ``is_active`` inherited from BaseModel.SoftDeleteMixin.


# ============================================================================
# 20. Fee → GL mapping master
# ============================================================================


class FeeGlMapping(BaseModel):
    """Maps a fee_type_code → income GL + receivable GL accounts."""

    __tablename__ = "mst_fee_gl_mapping"
    __table_args__ = (
        UniqueConstraint("organization_id", "fee_type_code", name="uq_fee_gl_mapping_unique"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    fee_type_code: Mapped[str] = mapped_column(String(60), nullable=False)
    income_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
    )
    receivable_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
    )
    gst_payable_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)


# ============================================================================
# 21. NACH return reason codes (NPCI)
# ============================================================================


class NachReturnReason(BaseModel):
    """NPCI NACH return reason codes. Read-mostly seed-driven master."""

    __tablename__ = "mst_nach_return_reason"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_nach_return_reason_unique"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="OTHER",
        comment="INSUFFICIENT_FUNDS | ACCOUNT_RELATED | TECHNICAL | MANDATE_RELATED | OTHER",
    )
    auto_retry_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triggers_charge: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
