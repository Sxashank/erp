"""Phase 3: NPA & Collections schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import model_validator

from app.models.lending.enums import (
    AssetClassification,
    AuctionStatus,
    CollectionStage,
    DemandNoticeType,
    FollowUpOutcome,
    FollowUpStatus,
    FollowUpType,
    LegalCaseStatus,
    LegalCaseType,
    LegalForumType,
    NPAStatus,
    OTSPaymentMode,
    OTSStatus,
    RestructureStatus,
    RestructureType,
    SARFAESIStage,
    WriteOffStatus,
    WriteOffType,
)
from app.schemas.base import CamelSchema, PaginatedResponse

# ============================================================================
# Collection Follow-Up Schemas
# ============================================================================


class CollectionFollowUpCreate(CamelSchema):
    """Schema for creating a collection follow-up."""

    loan_account_id: UUID
    follow_up_type: FollowUpType
    collection_stage: CollectionStage
    scheduled_date: date
    scheduled_time: str | None = None
    assigned_to_id: UUID | None = None
    assigned_to_name: str | None = None
    contact_person: str | None = None
    contact_number: str | None = None
    remarks: str | None = None


class CollectionFollowUpUpdate(CamelSchema):
    """Schema for updating a collection follow-up."""

    scheduled_date: date | None = None
    scheduled_time: str | None = None
    assigned_to_id: UUID | None = None
    assigned_to_name: str | None = None
    status: FollowUpStatus | None = None
    outcome: FollowUpOutcome | None = None
    ptp_date: date | None = None
    ptp_amount: Decimal | None = None
    ptp_broken: bool | None = None
    follow_up_notes: str | None = None
    next_follow_up_date: date | None = None
    next_action: str | None = None
    remarks: str | None = None


class CollectionFollowUpExecute(CamelSchema):
    """Schema for recording follow-up execution."""

    outcome: FollowUpOutcome
    executed_date: datetime | None = None
    contact_person: str | None = None
    contact_number: str | None = None
    follow_up_notes: str
    ptp_date: date | None = None
    ptp_amount: Decimal | None = None
    next_follow_up_date: date | None = None
    next_action: str | None = None


class CollectionFollowUpResponse(CamelSchema):
    """Schema for collection follow-up response."""

    id: UUID
    loan_account_id: UUID
    follow_up_type: FollowUpType
    collection_stage: CollectionStage
    scheduled_date: date
    scheduled_time: str | None
    assigned_to_id: UUID | None
    assigned_to_name: str | None
    status: FollowUpStatus
    executed_date: datetime | None
    outcome: FollowUpOutcome | None
    ptp_date: date | None
    ptp_amount: Decimal | None
    ptp_broken: bool
    contact_person: str | None
    contact_number: str | None
    remarks: str | None
    follow_up_notes: str | None
    next_follow_up_date: date | None
    next_action: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Demand Notice Schemas
# ============================================================================


class DemandNoticeCreate(CamelSchema):
    """Schema for creating a demand notice."""

    loan_account_id: UUID
    notice_type: DemandNoticeType
    notice_date: date
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal = Decimal("0")
    other_charges: Decimal = Decimal("0")
    total_due: Decimal
    response_due_date: date | None = None
    delivery_mode: str | None = None
    delivery_address: str | None = None
    remarks: str | None = None


class DemandNoticeUpdate(CamelSchema):
    """Schema for updating a demand notice."""

    dispatch_date: date | None = None
    delivery_date: date | None = None
    tracking_number: str | None = None
    delivery_status: str | None = None
    document_path: str | None = None
    response_received: bool | None = None
    response_date: date | None = None
    response_summary: str | None = None
    remarks: str | None = None


class DemandNoticeResponse(CamelSchema):
    """Schema for demand notice response."""

    id: UUID
    loan_account_id: UUID
    notice_number: str
    notice_type: DemandNoticeType
    notice_date: date
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal
    other_charges: Decimal
    total_due: Decimal
    response_due_date: date | None
    delivery_mode: str | None
    delivery_address: str | None
    dispatch_date: date | None
    delivery_date: date | None
    tracking_number: str | None
    delivery_status: str | None
    document_path: str | None
    response_received: bool
    response_date: date | None
    response_summary: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# NPA Record Schemas
# ============================================================================


class NPARecordCreate(CamelSchema):
    """Schema for creating an NPA record."""

    loan_account_id: UUID
    npa_status: NPAStatus
    classification_at_npa: AssetClassification
    current_classification: AssetClassification
    npa_date: date
    first_overdue_date: date | None = None
    principal_at_npa: Decimal
    interest_at_npa: Decimal
    total_at_npa: Decimal
    current_principal: Decimal
    current_interest: Decimal
    current_penal: Decimal = Decimal("0")
    current_total: Decimal
    provision_rate: Decimal
    provision_amount: Decimal
    realizable_security_value: Decimal | None = None
    resolution_strategy: str | None = None
    expected_resolution_date: date | None = None
    remarks: str | None = None


class NPARecordUpdate(CamelSchema):
    """Schema for updating an NPA record."""

    npa_status: NPAStatus | None = None
    current_classification: AssetClassification | None = None
    upgrade_date: date | None = None
    closure_date: date | None = None
    current_principal: Decimal | None = None
    current_interest: Decimal | None = None
    current_penal: Decimal | None = None
    current_total: Decimal | None = None
    provision_rate: Decimal | None = None
    provision_amount: Decimal | None = None
    realizable_security_value: Decimal | None = None
    erosion_in_security: Decimal | None = None
    total_recovery: Decimal | None = None
    recovery_principal: Decimal | None = None
    recovery_interest: Decimal | None = None
    resolution_strategy: str | None = None
    expected_resolution_date: date | None = None
    remarks: str | None = None


class NPARecordResponse(CamelSchema):
    """Schema for NPA record response."""

    id: UUID
    loan_account_id: UUID
    npa_status: NPAStatus
    classification_at_npa: AssetClassification
    current_classification: AssetClassification
    npa_date: date
    first_overdue_date: date | None
    upgrade_date: date | None
    closure_date: date | None
    principal_at_npa: Decimal
    interest_at_npa: Decimal
    total_at_npa: Decimal
    current_principal: Decimal
    current_interest: Decimal
    current_penal: Decimal
    current_total: Decimal
    provision_rate: Decimal
    provision_amount: Decimal
    realizable_security_value: Decimal | None
    erosion_in_security: Decimal | None
    total_recovery: Decimal
    recovery_principal: Decimal
    recovery_interest: Decimal
    resolution_strategy: str | None
    expected_resolution_date: date | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Penal Interest Schemas
# ============================================================================


class PenalInterestCreate(CamelSchema):
    """Schema for creating a penal interest entry."""

    loan_account_id: UUID
    period_start: date
    period_end: date
    overdue_principal: Decimal
    overdue_interest: Decimal
    overdue_total: Decimal
    penal_rate: Decimal
    days_overdue: int
    calculated_amount: Decimal
    applied_amount: Decimal
    remarks: str | None = None


class PenalInterestResponse(CamelSchema):
    """Schema for penal interest response."""

    id: UUID
    loan_account_id: UUID
    period_start: date
    period_end: date
    overdue_principal: Decimal
    overdue_interest: Decimal
    overdue_total: Decimal
    penal_rate: Decimal
    days_overdue: int
    calculated_amount: Decimal
    applied_amount: Decimal
    waived_amount: Decimal
    is_accrued: bool
    is_suspended: bool
    gl_entry_reference: str | None
    remarks: str | None
    created_at: datetime


# ============================================================================
# Penal Waiver Schemas
# ============================================================================


class PenalWaiverCreate(CamelSchema):
    """Schema for creating a penal waiver."""

    loan_account_id: UUID
    waiver_date: date
    total_penal_accrued: Decimal
    waiver_amount: Decimal
    waiver_reason: str
    remarks: str | None = None


class PenalWaiverApprove(CamelSchema):
    """Schema for approving a penal waiver."""

    approved_by_id: UUID
    approved_by_name: str
    approval_reference: str | None = None


class PenalWaiverResponse(CamelSchema):
    """Schema for penal waiver response."""

    id: UUID
    loan_account_id: UUID
    waiver_reference: str
    waiver_date: date
    total_penal_accrued: Decimal
    waiver_amount: Decimal
    balance_after_waiver: Decimal
    waiver_reason: str
    approved_by_id: UUID | None
    approved_by_name: str | None
    approval_date: date | None
    approval_reference: str | None
    is_approved: bool
    is_effected: bool
    gl_entry_reference: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# OTS Proposal Schemas
# ============================================================================


class OTSProposalCreate(CamelSchema):
    """Schema for creating an OTS proposal."""

    loan_account_id: UUID
    proposal_date: date
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal = Decimal("0")
    other_charges: Decimal = Decimal("0")
    total_outstanding: Decimal
    ots_amount: Decimal
    principal_waiver: Decimal = Decimal("0")
    interest_waiver: Decimal = Decimal("0")
    penal_waiver: Decimal = Decimal("0")
    charges_waiver: Decimal = Decimal("0")
    payment_mode: OTSPaymentMode
    upfront_amount: Decimal = Decimal("0")
    upfront_due_date: date | None = None
    number_of_installments: int = 1
    valid_till: date
    security_release_terms: str | None = None
    terms_and_conditions: str | None = None
    remarks: str | None = None


class OTSProposalUpdate(CamelSchema):
    """Schema for updating an OTS proposal."""

    status: OTSStatus | None = None
    ots_amount: Decimal | None = None
    payment_mode: OTSPaymentMode | None = None
    upfront_amount: Decimal | None = None
    upfront_due_date: date | None = None
    number_of_installments: int | None = None
    valid_till: date | None = None
    security_release_terms: str | None = None
    terms_and_conditions: str | None = None
    remarks: str | None = None


class OTSProposalApprove(CamelSchema):
    """Schema for approving an OTS proposal."""

    approved_by_id: UUID
    approved_by_name: str
    approval_authority: str


class OTSBorrowerAccept(CamelSchema):
    """Schema for recording borrower acceptance."""

    borrower_acceptance_date: date
    borrower_acceptance_document: str | None = None


class OTSPaymentScheduleCreate(CamelSchema):
    """Schema for creating OTS payment schedule."""

    installment_number: int
    due_date: date
    due_amount: Decimal


class OTSPaymentScheduleResponse(CamelSchema):
    """Schema for OTS payment schedule response."""

    id: UUID
    ots_proposal_id: UUID
    installment_number: int
    due_date: date
    due_amount: Decimal
    paid_amount: Decimal
    paid_date: date | None
    receipt_reference: str | None
    is_paid: bool
    is_overdue: bool
    remarks: str | None


class OTSProposalResponse(CamelSchema):
    """Schema for OTS proposal response."""

    id: UUID
    loan_account_id: UUID
    ots_reference: str
    proposal_date: date
    status: OTSStatus
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal
    other_charges: Decimal
    total_outstanding: Decimal
    ots_amount: Decimal
    haircut_amount: Decimal
    haircut_percent: Decimal
    principal_waiver: Decimal
    interest_waiver: Decimal
    penal_waiver: Decimal
    charges_waiver: Decimal
    payment_mode: OTSPaymentMode
    upfront_amount: Decimal
    upfront_due_date: date | None
    number_of_installments: int
    valid_till: date
    security_release_terms: str | None
    approved_by_id: UUID | None
    approved_by_name: str | None
    approval_date: date | None
    approval_authority: str | None
    borrower_acceptance_date: date | None
    borrower_acceptance_document: str | None
    total_received: Decimal
    balance_pending: Decimal
    completion_date: date | None
    remarks: str | None
    terms_and_conditions: str | None
    payment_schedule: list[OTSPaymentScheduleResponse] = []
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Loan Restructure Schemas
# ============================================================================


class LoanRestructureCreate(CamelSchema):
    """Schema for creating a loan restructure."""

    loan_account_id: UUID
    restructure_type: RestructureType
    proposal_date: date
    pre_outstanding_principal: Decimal
    pre_outstanding_interest: Decimal
    pre_interest_rate: Decimal
    pre_tenure_months: int
    pre_emi_amount: Decimal | None = None
    pre_maturity_date: date
    post_outstanding_principal: Decimal
    post_interest_rate: Decimal
    post_tenure_months: int
    post_emi_amount: Decimal | None = None
    post_maturity_date: date
    moratorium_months: int = 0
    moratorium_start_date: date | None = None
    moratorium_end_date: date | None = None
    moratorium_interest_treatment: str | None = None
    interest_waived: Decimal = Decimal("0")
    penal_waived: Decimal = Decimal("0")
    principal_converted_to_fitl: Decimal = Decimal("0")
    is_standard_restructure: bool = True
    downgrade_required: bool = False
    pre_conditions: str | None = None
    post_conditions: str | None = None
    justification: str
    remarks: str | None = None


class LoanRestructureUpdate(CamelSchema):
    """Schema for updating a loan restructure."""

    status: RestructureStatus | None = None
    post_outstanding_principal: Decimal | None = None
    post_interest_rate: Decimal | None = None
    post_tenure_months: int | None = None
    post_emi_amount: Decimal | None = None
    post_maturity_date: date | None = None
    moratorium_months: int | None = None
    moratorium_start_date: date | None = None
    moratorium_end_date: date | None = None
    pre_conditions: str | None = None
    post_conditions: str | None = None
    justification: str | None = None
    remarks: str | None = None


class LoanRestructureApprove(CamelSchema):
    """Schema for approving a restructure."""

    approved_by_id: UUID
    approved_by_name: str
    approval_authority: str


class LoanRestructureImplement(CamelSchema):
    """Schema for implementing a restructure."""

    implementation_date: date
    generate_new_schedule: bool = True


class LoanRestructureResponse(CamelSchema):
    """Schema for loan restructure response."""

    id: UUID
    loan_account_id: UUID
    restructure_reference: str
    restructure_type: RestructureType
    status: RestructureStatus
    proposal_date: date
    pre_outstanding_principal: Decimal
    pre_outstanding_interest: Decimal
    pre_interest_rate: Decimal
    pre_tenure_months: int
    pre_emi_amount: Decimal | None
    pre_maturity_date: date
    post_outstanding_principal: Decimal
    post_interest_rate: Decimal
    post_tenure_months: int
    post_emi_amount: Decimal | None
    post_maturity_date: date
    moratorium_months: int
    moratorium_start_date: date | None
    moratorium_end_date: date | None
    moratorium_interest_treatment: str | None
    interest_waived: Decimal
    penal_waived: Decimal
    principal_converted_to_fitl: Decimal
    is_standard_restructure: bool
    downgrade_required: bool
    pre_conditions: str | None
    post_conditions: str | None
    approved_by_id: UUID | None
    approved_by_name: str | None
    approval_date: date | None
    approval_authority: str | None
    implementation_date: date | None
    new_schedule_generated: bool
    justification: str
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Legal Case Schemas
# ============================================================================


class LegalCaseCreate(CamelSchema):
    """Schema for creating a legal case."""

    loan_account_id: UUID
    case_type: LegalCaseType
    forum_type: LegalForumType
    court_name: str
    court_location: str
    claim_principal: Decimal
    claim_interest: Decimal
    claim_costs: Decimal = Decimal("0")
    total_claim: Decimal
    interest_rate_claimed: Decimal | None = None
    sarfaesi_stage: SARFAESIStage | None = None
    demand_notice_date: date | None = None
    advocate_name: str | None = None
    advocate_contact: str | None = None
    law_firm: str | None = None
    remarks: str | None = None


class LegalCaseUpdate(CamelSchema):
    """Schema for updating a legal case."""

    status: LegalCaseStatus | None = None
    case_number: str | None = None
    filing_date: date | None = None
    sarfaesi_stage: SARFAESIStage | None = None
    possession_date: date | None = None
    possession_type: str | None = None
    decree_date: date | None = None
    decree_amount: Decimal | None = None
    decree_interest_rate: Decimal | None = None
    next_hearing_date: date | None = None
    legal_costs_incurred: Decimal | None = None
    court_fees_paid: Decimal | None = None
    recovery_through_case: Decimal | None = None
    closure_date: date | None = None
    closure_reason: str | None = None
    remarks: str | None = None


class LegalCaseResponse(CamelSchema):
    """Schema for legal case response."""

    id: UUID
    loan_account_id: UUID
    case_reference: str
    case_type: LegalCaseType
    forum_type: LegalForumType
    status: LegalCaseStatus
    court_name: str
    court_location: str
    case_number: str | None
    filing_date: date | None
    claim_principal: Decimal
    claim_interest: Decimal
    claim_costs: Decimal
    total_claim: Decimal
    interest_rate_claimed: Decimal | None
    sarfaesi_stage: SARFAESIStage | None
    demand_notice_date: date | None
    possession_date: date | None
    possession_type: str | None
    decree_date: date | None
    decree_amount: Decimal | None
    decree_interest_rate: Decimal | None
    advocate_name: str | None
    advocate_contact: str | None
    law_firm: str | None
    next_hearing_date: date | None
    legal_costs_incurred: Decimal
    court_fees_paid: Decimal
    recovery_through_case: Decimal
    closure_date: date | None
    closure_reason: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Legal Hearing Schemas
# ============================================================================


class LegalHearingCreate(CamelSchema):
    """Schema for creating a legal hearing."""

    legal_case_id: UUID
    hearing_number: int
    hearing_date: date
    hearing_type: str
    bench: str | None = None
    presiding_officer: str | None = None
    proceedings_summary: str
    order_passed: str | None = None
    our_advocate_present: bool = True
    opposite_party_present: bool = False
    documents_filed: str | None = None
    documents_received: str | None = None
    next_hearing_date: date | None = None
    next_hearing_purpose: str | None = None
    action_required: str | None = None
    remarks: str | None = None


class LegalHearingUpdate(CamelSchema):
    """Schema for updating a legal hearing."""

    proceedings_summary: str | None = None
    order_passed: str | None = None
    our_advocate_present: bool | None = None
    opposite_party_present: bool | None = None
    documents_filed: str | None = None
    documents_received: str | None = None
    next_hearing_date: date | None = None
    next_hearing_purpose: str | None = None
    action_required: str | None = None
    remarks: str | None = None


class LegalHearingResponse(CamelSchema):
    """Schema for legal hearing response."""

    id: UUID
    legal_case_id: UUID
    hearing_number: int
    hearing_date: date
    hearing_type: str
    bench: str | None
    presiding_officer: str | None
    proceedings_summary: str
    order_passed: str | None
    our_advocate_present: bool
    opposite_party_present: bool
    documents_filed: str | None
    documents_received: str | None
    next_hearing_date: date | None
    next_hearing_purpose: str | None
    action_required: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Property Auction Schemas
# ============================================================================


class PropertyAuctionCreate(CamelSchema):
    """Schema for creating a property auction."""

    legal_case_id: UUID
    loan_security_id: UUID | None = None
    auction_number: int
    property_description: str
    property_address: str
    property_area: str | None = None
    valuation_date: date | None = None
    market_value: Decimal
    forced_sale_value: Decimal
    reserve_price: Decimal
    emd_amount: Decimal
    emd_percent: Decimal
    auction_date: date
    auction_time: str
    auction_venue: str
    is_e_auction: bool = False
    e_auction_portal: str | None = None
    remarks: str | None = None


class PropertyAuctionUpdate(CamelSchema):
    """Schema for updating a property auction."""

    status: AuctionStatus | None = None
    publication_date: date | None = None
    publication_details: str | None = None
    newspapers: str | None = None
    auction_date: date | None = None
    auction_time: str | None = None
    auction_venue: str | None = None
    number_of_bidders: int | None = None
    highest_bid: Decimal | None = None
    successful_bidder_name: str | None = None
    successful_bidder_address: str | None = None
    sale_confirmed: bool | None = None
    sale_confirmation_date: date | None = None
    sale_certificate_date: date | None = None
    sale_amount: Decimal | None = None
    total_received: Decimal | None = None
    balance_due: Decimal | None = None
    payment_due_date: date | None = None
    cancellation_reason: str | None = None
    remarks: str | None = None


class PropertyAuctionResponse(CamelSchema):
    """Schema for property auction response."""

    id: UUID
    legal_case_id: UUID
    loan_security_id: UUID | None
    auction_reference: str
    auction_number: int
    status: AuctionStatus
    property_description: str
    property_address: str
    property_area: str | None
    valuation_date: date | None
    market_value: Decimal
    forced_sale_value: Decimal
    reserve_price: Decimal
    emd_amount: Decimal
    emd_percent: Decimal
    publication_date: date | None
    publication_details: str | None
    newspapers: str | None
    auction_date: date
    auction_time: str
    auction_venue: str
    is_e_auction: bool
    e_auction_portal: str | None
    number_of_bidders: int
    highest_bid: Decimal | None
    successful_bidder_name: str | None
    successful_bidder_address: str | None
    sale_confirmed: bool
    sale_confirmation_date: date | None
    sale_certificate_date: date | None
    sale_amount: Decimal | None
    total_received: Decimal
    balance_due: Decimal | None
    payment_due_date: date | None
    cancellation_reason: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Write-Off Schemas
# ============================================================================


class WriteOffCreate(CamelSchema):
    """Schema for creating a write-off."""

    loan_account_id: UUID
    write_off_type: WriteOffType
    proposal_date: date
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal = Decimal("0")
    other_charges: Decimal = Decimal("0")
    total_outstanding: Decimal
    principal_written_off: Decimal
    interest_written_off: Decimal
    penal_written_off: Decimal = Decimal("0")
    total_written_off: Decimal
    provision_available: Decimal
    provision_utilized: Decimal
    security_value: Decimal | None = None
    security_realized: Decimal | None = None
    shortfall: Decimal | None = None
    justification: str
    recovery_efforts: str | None = None
    remarks: str | None = None


class WriteOffApprove(CamelSchema):
    """Schema for approving a write-off."""

    approved_by_id: UUID
    approved_by_name: str
    approval_authority: str
    board_resolution_date: date | None = None
    board_resolution_number: str | None = None


class WriteOffEffect(CamelSchema):
    """Schema for effecting a write-off."""

    effective_date: date


class WriteOffResponse(CamelSchema):
    """Schema for write-off response."""

    id: UUID
    loan_account_id: UUID
    write_off_reference: str
    write_off_type: WriteOffType
    status: WriteOffStatus
    proposal_date: date
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal
    other_charges: Decimal
    total_outstanding: Decimal
    principal_written_off: Decimal
    interest_written_off: Decimal
    penal_written_off: Decimal
    total_written_off: Decimal
    provision_available: Decimal
    provision_utilized: Decimal
    security_value: Decimal | None
    security_realized: Decimal | None
    shortfall: Decimal | None
    justification: str
    recovery_efforts: str | None
    approved_by_id: UUID | None
    approved_by_name: str | None
    approval_date: date | None
    approval_authority: str | None
    board_resolution_date: date | None
    board_resolution_number: str | None
    effective_date: date | None
    gl_entry_reference: str | None
    recovery_after_write_off: Decimal
    write_back_date: date | None
    write_back_amount: Decimal | None
    write_back_reason: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Summary & Dashboard Schemas
# ============================================================================


class NPASummary(CamelSchema):
    """NPA portfolio summary (camelCase wire format).

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    total_npa_accounts: int = 0
    total_npa_amount: Decimal = Decimal("0")
    gross_npa_ratio: Decimal = Decimal("0")
    net_npa_ratio: Decimal = Decimal("0")
    total_provision_held: Decimal = Decimal("0")
    provision_coverage_ratio: Decimal = Decimal("0")

    sma_0_count: int = 0
    sma_0_amount: Decimal = Decimal("0")
    sma_1_count: int = 0
    sma_1_amount: Decimal = Decimal("0")
    sma_2_count: int = 0
    sma_2_amount: Decimal = Decimal("0")

    substandard_count: int = 0
    substandard_amount: Decimal = Decimal("0")
    doubtful_1_count: int = 0
    doubtful_1_amount: Decimal = Decimal("0")
    doubtful_2_count: int = 0
    doubtful_2_amount: Decimal = Decimal("0")
    doubtful_3_count: int = 0
    doubtful_3_amount: Decimal = Decimal("0")
    loss_count: int = 0
    loss_amount: Decimal = Decimal("0")

    # Total active loans for ratio context (computed)
    total_loans: int = 0
    standard_count: int = 0
    standard_amount: Decimal = Decimal("0")


