"""Phase 3: NPA & Collections schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse
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


# ============================================================================
# Collection Follow-Up Schemas
# ============================================================================

class CollectionFollowUpCreate(BaseSchema):
    """Schema for creating a collection follow-up."""

    loan_account_id: UUID
    follow_up_type: FollowUpType
    collection_stage: CollectionStage
    scheduled_date: date
    scheduled_time: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    remarks: Optional[str] = None


class CollectionFollowUpUpdate(BaseSchema):
    """Schema for updating a collection follow-up."""

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    status: Optional[FollowUpStatus] = None
    outcome: Optional[FollowUpOutcome] = None
    ptp_date: Optional[date] = None
    ptp_amount: Optional[Decimal] = None
    ptp_broken: Optional[bool] = None
    follow_up_notes: Optional[str] = None
    next_follow_up_date: Optional[date] = None
    next_action: Optional[str] = None
    remarks: Optional[str] = None


class CollectionFollowUpExecute(BaseSchema):
    """Schema for recording follow-up execution."""

    outcome: FollowUpOutcome
    executed_date: Optional[datetime] = None
    contact_person: Optional[str] = None
    contact_number: Optional[str] = None
    follow_up_notes: str
    ptp_date: Optional[date] = None
    ptp_amount: Optional[Decimal] = None
    next_follow_up_date: Optional[date] = None
    next_action: Optional[str] = None


class CollectionFollowUpResponse(BaseSchema):
    """Schema for collection follow-up response."""

    id: UUID
    loan_account_id: UUID
    follow_up_type: FollowUpType
    collection_stage: CollectionStage
    scheduled_date: date
    scheduled_time: Optional[str]
    assigned_to_id: Optional[UUID]
    assigned_to_name: Optional[str]
    status: FollowUpStatus
    executed_date: Optional[datetime]
    outcome: Optional[FollowUpOutcome]
    ptp_date: Optional[date]
    ptp_amount: Optional[Decimal]
    ptp_broken: bool
    contact_person: Optional[str]
    contact_number: Optional[str]
    remarks: Optional[str]
    follow_up_notes: Optional[str]
    next_follow_up_date: Optional[date]
    next_action: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Demand Notice Schemas
# ============================================================================

class DemandNoticeCreate(BaseSchema):
    """Schema for creating a demand notice."""

    loan_account_id: UUID
    notice_type: DemandNoticeType
    notice_date: date
    principal_outstanding: Decimal
    interest_outstanding: Decimal
    penal_outstanding: Decimal = Decimal("0")
    other_charges: Decimal = Decimal("0")
    total_due: Decimal
    response_due_date: Optional[date] = None
    delivery_mode: Optional[str] = None
    delivery_address: Optional[str] = None
    remarks: Optional[str] = None


class DemandNoticeUpdate(BaseSchema):
    """Schema for updating a demand notice."""

    dispatch_date: Optional[date] = None
    delivery_date: Optional[date] = None
    tracking_number: Optional[str] = None
    delivery_status: Optional[str] = None
    document_path: Optional[str] = None
    response_received: Optional[bool] = None
    response_date: Optional[date] = None
    response_summary: Optional[str] = None
    remarks: Optional[str] = None


class DemandNoticeResponse(BaseSchema):
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
    response_due_date: Optional[date]
    delivery_mode: Optional[str]
    delivery_address: Optional[str]
    dispatch_date: Optional[date]
    delivery_date: Optional[date]
    tracking_number: Optional[str]
    delivery_status: Optional[str]
    document_path: Optional[str]
    response_received: bool
    response_date: Optional[date]
    response_summary: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# NPA Record Schemas
# ============================================================================

class NPARecordCreate(BaseSchema):
    """Schema for creating an NPA record."""

    loan_account_id: UUID
    npa_status: NPAStatus
    classification_at_npa: AssetClassification
    current_classification: AssetClassification
    npa_date: date
    first_overdue_date: Optional[date] = None
    principal_at_npa: Decimal
    interest_at_npa: Decimal
    total_at_npa: Decimal
    current_principal: Decimal
    current_interest: Decimal
    current_penal: Decimal = Decimal("0")
    current_total: Decimal
    provision_rate: Decimal
    provision_amount: Decimal
    realizable_security_value: Optional[Decimal] = None
    resolution_strategy: Optional[str] = None
    expected_resolution_date: Optional[date] = None
    remarks: Optional[str] = None


class NPARecordUpdate(BaseSchema):
    """Schema for updating an NPA record."""

    npa_status: Optional[NPAStatus] = None
    current_classification: Optional[AssetClassification] = None
    upgrade_date: Optional[date] = None
    closure_date: Optional[date] = None
    current_principal: Optional[Decimal] = None
    current_interest: Optional[Decimal] = None
    current_penal: Optional[Decimal] = None
    current_total: Optional[Decimal] = None
    provision_rate: Optional[Decimal] = None
    provision_amount: Optional[Decimal] = None
    realizable_security_value: Optional[Decimal] = None
    erosion_in_security: Optional[Decimal] = None
    total_recovery: Optional[Decimal] = None
    recovery_principal: Optional[Decimal] = None
    recovery_interest: Optional[Decimal] = None
    resolution_strategy: Optional[str] = None
    expected_resolution_date: Optional[date] = None
    remarks: Optional[str] = None


class NPARecordResponse(BaseSchema):
    """Schema for NPA record response."""

    id: UUID
    loan_account_id: UUID
    npa_status: NPAStatus
    classification_at_npa: AssetClassification
    current_classification: AssetClassification
    npa_date: date
    first_overdue_date: Optional[date]
    upgrade_date: Optional[date]
    closure_date: Optional[date]
    principal_at_npa: Decimal
    interest_at_npa: Decimal
    total_at_npa: Decimal
    current_principal: Decimal
    current_interest: Decimal
    current_penal: Decimal
    current_total: Decimal
    provision_rate: Decimal
    provision_amount: Decimal
    realizable_security_value: Optional[Decimal]
    erosion_in_security: Optional[Decimal]
    total_recovery: Decimal
    recovery_principal: Decimal
    recovery_interest: Decimal
    resolution_strategy: Optional[str]
    expected_resolution_date: Optional[date]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Penal Interest Schemas
# ============================================================================

class PenalInterestCreate(BaseSchema):
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
    remarks: Optional[str] = None


class PenalInterestResponse(BaseSchema):
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
    gl_entry_reference: Optional[str]
    remarks: Optional[str]
    created_at: datetime


# ============================================================================
# Penal Waiver Schemas
# ============================================================================

class PenalWaiverCreate(BaseSchema):
    """Schema for creating a penal waiver."""

    loan_account_id: UUID
    waiver_date: date
    total_penal_accrued: Decimal
    waiver_amount: Decimal
    waiver_reason: str
    remarks: Optional[str] = None


class PenalWaiverApprove(BaseSchema):
    """Schema for approving a penal waiver."""

    approved_by_id: UUID
    approved_by_name: str
    approval_reference: Optional[str] = None


class PenalWaiverResponse(BaseSchema):
    """Schema for penal waiver response."""

    id: UUID
    loan_account_id: UUID
    waiver_reference: str
    waiver_date: date
    total_penal_accrued: Decimal
    waiver_amount: Decimal
    balance_after_waiver: Decimal
    waiver_reason: str
    approved_by_id: Optional[UUID]
    approved_by_name: Optional[str]
    approval_date: Optional[date]
    approval_reference: Optional[str]
    is_approved: bool
    is_effected: bool
    gl_entry_reference: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# OTS Proposal Schemas
# ============================================================================

class OTSProposalCreate(BaseSchema):
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
    upfront_due_date: Optional[date] = None
    number_of_installments: int = 1
    valid_till: date
    security_release_terms: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    remarks: Optional[str] = None


class OTSProposalUpdate(BaseSchema):
    """Schema for updating an OTS proposal."""

    status: Optional[OTSStatus] = None
    ots_amount: Optional[Decimal] = None
    payment_mode: Optional[OTSPaymentMode] = None
    upfront_amount: Optional[Decimal] = None
    upfront_due_date: Optional[date] = None
    number_of_installments: Optional[int] = None
    valid_till: Optional[date] = None
    security_release_terms: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    remarks: Optional[str] = None


class OTSProposalApprove(BaseSchema):
    """Schema for approving an OTS proposal."""

    approved_by_id: UUID
    approved_by_name: str
    approval_authority: str


class OTSBorrowerAccept(BaseSchema):
    """Schema for recording borrower acceptance."""

    borrower_acceptance_date: date
    borrower_acceptance_document: Optional[str] = None


class OTSPaymentScheduleCreate(BaseSchema):
    """Schema for creating OTS payment schedule."""

    installment_number: int
    due_date: date
    due_amount: Decimal


class OTSPaymentScheduleResponse(BaseSchema):
    """Schema for OTS payment schedule response."""

    id: UUID
    ots_proposal_id: UUID
    installment_number: int
    due_date: date
    due_amount: Decimal
    paid_amount: Decimal
    paid_date: Optional[date]
    receipt_reference: Optional[str]
    is_paid: bool
    is_overdue: bool
    remarks: Optional[str]


class OTSProposalResponse(BaseSchema):
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
    upfront_due_date: Optional[date]
    number_of_installments: int
    valid_till: date
    security_release_terms: Optional[str]
    approved_by_id: Optional[UUID]
    approved_by_name: Optional[str]
    approval_date: Optional[date]
    approval_authority: Optional[str]
    borrower_acceptance_date: Optional[date]
    borrower_acceptance_document: Optional[str]
    total_received: Decimal
    balance_pending: Decimal
    completion_date: Optional[date]
    remarks: Optional[str]
    terms_and_conditions: Optional[str]
    payment_schedule: List[OTSPaymentScheduleResponse] = []
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Loan Restructure Schemas
# ============================================================================

class LoanRestructureCreate(BaseSchema):
    """Schema for creating a loan restructure."""

    loan_account_id: UUID
    restructure_type: RestructureType
    proposal_date: date
    pre_outstanding_principal: Decimal
    pre_outstanding_interest: Decimal
    pre_interest_rate: Decimal
    pre_tenure_months: int
    pre_emi_amount: Optional[Decimal] = None
    pre_maturity_date: date
    post_outstanding_principal: Decimal
    post_interest_rate: Decimal
    post_tenure_months: int
    post_emi_amount: Optional[Decimal] = None
    post_maturity_date: date
    moratorium_months: int = 0
    moratorium_start_date: Optional[date] = None
    moratorium_end_date: Optional[date] = None
    moratorium_interest_treatment: Optional[str] = None
    interest_waived: Decimal = Decimal("0")
    penal_waived: Decimal = Decimal("0")
    principal_converted_to_fitl: Decimal = Decimal("0")
    is_standard_restructure: bool = True
    downgrade_required: bool = False
    pre_conditions: Optional[str] = None
    post_conditions: Optional[str] = None
    justification: str
    remarks: Optional[str] = None


class LoanRestructureUpdate(BaseSchema):
    """Schema for updating a loan restructure."""

    status: Optional[RestructureStatus] = None
    post_outstanding_principal: Optional[Decimal] = None
    post_interest_rate: Optional[Decimal] = None
    post_tenure_months: Optional[int] = None
    post_emi_amount: Optional[Decimal] = None
    post_maturity_date: Optional[date] = None
    moratorium_months: Optional[int] = None
    moratorium_start_date: Optional[date] = None
    moratorium_end_date: Optional[date] = None
    pre_conditions: Optional[str] = None
    post_conditions: Optional[str] = None
    justification: Optional[str] = None
    remarks: Optional[str] = None


class LoanRestructureApprove(BaseSchema):
    """Schema for approving a restructure."""

    approved_by_id: UUID
    approved_by_name: str
    approval_authority: str


class LoanRestructureImplement(BaseSchema):
    """Schema for implementing a restructure."""

    implementation_date: date
    generate_new_schedule: bool = True


class LoanRestructureResponse(BaseSchema):
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
    pre_emi_amount: Optional[Decimal]
    pre_maturity_date: date
    post_outstanding_principal: Decimal
    post_interest_rate: Decimal
    post_tenure_months: int
    post_emi_amount: Optional[Decimal]
    post_maturity_date: date
    moratorium_months: int
    moratorium_start_date: Optional[date]
    moratorium_end_date: Optional[date]
    moratorium_interest_treatment: Optional[str]
    interest_waived: Decimal
    penal_waived: Decimal
    principal_converted_to_fitl: Decimal
    is_standard_restructure: bool
    downgrade_required: bool
    pre_conditions: Optional[str]
    post_conditions: Optional[str]
    approved_by_id: Optional[UUID]
    approved_by_name: Optional[str]
    approval_date: Optional[date]
    approval_authority: Optional[str]
    implementation_date: Optional[date]
    new_schedule_generated: bool
    justification: str
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Legal Case Schemas
# ============================================================================

class LegalCaseCreate(BaseSchema):
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
    interest_rate_claimed: Optional[Decimal] = None
    sarfaesi_stage: Optional[SARFAESIStage] = None
    demand_notice_date: Optional[date] = None
    advocate_name: Optional[str] = None
    advocate_contact: Optional[str] = None
    law_firm: Optional[str] = None
    remarks: Optional[str] = None


class LegalCaseUpdate(BaseSchema):
    """Schema for updating a legal case."""

    status: Optional[LegalCaseStatus] = None
    case_number: Optional[str] = None
    filing_date: Optional[date] = None
    sarfaesi_stage: Optional[SARFAESIStage] = None
    possession_date: Optional[date] = None
    possession_type: Optional[str] = None
    decree_date: Optional[date] = None
    decree_amount: Optional[Decimal] = None
    decree_interest_rate: Optional[Decimal] = None
    next_hearing_date: Optional[date] = None
    legal_costs_incurred: Optional[Decimal] = None
    court_fees_paid: Optional[Decimal] = None
    recovery_through_case: Optional[Decimal] = None
    closure_date: Optional[date] = None
    closure_reason: Optional[str] = None
    remarks: Optional[str] = None


class LegalCaseResponse(BaseSchema):
    """Schema for legal case response."""

    id: UUID
    loan_account_id: UUID
    case_reference: str
    case_type: LegalCaseType
    forum_type: LegalForumType
    status: LegalCaseStatus
    court_name: str
    court_location: str
    case_number: Optional[str]
    filing_date: Optional[date]
    claim_principal: Decimal
    claim_interest: Decimal
    claim_costs: Decimal
    total_claim: Decimal
    interest_rate_claimed: Optional[Decimal]
    sarfaesi_stage: Optional[SARFAESIStage]
    demand_notice_date: Optional[date]
    possession_date: Optional[date]
    possession_type: Optional[str]
    decree_date: Optional[date]
    decree_amount: Optional[Decimal]
    decree_interest_rate: Optional[Decimal]
    advocate_name: Optional[str]
    advocate_contact: Optional[str]
    law_firm: Optional[str]
    next_hearing_date: Optional[date]
    legal_costs_incurred: Decimal
    court_fees_paid: Decimal
    recovery_through_case: Decimal
    closure_date: Optional[date]
    closure_reason: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Legal Hearing Schemas
# ============================================================================

class LegalHearingCreate(BaseSchema):
    """Schema for creating a legal hearing."""

    legal_case_id: UUID
    hearing_number: int
    hearing_date: date
    hearing_type: str
    bench: Optional[str] = None
    presiding_officer: Optional[str] = None
    proceedings_summary: str
    order_passed: Optional[str] = None
    our_advocate_present: bool = True
    opposite_party_present: bool = False
    documents_filed: Optional[str] = None
    documents_received: Optional[str] = None
    next_hearing_date: Optional[date] = None
    next_hearing_purpose: Optional[str] = None
    action_required: Optional[str] = None
    remarks: Optional[str] = None


class LegalHearingUpdate(BaseSchema):
    """Schema for updating a legal hearing."""

    proceedings_summary: Optional[str] = None
    order_passed: Optional[str] = None
    our_advocate_present: Optional[bool] = None
    opposite_party_present: Optional[bool] = None
    documents_filed: Optional[str] = None
    documents_received: Optional[str] = None
    next_hearing_date: Optional[date] = None
    next_hearing_purpose: Optional[str] = None
    action_required: Optional[str] = None
    remarks: Optional[str] = None


class LegalHearingResponse(BaseSchema):
    """Schema for legal hearing response."""

    id: UUID
    legal_case_id: UUID
    hearing_number: int
    hearing_date: date
    hearing_type: str
    bench: Optional[str]
    presiding_officer: Optional[str]
    proceedings_summary: str
    order_passed: Optional[str]
    our_advocate_present: bool
    opposite_party_present: bool
    documents_filed: Optional[str]
    documents_received: Optional[str]
    next_hearing_date: Optional[date]
    next_hearing_purpose: Optional[str]
    action_required: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Property Auction Schemas
# ============================================================================

class PropertyAuctionCreate(BaseSchema):
    """Schema for creating a property auction."""

    legal_case_id: UUID
    loan_security_id: Optional[UUID] = None
    auction_number: int
    property_description: str
    property_address: str
    property_area: Optional[str] = None
    valuation_date: Optional[date] = None
    market_value: Decimal
    forced_sale_value: Decimal
    reserve_price: Decimal
    emd_amount: Decimal
    emd_percent: Decimal
    auction_date: date
    auction_time: str
    auction_venue: str
    is_e_auction: bool = False
    e_auction_portal: Optional[str] = None
    remarks: Optional[str] = None


class PropertyAuctionUpdate(BaseSchema):
    """Schema for updating a property auction."""

    status: Optional[AuctionStatus] = None
    publication_date: Optional[date] = None
    publication_details: Optional[str] = None
    newspapers: Optional[str] = None
    auction_date: Optional[date] = None
    auction_time: Optional[str] = None
    auction_venue: Optional[str] = None
    number_of_bidders: Optional[int] = None
    highest_bid: Optional[Decimal] = None
    successful_bidder_name: Optional[str] = None
    successful_bidder_address: Optional[str] = None
    sale_confirmed: Optional[bool] = None
    sale_confirmation_date: Optional[date] = None
    sale_certificate_date: Optional[date] = None
    sale_amount: Optional[Decimal] = None
    total_received: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
    payment_due_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    remarks: Optional[str] = None


class PropertyAuctionResponse(BaseSchema):
    """Schema for property auction response."""

    id: UUID
    legal_case_id: UUID
    loan_security_id: Optional[UUID]
    auction_reference: str
    auction_number: int
    status: AuctionStatus
    property_description: str
    property_address: str
    property_area: Optional[str]
    valuation_date: Optional[date]
    market_value: Decimal
    forced_sale_value: Decimal
    reserve_price: Decimal
    emd_amount: Decimal
    emd_percent: Decimal
    publication_date: Optional[date]
    publication_details: Optional[str]
    newspapers: Optional[str]
    auction_date: date
    auction_time: str
    auction_venue: str
    is_e_auction: bool
    e_auction_portal: Optional[str]
    number_of_bidders: int
    highest_bid: Optional[Decimal]
    successful_bidder_name: Optional[str]
    successful_bidder_address: Optional[str]
    sale_confirmed: bool
    sale_confirmation_date: Optional[date]
    sale_certificate_date: Optional[date]
    sale_amount: Optional[Decimal]
    total_received: Decimal
    balance_due: Optional[Decimal]
    payment_due_date: Optional[date]
    cancellation_reason: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Write-Off Schemas
# ============================================================================

class WriteOffCreate(BaseSchema):
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
    security_value: Optional[Decimal] = None
    security_realized: Optional[Decimal] = None
    shortfall: Optional[Decimal] = None
    justification: str
    recovery_efforts: Optional[str] = None
    remarks: Optional[str] = None


class WriteOffApprove(BaseSchema):
    """Schema for approving a write-off."""

    approved_by_id: UUID
    approved_by_name: str
    approval_authority: str
    board_resolution_date: Optional[date] = None
    board_resolution_number: Optional[str] = None


class WriteOffEffect(BaseSchema):
    """Schema for effecting a write-off."""

    effective_date: date


class WriteOffResponse(BaseSchema):
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
    security_value: Optional[Decimal]
    security_realized: Optional[Decimal]
    shortfall: Optional[Decimal]
    justification: str
    recovery_efforts: Optional[str]
    approved_by_id: Optional[UUID]
    approved_by_name: Optional[str]
    approval_date: Optional[date]
    approval_authority: Optional[str]
    board_resolution_date: Optional[date]
    board_resolution_number: Optional[str]
    effective_date: Optional[date]
    gl_entry_reference: Optional[str]
    recovery_after_write_off: Decimal
    write_back_date: Optional[date]
    write_back_amount: Optional[Decimal]
    write_back_reason: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Summary & Dashboard Schemas
# ============================================================================

class NPASummary(BaseSchema):
    """NPA portfolio summary."""

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


class CollectionActivitySummary(BaseSchema):
    """Collection activity summary."""

    total_overdue_accounts: int = 0
    total_overdue_amount: Decimal = Decimal("0")
    pending_follow_ups: int = 0
    completed_follow_ups_today: int = 0
    ptp_received_count: int = 0
    ptp_total_amount: Decimal = Decimal("0")
    collections_today: Decimal = Decimal("0")
    collections_mtd: Decimal = Decimal("0")


class RecoverySummary(BaseSchema):
    """Recovery summary for NPA accounts."""

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

    items: List[CollectionFollowUpResponse] = []


class PaginatedDemandNoticeResponse(PaginatedResponse):
    """Paginated demand notice response."""

    items: List[DemandNoticeResponse] = []


class PaginatedNPARecordResponse(PaginatedResponse):
    """Paginated NPA record response."""

    items: List[NPARecordResponse] = []


class PaginatedOTSProposalResponse(PaginatedResponse):
    """Paginated OTS proposal response."""

    items: List[OTSProposalResponse] = []


class PaginatedRestructureResponse(PaginatedResponse):
    """Paginated restructure response."""

    items: List[LoanRestructureResponse] = []


class PaginatedLegalCaseResponse(PaginatedResponse):
    """Paginated legal case response."""

    items: List[LegalCaseResponse] = []


class PaginatedAuctionResponse(PaginatedResponse):
    """Paginated auction response."""

    items: List[PropertyAuctionResponse] = []


class PaginatedWriteOffResponse(PaginatedResponse):
    """Paginated write-off response."""

    items: List[WriteOffResponse] = []