class CollectionActivitySummary(CamelSchema):
    """Collection activity summary (camelCase wire format).

    Monetary fields stay Decimal per CLAUDE.md §6.2.
    """

    total_overdue_accounts: int = 0
    total_overdue_amount: Decimal = Decimal("0")
    pending_follow_ups: int = 0
    completed_follow_ups_today: int = 0
    ptp_received_count: int = 0
    ptp_total_amount: Decimal = Decimal("0")
    collections_today: Decimal = Decimal("0")
    collections_mtd: Decimal = Decimal("0")


class RecoverySummary(CamelSchema):
    """Recovery summary for NPA accounts (camelCase wire format)."""

    total_ots_proposals: int = 0
    approved_ots: int = 0
    completed_ots: int = 0
    ots_settlement_amount: Decimal = Decimal("0")

    total_restructures: int = 0
    approved_restructures: int = 0
    implemented_restructures: int = 0

    total_legal_cases: int = 0
    pending_cases: int = 0
    decree_obtained: int = 0
    recovery_through_legal: Decimal = Decimal("0")

    total_written_off: Decimal = Decimal("0")
    recovery_from_written_off: Decimal = Decimal("0")


# ============================================================================
# Paginated Response Types
# ============================================================================


class PaginatedFollowUpResponse(PaginatedResponse):
    """Paginated collection follow-up response."""

    items: list[CollectionFollowUpResponse] = []


class PaginatedDemandNoticeResponse(PaginatedResponse):
    """Paginated demand notice response."""

    items: list[DemandNoticeResponse] = []


class PaginatedNPARecordResponse(PaginatedResponse):
    """Paginated NPA record response."""

    items: list[NPARecordResponse] = []


class PaginatedOTSProposalResponse(PaginatedResponse):
    """Paginated OTS proposal response."""

    items: list[OTSProposalResponse] = []


class PaginatedRestructureResponse(PaginatedResponse):
    """Paginated restructure response."""

    items: list[LoanRestructureResponse] = []


class PaginatedLegalCaseResponse(PaginatedResponse):
    """Paginated legal case response."""

    items: list[LegalCaseResponse] = []


class PaginatedAuctionResponse(PaginatedResponse):
    """Paginated auction response."""

    items: list[PropertyAuctionResponse] = []


class PaginatedWriteOffResponse(PaginatedResponse):
    """Paginated write-off response."""

    items: list[WriteOffResponse] = []


# ============================================================================
# Slim list responses (camelCase wire format via CamelSchema)
# ============================================================================


def _flatten_loan_account(obj):
    """Pull loan_account_number + entity_name off a joined ORM row."""
    loan = getattr(obj, "loan_account", None)
    entity = getattr(loan, "entity", None) if loan is not None else None
    return {
        "loan_account_id": getattr(obj, "loan_account_id", None),
        "loan_account_number": getattr(loan, "loan_account_number", None),
        "entity_id": getattr(loan, "entity_id", None),
        "entity_name": (getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)),
    }


class OTSProposalListResponse(CamelSchema):
    """Slim list response for OTS proposals (camelCase wire format).

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    ots_reference: str
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    proposal_date: date
    status: OTSStatus
    total_outstanding: Decimal
    ots_amount: Decimal
    haircut_amount: Decimal
    haircut_percent: Decimal
    upfront_amount: Decimal
    number_of_installments: int
    valid_till: date
    total_received: Decimal
    balance_pending: Decimal
    approval_date: date | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        rel = _flatten_loan_account(obj)
        return {
            "id": obj.id,
            "ots_reference": obj.ots_reference,
            **rel,
            "proposal_date": obj.proposal_date,
            "status": obj.status,
            "total_outstanding": obj.total_outstanding,
            "ots_amount": obj.ots_amount,
            "haircut_amount": obj.haircut_amount,
            "haircut_percent": obj.haircut_percent,
            "upfront_amount": obj.upfront_amount,
            "number_of_installments": obj.number_of_installments,
            "valid_till": obj.valid_till,
            "total_received": obj.total_received,
            "balance_pending": obj.balance_pending,
            "approval_date": obj.approval_date,
        }


class RestructureListResponse(CamelSchema):
    """Slim list response for loan restructures (camelCase wire format).

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    restructure_reference: str
    restructure_type: RestructureType
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    proposal_date: date
    status: RestructureStatus
    pre_outstanding_principal: Decimal
    post_outstanding_principal: Decimal
    pre_interest_rate: Decimal
    post_interest_rate: Decimal
    pre_tenure_months: int
    post_tenure_months: int
    moratorium_months: int
    is_standard_restructure: bool
    approval_date: date | None = None
    implementation_date: date | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        rel = _flatten_loan_account(obj)
        return {
            "id": obj.id,
            "restructure_reference": obj.restructure_reference,
            "restructure_type": obj.restructure_type,
            **rel,
            "proposal_date": obj.proposal_date,
            "status": obj.status,
            "pre_outstanding_principal": obj.pre_outstanding_principal,
            "post_outstanding_principal": obj.post_outstanding_principal,
            "pre_interest_rate": obj.pre_interest_rate,
            "post_interest_rate": obj.post_interest_rate,
            "pre_tenure_months": obj.pre_tenure_months,
            "post_tenure_months": obj.post_tenure_months,
            "moratorium_months": obj.moratorium_months,
            "is_standard_restructure": obj.is_standard_restructure,
            "approval_date": obj.approval_date,
            "implementation_date": obj.implementation_date,
        }


class LegalCaseListResponse(CamelSchema):
    """Slim list response for legal cases (camelCase wire format).

    Monetary fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    case_reference: str
    case_number: str | None = None
    case_type: LegalCaseType
    forum_type: LegalForumType
    court_name: str
    court_location: str
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    status: LegalCaseStatus
    filing_date: date | None = None
    next_hearing_date: date | None = None
    total_claim: Decimal
    recovery_through_case: Decimal
    advocate_name: str | None = None
    law_firm: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        loan = getattr(obj, "loan_account", None)
        entity = getattr(loan, "entity", None) if loan is not None else None
        return {
            "id": obj.id,
            "case_reference": obj.case_reference,
            "case_number": obj.case_number,
            "case_type": obj.case_type,
            "forum_type": obj.forum_type,
            "court_name": obj.court_name,
            "court_location": obj.court_location,
            "loan_account_id": obj.loan_account_id,
            "loan_account_number": getattr(loan, "loan_account_number", None),
            "entity_id": getattr(loan, "entity_id", None),
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "status": obj.status,
            "filing_date": obj.filing_date,
            "next_hearing_date": obj.next_hearing_date,
            "total_claim": obj.total_claim,
            "recovery_through_case": obj.recovery_through_case,
            "advocate_name": obj.advocate_name,
            "law_firm": obj.law_firm,
        }


class NPAAccountListResponse(CamelSchema):
    """Slim list response for NPA accounts page (camelCase wire format).

    Source: LoanAccount filtered to NPA-grade asset_classification,
    LEFT JOINed to NPARecord for provision_rate / provision_amount.

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    loan_account_number: str
    loan_account_id: UUID
    entity_id: UUID | None = None
    entity_name: str | None = None
    product_id: UUID | None = None
    product_name: str | None = None
    total_outstanding: Decimal
    principal_outstanding: Decimal
    days_past_due: int
    classification: AssetClassification
    npa_date: date | None = None
    provision_rate: Decimal | None = None
    provision_amount: Decimal | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        # `obj` is a (LoanAccount, NPARecord|None) tuple from the join.
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, tuple):
            loan, npa = obj
        else:
            loan, npa = obj, None
        entity = getattr(loan, "entity", None)
        product = getattr(loan, "product", None)
        return {
            "id": loan.id,
            "loan_account_id": loan.id,
            "loan_account_number": loan.loan_account_number,
            "entity_id": getattr(entity, "id", None),
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "product_id": getattr(product, "id", None),
            "product_name": getattr(product, "name", None),
            "total_outstanding": loan.total_outstanding,
            "principal_outstanding": loan.principal_outstanding,
            "days_past_due": loan.days_past_due,
            "classification": loan.asset_classification,
            "npa_date": loan.npa_date or getattr(npa, "npa_date", None),
            "provision_rate": getattr(npa, "provision_rate", None),
            "provision_amount": getattr(npa, "provision_amount", None),
        }


class FollowUpListResponse(CamelSchema):
    """Slim list response for collection follow-ups (camelCase wire format)."""

    id: UUID
    loan_account_id: UUID
    loan_account_number: str | None = None
    entity_id: UUID | None = None
    entity_name: str | None = None
    follow_up_type: FollowUpType
    collection_stage: CollectionStage
    scheduled_date: date
    scheduled_time: str | None = None
    assigned_to_name: str | None = None
    status: FollowUpStatus
    executed_date: datetime | None = None
    outcome: FollowUpOutcome | None = None
    ptp_date: date | None = None
    ptp_amount: Decimal | None = None
    ptp_broken: bool
    contact_person: str | None = None
    contact_number: str | None = None
    next_follow_up_date: date | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        rel = _flatten_loan_account(obj)
        return {
            "id": obj.id,
            **rel,
            "follow_up_type": obj.follow_up_type,
            "collection_stage": obj.collection_stage,
            "scheduled_date": obj.scheduled_date,
            "scheduled_time": obj.scheduled_time,
            "assigned_to_name": obj.assigned_to_name,
            "status": obj.status,
            "executed_date": obj.executed_date,
            "outcome": obj.outcome,
            "ptp_date": obj.ptp_date,
            "ptp_amount": obj.ptp_amount,
            "ptp_broken": obj.ptp_broken,
            "contact_person": obj.contact_person,
            "contact_number": obj.contact_number,
            "next_follow_up_date": obj.next_follow_up_date,
        }
