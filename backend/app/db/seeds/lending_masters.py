"""Idempotent seed for the lending, treasury and borrowing master tables.

Run with: ``python -m app.db.seeds.lending_masters``

The seed is **idempotent** — it never overwrites operator-modified rows.
The criterion is the unique key (typically ``(organization_id, code)``):
if a row with that key exists, the seed leaves it alone. New rows are
inserted with ``is_system=True`` so the admin UI can warn operators
before they delete a baseline row.

This file is the platform's defaults library. When SMFCL launches a new
NBFC tenant, this is the first thing that runs after schema migration —
they get a working master-data set out of the box, and customise from
there via the admin UI.

The seed runs **per organization**: pass an org id, or seed defaults for
every existing organization.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.lending.masters import (
    ApprovalMatrix,
    AssetClass,
    ChargeTriggerRule,
    ChecklistItemCatalog,
    ClassificationOverridePolicy,
    CommunicationTemplate,
    DayCountConvention,
    DocumentTemplate,
    FeeGlMapping,
    FeeType,
    InsuranceType,
    LendingOption,
    LifecycleEventCatalog,
    NachReturnReason,
    NpaBucket,
    PenalChargePolicy,
    ProvisioningRate,
    RateResetBenchmark,
    RegistrationAuthority,
    SLAMatrix,
)
from app.models.masters.organization import Organization

# ============================================================================
# 1. Asset classes — VESSEL / PORT_CONCESSION / SHIPYARD_LEASEHOLD / etc.
# ============================================================================

_ASSET_CLASSES: list[dict[str, Any]] = [
    {
        "code": "VESSEL",
        "name": "Vessel / Ship",
        "description": "Cargo vessels, tankers, bulkers, passenger ships, etc. Mortgage under Merchant Shipping Act 1958.",
        "details_schema": {
            "imo_number": {"type": "string", "label": "IMO number"},
            "vessel_name": {"type": "string", "label": "Vessel name"},
            "flag_state": {"type": "string", "label": "Flag state"},
            "tonnage_gross": {"type": "number", "label": "Gross tonnage"},
            "class_society": {"type": "string", "label": "Classification society"},
            "year_built": {"type": "integer", "label": "Year built"},
            "shipyard_builder": {"type": "string", "label": "Builder shipyard"},
        },
        "mandatory_insurance_types": ["HULL", "P_AND_I"],
        "registration_authority_code": "DG_SHIPPING",
        "default_provisioning_band": "INFRASTRUCTURE",
        "sort_order": 10,
    },
    {
        "code": "PORT_CONCESSION",
        "name": "Port concession",
        "description": "Concession rights granted by a port authority for operating berths, terminals, or supporting infrastructure.",
        "details_schema": {
            "port_name": {"type": "string", "label": "Port name"},
            "concession_grantor": {"type": "string", "label": "Grantor"},
            "concession_period_years": {"type": "integer", "label": "Concession period (years)"},
            "annual_throughput_tonnes": {"type": "number", "label": "Annual throughput (tonnes)"},
        },
        "mandatory_insurance_types": ["BUSINESS_INTERRUPTION", "PROPERTY"],
        "registration_authority_code": "CERSAI",
        "default_provisioning_band": "INFRASTRUCTURE",
        "sort_order": 20,
    },
    {
        "code": "SHIPYARD_LEASEHOLD",
        "name": "Shipyard leasehold",
        "description": "Leasehold rights over shipyard / dry-dock land + EPC contract assignment.",
        "details_schema": {
            "yard_location": {"type": "string", "label": "Yard location"},
            "lease_period_years": {"type": "integer", "label": "Lease period (years)"},
            "epc_contractor": {"type": "string", "label": "EPC contractor"},
        },
        "mandatory_insurance_types": ["PROPERTY", "EQUIPMENT"],
        "registration_authority_code": "CERSAI",
        "default_provisioning_band": "INFRASTRUCTURE",
        "sort_order": 30,
    },
    {
        "code": "INDUSTRIAL_PROPERTY",
        "name": "Industrial property",
        "description": "Factory land + building hypothecated as security.",
        "details_schema": {
            "address": {"type": "string", "label": "Address"},
            "area_sqft": {"type": "number", "label": "Area (sq ft)"},
            "survey_number": {"type": "string", "label": "Survey number"},
        },
        "mandatory_insurance_types": ["PROPERTY"],
        "registration_authority_code": "CERSAI",
        "default_provisioning_band": "STANDARD",
        "sort_order": 40,
    },
    {
        "code": "COMMERCIAL_PROPERTY",
        "name": "Commercial property",
        "details_schema": {"address": {"type": "string", "label": "Address"}},
        "mandatory_insurance_types": ["PROPERTY"],
        "registration_authority_code": "CERSAI",
        "default_provisioning_band": "STANDARD",
        "sort_order": 50,
    },
    {
        "code": "EQUIPMENT",
        "name": "Plant & machinery",
        "details_schema": {
            "equipment_description": {"type": "string", "label": "Description"},
            "serial_number": {"type": "string", "label": "Serial number"},
        },
        "mandatory_insurance_types": ["EQUIPMENT"],
        "registration_authority_code": "CERSAI",
        "default_provisioning_band": "STANDARD",
        "sort_order": 60,
    },
    {
        "code": "RECEIVABLES",
        "name": "Receivables assignment",
        "description": "Assignment of book debts / receivables.",
        "details_schema": {},
        "valuation_required": False,
        "mandatory_insurance_types": [],
        "registration_authority_code": "CERSAI",
        "sort_order": 70,
    },
    {
        "code": "INVENTORY_PLEDGE",
        "name": "Inventory pledge",
        "details_schema": {},
        "mandatory_insurance_types": ["MARINE_CARGO"],
        "registration_authority_code": "CERSAI",
        "sort_order": 80,
    },
]


# ============================================================================
# 2. Lifecycle event catalog (~80 events)
# ============================================================================

_LIFECYCLE_EVENT_CATALOG: list[dict[str, Any]] = [
    # Application phase
    {
        "code": "APPLICATION_DRAFT_CREATED",
        "label": "Application drafted",
        "phase": "application",
        "borrower_visible": False,
    },
    {
        "code": "APPLICATION_SUBMITTED",
        "label": "Application submitted",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "APPLICATION_EDITED",
        "label": "Application edited",
        "phase": "application",
        "borrower_visible": False,
    },
    {
        "code": "KYC_INITIATED",
        "label": "KYC verification started",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "KYC_COMPLETED",
        "label": "KYC verified",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "BUREAU_PULL_INITIATED",
        "label": "Credit bureau pull initiated",
        "phase": "application",
        "borrower_visible": False,
    },
    {
        "code": "BUREAU_REPORT_RECEIVED",
        "label": "Credit bureau report received",
        "phase": "application",
        "borrower_visible": False,
    },
    {
        "code": "QUERY_RAISED",
        "label": "Query raised by lender",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "BORROWER_RESPONDED",
        "label": "Borrower responded to query",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "QUERY_RESOLVED",
        "label": "Query resolved",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "QUERY_LAPSED",
        "label": "Query lapsed (SLA breach)",
        "phase": "application",
        "borrower_visible": False,
    },
    {
        "code": "APPLICATION_REJECTED",
        "label": "Application rejected",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "APPLICATION_WITHDRAWN",
        "label": "Application withdrawn by borrower",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "APPLICATION_EXPIRED",
        "label": "Application expired",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "APPRAISAL_STARTED",
        "label": "Credit appraisal started",
        "phase": "application",
        "borrower_visible": False,
    },
    {
        "code": "APPRAISAL_COMPLETED",
        "label": "Credit appraisal completed",
        "phase": "application",
        "borrower_visible": False,
    },
    # Sanction phase
    {
        "code": "SANCTION_PROPOSED",
        "label": "Sanction proposed",
        "phase": "sanction",
        "borrower_visible": False,
        "regulatory_tags": ["SANCTION_PROPOSED"],
    },
    {
        "code": "SANCTION_APPROVED",
        "label": "Sanction approved",
        "phase": "sanction",
        "borrower_visible": True,
        "regulatory_tags": ["SANCTION_APPROVED"],
    },
    {
        "code": "SANCTION_REJECTED",
        "label": "Sanction rejected",
        "phase": "sanction",
        "borrower_visible": True,
    },
    {
        "code": "KFS_ISSUED",
        "label": "Key Facts Statement issued",
        "phase": "sanction",
        "borrower_visible": True,
        "regulatory_tags": ["KFS_ISSUED"],
    },
    {
        "code": "KFS_ACKNOWLEDGED",
        "label": "KFS acknowledged by borrower",
        "phase": "sanction",
        "borrower_visible": True,
        "regulatory_tags": ["KFS_ACKNOWLEDGED"],
    },
    {
        "code": "SANCTION_LETTER_ISSUED",
        "label": "Sanction letter issued",
        "phase": "sanction",
        "borrower_visible": True,
    },
    {
        "code": "SANCTION_ACCEPTED",
        "label": "Sanction accepted by borrower",
        "phase": "sanction",
        "borrower_visible": True,
        "regulatory_tags": ["SANCTION_ACCEPTED"],
    },
    {
        "code": "SANCTION_DECLINED",
        "label": "Sanction declined by borrower",
        "phase": "sanction",
        "borrower_visible": True,
    },
    {
        "code": "SANCTION_EXPIRED",
        "label": "Sanction expired",
        "phase": "sanction",
        "borrower_visible": True,
    },
    {
        "code": "CP_MARKED_COMPLIED",
        "label": "Condition precedent complied",
        "phase": "sanction",
        "borrower_visible": False,
    },
    {
        "code": "AGREEMENT_ESIGN_INITIATED",
        "label": "e-Sign initiated",
        "phase": "sanction",
        "borrower_visible": True,
    },
    {
        "code": "AGREEMENT_ESIGN_COMPLETED",
        "label": "Loan agreement signed",
        "phase": "sanction",
        "borrower_visible": True,
        "regulatory_tags": ["AGREEMENT_SIGNED"],
    },
    {
        "code": "CHARGE_REGISTERED_CERSAI",
        "label": "CERSAI charge registered",
        "phase": "sanction",
        "borrower_visible": False,
        "regulatory_tags": ["CERSAI_REGISTERED"],
    },
    {
        "code": "CHARGE_REGISTERED_ROC",
        "label": "ROC charge registered",
        "phase": "sanction",
        "borrower_visible": False,
        "regulatory_tags": ["ROC_REGISTERED"],
    },
    {
        "code": "CHARGE_REGISTERED_NESL",
        "label": "NeSL Digital Document Execution",
        "phase": "sanction",
        "borrower_visible": False,
        "regulatory_tags": ["NESL_DDA"],
    },
    # Disbursement phase
    {
        "code": "DISBURSEMENT_APPROVED",
        "label": "Disbursement approved",
        "phase": "disbursement",
        "borrower_visible": False,
    },
    {
        "code": "DISBURSEMENT_PROCESSED",
        "label": "Disbursement processed",
        "phase": "disbursement",
        "borrower_visible": True,
        "regulatory_tags": ["DISBURSEMENT_PROCESSED"],
    },
    {
        "code": "LOAN_ACCOUNT_ACTIVATED",
        "label": "Loan account activated",
        "phase": "disbursement",
        "borrower_visible": True,
    },
    {
        "code": "SCHEDULE_GENERATED",
        "label": "EMI schedule generated",
        "phase": "disbursement",
        "borrower_visible": True,
    },
    # Servicing phase
    {
        "code": "RATE_RESET_DUE",
        "label": "Rate reset due",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "RATE_RESET_APPLIED",
        "label": "Rate reset applied",
        "phase": "servicing",
        "borrower_visible": True,
        "regulatory_tags": ["RATE_RESET"],
    },
    {
        "code": "RATE_RESET_BORROWER_CHOICE",
        "label": "Rate reset borrower choice recorded",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "EMI_DATE_CHANGED",
        "label": "EMI date changed",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "NACH_REGISTERED",
        "label": "NACH mandate registered",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "NACH_PRESENTED",
        "label": "NACH presented to bank",
        "phase": "servicing",
        "borrower_visible": False,
    },
    {
        "code": "NACH_BOUNCED",
        "label": "NACH bounced",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "NACH_REPLACED",
        "label": "NACH mandate replaced",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "NACH_CANCELLED",
        "label": "NACH mandate cancelled",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "RECEIPT_RECORDED",
        "label": "Receipt recorded",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "RECEIPT_ALLOCATED",
        "label": "Receipt allocated to EMI",
        "phase": "servicing",
        "borrower_visible": False,
    },
    {
        "code": "RECEIPT_BOUNCED",
        "label": "Receipt bounced",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "PENAL_INTEREST_APPLIED",
        "label": "Penal interest applied",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "CHARGE_APPLIED",
        "label": "Charge applied",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "PROVISIONAL_INTEREST_CERT_ISSUED",
        "label": "Provisional interest certificate issued",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "INTEREST_CERT_ISSUED",
        "label": "Interest certificate issued",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "STATEMENT_ISSUED",
        "label": "Statement of account issued",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "RESTRUCTURE_PROPOSED",
        "label": "Restructure proposed",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "RESTRUCTURE_APPROVED",
        "label": "Restructure approved",
        "phase": "servicing",
        "borrower_visible": True,
        "regulatory_tags": ["RESTRUCTURE_APPROVED"],
    },
    {
        "code": "RESTRUCTURE_IMPLEMENTED",
        "label": "Restructure implemented",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "OTS_PROPOSED",
        "label": "OTS proposed",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "OTS_APPROVED",
        "label": "OTS approved",
        "phase": "servicing",
        "borrower_visible": True,
        "regulatory_tags": ["OTS_APPROVED"],
    },
    {
        "code": "OTS_BORROWER_ACCEPTED",
        "label": "OTS accepted by borrower",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "OTS_COMPLETED",
        "label": "OTS completed",
        "phase": "servicing",
        "borrower_visible": True,
        "regulatory_tags": ["OTS_COMPLETED"],
    },
    {
        "code": "ASSET_RECLASSIFIED",
        "label": "Asset re-classified",
        "phase": "servicing",
        "borrower_visible": False,
        "regulatory_tags": ["NPA_CLASSIFICATION"],
    },
    {
        "code": "DEMAND_NOTICE_ISSUED",
        "label": "Demand notice issued",
        "phase": "servicing",
        "borrower_visible": True,
    },
    # Closure & legal
    {
        "code": "LEGAL_NOTICE_13_2",
        "label": "SARFAESI 13(2) notice issued",
        "phase": "closure",
        "borrower_visible": True,
        "regulatory_tags": ["SARFAESI_13_2"],
    },
    {
        "code": "POSSESSION_13_4",
        "label": "SARFAESI 13(4) possession",
        "phase": "closure",
        "borrower_visible": True,
        "regulatory_tags": ["SARFAESI_13_4"],
    },
    {
        "code": "AUCTION_INITIATED",
        "label": "Auction initiated",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "WRITE_OFF_TECHNICAL",
        "label": "Technical write-off",
        "phase": "closure",
        "borrower_visible": False,
        "regulatory_tags": ["WRITE_OFF_TECHNICAL"],
    },
    {
        "code": "WRITE_OFF_FINAL",
        "label": "Final write-off",
        "phase": "closure",
        "borrower_visible": False,
        "regulatory_tags": ["WRITE_OFF_FINAL"],
    },
    {
        "code": "WILFUL_DEFAULTER_PROPOSED",
        "label": "Wilful defaulter proposed",
        "phase": "closure",
        "borrower_visible": True,
        "regulatory_tags": ["WD_PROPOSED"],
    },
    {
        "code": "WILFUL_DEFAULTER_CONFIRMED",
        "label": "Wilful defaulter confirmed",
        "phase": "closure",
        "borrower_visible": True,
        "regulatory_tags": ["WD_CONFIRMED"],
    },
    {
        "code": "TAKEOVER_NOC_REQUESTED",
        "label": "NoC requested for takeover",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "TAKEOVER_LETTER_ISSUED",
        "label": "Takeover letter / NoC issued",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "TAKEOVER_COMPLETED",
        "label": "Takeover completed",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "TRANSFER_IN_INITIATED",
        "label": "Transfer-in initiated",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "TRANSFER_IN_COMPLETED",
        "label": "Transfer-in completed",
        "phase": "disbursement",
        "borrower_visible": True,
    },
    {
        "code": "FORECLOSURE_QUOTE_ISSUED",
        "label": "Foreclosure quote issued",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "PREPAYMENT_QUOTE_ISSUED",
        "label": "Prepayment quote issued",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "PREPAYMENT_RECEIVED",
        "label": "Prepayment received",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "FORECLOSED",
        "label": "Loan foreclosed",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "ORIGINAL_DOCS_RELEASED",
        "label": "Original documents released",
        "phase": "closure",
        "borrower_visible": True,
        "regulatory_tags": ["DOCS_RELEASED"],
    },
    {
        "code": "NDC_ISSUED",
        "label": "No-Dues Certificate issued",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "CIBIL_UPDATE_SENT",
        "label": "CIBIL closure update sent",
        "phase": "closure",
        "borrower_visible": False,
    },
    {
        "code": "INTEREST_REVIVED",
        "label": "Interest revived",
        "phase": "servicing",
        "borrower_visible": False,
    },
    {
        "code": "BORROWER_COMMUNICATION_SENT",
        "label": "Borrower communication sent",
        "phase": "servicing",
        "borrower_visible": True,
    },
    {
        "code": "DOCUMENT_UPLOADED",
        "label": "Document uploaded",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "DOCUMENT_VERIFIED",
        "label": "Document verified",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "DOCUMENT_REJECTED",
        "label": "Document rejected",
        "phase": "application",
        "borrower_visible": True,
    },
    {
        "code": "CLOSED_NORMAL",
        "label": "Loan closed (normal)",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "CLOSED_FORECLOSED",
        "label": "Loan closed (foreclosed)",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "CLOSED_TAKEOVER",
        "label": "Loan closed (takeover)",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "CLOSED_OTS",
        "label": "Loan closed (OTS)",
        "phase": "closure",
        "borrower_visible": True,
    },
    {
        "code": "CLOSED_WRITTEN_OFF",
        "label": "Loan closed (written off)",
        "phase": "closure",
        "borrower_visible": False,
    },
]


# ============================================================================
# 3. Insurance types
# ============================================================================

_INSURANCE_TYPES = [
    ("HULL", "Hull insurance", "Hull & Machinery for vessels"),
    ("P_AND_I", "Protection & Indemnity (P&I)", "Marine third-party liability"),
    ("BUSINESS_INTERRUPTION", "Business interruption", "Loss of revenue from operational stoppage"),
    ("PROPERTY", "Property all risk", "Building / industrial property"),
    ("CAR_THIRD_PARTY", "CAR / Third party", "Contractor's All Risks / third-party liability"),
    ("MARINE_CARGO", "Marine cargo", "Goods in transit"),
    ("EQUIPMENT", "Equipment / machinery breakdown", "Plant & machinery"),
    ("KEY_PERSON", "Key-person insurance", "Insurance on borrower's key personnel"),
]


# ============================================================================
# 4. Registration authorities
# ============================================================================

_REGISTRATION_AUTHORITIES = [
    ("CERSAI", "CERSAI (Central Registry)", "https://www.cersai.org.in/"),
    ("ROC", "Registrar of Companies (MCA)", "https://www.mca.gov.in/"),
    ("NESL", "National e-Governance Services Ltd", "https://nesl.co.in/"),
    ("DG_SHIPPING", "Directorate General of Shipping", "https://dgshipping.gov.in/"),
    ("MORTH", "Ministry of Road Transport & Highways", "https://morth.nic.in/"),
    ("NHAI", "National Highways Authority of India", "https://nhai.gov.in/"),
    ("AAI", "Airports Authority of India", "https://www.aai.aero/"),
    ("RAILWAYS", "Indian Railways", "https://indianrailways.gov.in/"),
]


# ============================================================================
# 5. Fee types — operator extends this; we ship 16 baseline
# ============================================================================

_FEE_TYPES = [
    ("PROCESSING_FEE", "Processing fee", "APPLICATION", True, 18, False),
    ("LOGIN_FEE", "Login fee", "APPLICATION", True, 18, True),
    ("LEGAL_FEE", "Legal fee", "SANCTION", True, 18, False),
    ("VALUATION_FEE", "Valuation fee", "SANCTION", True, 18, False),
    ("CERSAI_FEE", "CERSAI registration fee", "SANCTION", False, 0, False),
    ("STAMP_DUTY", "Stamp duty", "SANCTION", False, 0, False),
    ("ROC_FEE", "ROC filing fee", "SANCTION", False, 0, False),
    ("NACH_BOUNCE_CHARGE", "NACH bounce charge", "EVENT", True, 18, False),
    ("EMI_BOUNCE_CHARGE", "EMI / cheque bounce charge", "EVENT", True, 18, False),
    ("LATE_PAYMENT_PENAL", "Late payment penal charge", "EVENT", True, 18, False),
    ("FORECLOSURE_FEE", "Foreclosure fee", "CLOSURE", True, 18, False),
    ("PREPAYMENT_FEE", "Prepayment charge", "PREPAYMENT", True, 18, False),
    ("STATEMENT_CHARGE", "Statement charge", "EVENT", True, 18, False),
    ("NOC_CHARGE", "NoC issuance charge", "EVENT", True, 18, False),
    ("DOC_RETRIEVAL_CHARGE", "Document retrieval charge", "EVENT", True, 18, False),
    ("EMI_DATE_CHANGE_CHARGE", "EMI date change charge", "EVENT", True, 18, False),
    ("RATE_SWITCH_CHARGE", "Floating-fixed switch charge", "EVENT", True, 18, False),
    (
        "DOC_RELEASE_BREACH_COMPENSATION",
        "Doc-release breach compensation (RBI Sep-2023)",
        "CLOSURE",
        False,
        0,
        False,
    ),
]


# ============================================================================
# 6. Checklist items — 80+ items
# ============================================================================

_CHECKLIST_ITEMS = [
    # KYC (10)
    ("KYC_PAN", "PAN card", "KYC", "APPLICATION", True, None),
    ("KYC_AADHAAR", "Aadhaar (masked)", "KYC", "APPLICATION", True, None),
    ("KYC_PHOTO", "Recent photograph", "KYC", "APPLICATION", True, None),
    ("KYC_ADDRESS_PROOF", "Address proof", "KYC", "APPLICATION", True, None),
    ("KYC_CIN", "Corporate Identity Number (CIN)", "KYC", "APPLICATION", True, None),
    ("KYC_GSTIN", "GSTIN", "KYC", "APPLICATION", True, None),
    ("KYC_MOA_AOA", "MoA / AoA", "KYC", "APPLICATION", True, None),
    ("KYC_BOARD_RESOLUTION", "Board resolution to borrow", "KYC", "APPLICATION", True, None),
    (
        "KYC_PROMOTER_NETWORTH",
        "Promoter / director net-worth statement",
        "KYC",
        "APPLICATION",
        True,
        None,
    ),
    ("KYC_BUREAU_CONSENT", "Credit bureau pull consent", "KYC", "APPLICATION", True, None),
    # Financial (8)
    ("FIN_ITR_3YR", "ITR returns (last 3 years)", "FINANCIAL", "APPLICATION", True, 365),
    (
        "FIN_AUDITED_FINANCIALS",
        "Audited financials (last 3 years)",
        "FINANCIAL",
        "APPLICATION",
        True,
        365,
    ),
    ("FIN_GST_RETURNS_12M", "GST returns (12 months)", "FINANCIAL", "APPLICATION", True, 90),
    (
        "FIN_BANK_STMT_12M",
        "Bank statements (all accounts, 12 months)",
        "FINANCIAL",
        "APPLICATION",
        True,
        90,
    ),
    ("FIN_LOD", "List of existing borrowings (LOD)", "FINANCIAL", "APPLICATION", True, 30),
    (
        "FIN_PROJECTED_FINANCIALS",
        "Projected financials (3-5 years)",
        "FINANCIAL",
        "APPLICATION",
        False,
        None,
    ),
    ("FIN_CASHFLOW_MODEL", "Cashflow model", "FINANCIAL", "APPLICATION", False, None),
    ("FIN_DEBT_PROFILE", "Existing debt schedule", "FINANCIAL", "APPLICATION", True, None),
    # Property (12)
    ("PROP_TITLE_DEED", "Title deed (chain ≥ 30 yrs)", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_EC", "Encumbrance certificate", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_TAX_RECEIPTS", "Property tax receipts (2 yrs)", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_APPROVED_PLAN", "Approved building plan", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_KHATA_PATTA", "Khata / patta", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_VALUATION", "Valuation report (panel valuer)", "PROPERTY", "APPRAISAL", True, 365),
    ("PROP_LEGAL_OPINION", "Legal opinion / title report", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_SEARCH_REPORT", "Search report (30 yrs)", "PROPERTY", "APPRAISAL", True, None),
    ("PROP_INSURANCE", "Property insurance", "PROPERTY", "PRE_DISBURSEMENT", True, 365),
    (
        "PROP_NOC_EXISTING_CHARGE",
        "NoC from existing charge holder",
        "PROPERTY",
        "PRE_DISBURSEMENT",
        False,
        None,
    ),
    (
        "PROP_DEPOSIT_TITLE_DEEDS",
        "Deposit of title deeds (equitable mortgage)",
        "PROPERTY",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    (
        "PROP_RTGS_BENEFICIARY",
        "RTGS beneficiary verification",
        "PROPERTY",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    # Vessel (8)
    ("VESSEL_RC", "Vessel registration certificate (RC)", "VESSEL", "APPRAISAL", True, None),
    ("VESSEL_TONNAGE_CERT", "Tonnage certificate", "VESSEL", "APPRAISAL", True, None),
    (
        "VESSEL_CLASS_SOCIETY_SURVEY",
        "Classification society survey",
        "VESSEL",
        "APPRAISAL",
        True,
        365,
    ),
    ("VESSEL_VALUATION", "Vessel valuation by approved valuer", "VESSEL", "APPRAISAL", True, 365),
    (
        "VESSEL_MORTGAGE_REG",
        "DG Shipping mortgage registration",
        "VESSEL",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    (
        "VESSEL_HULL_INSURANCE",
        "Hull insurance policy + assignment",
        "VESSEL",
        "PRE_DISBURSEMENT",
        True,
        365,
    ),
    ("VESSEL_PI_INSURANCE", "P&I insurance + assignment", "VESSEL", "PRE_DISBURSEMENT", True, 365),
    (
        "VESSEL_CHARTER_PARTY",
        "Charter party / time-charter agreement",
        "VESSEL",
        "APPRAISAL",
        False,
        None,
    ),
    # Maritime-specific (10)
    ("PORT_CONCESSION_AGREEMENT", "Port concession agreement", "PORT", "APPRAISAL", True, None),
    ("YARD_LEASE_DEED", "Yard lease deed", "PORT", "APPRAISAL", True, None),
    ("EPC_CONTRACT", "EPC / shipbuilding contract", "PORT", "APPRAISAL", True, None),
    ("SPONSOR_SUPPORT", "Sponsor support undertaking", "PORT", "APPRAISAL", True, None),
    (
        "DG_SHIPPING_REG_VERIFIED",
        "DG Shipping registration verified",
        "PORT",
        "APPRAISAL",
        True,
        None,
    ),
    ("PROJECT_DPR", "Project DPR", "PORT", "APPRAISAL", True, None),
    ("FINANCIAL_MODEL_VERIFIED", "Financial model verified", "PORT", "APPRAISAL", True, None),
    ("ECA_NOC", "Export Credit Agency NoC (if co-lending)", "PORT", "APPRAISAL", False, None),
    (
        "PROJECT_INSURANCE",
        "Project insurance (CAR / Erection All Risks)",
        "PORT",
        "PRE_DISBURSEMENT",
        True,
        365,
    ),
    ("PORT_AUTHORITY_NOC", "Port authority no-objection", "PORT", "APPRAISAL", True, None),
    # Legal (12)
    ("LEGAL_VETTING", "Pre-disbursement legal vetting report", "LEGAL", "APPRAISAL", True, None),
    ("LEGAL_LOAN_AGREEMENT", "Executed loan agreement", "LEGAL", "PRE_DISBURSEMENT", True, None),
    ("LEGAL_PG", "Personal guarantee", "LEGAL", "PRE_DISBURSEMENT", False, None),
    ("LEGAL_CG", "Corporate guarantee", "LEGAL", "PRE_DISBURSEMENT", False, None),
    ("LEGAL_HYPO_DEED", "Hypothecation deed", "LEGAL", "PRE_DISBURSEMENT", True, None),
    ("LEGAL_MORTGAGE_DEED", "Mortgage deed", "LEGAL", "PRE_DISBURSEMENT", False, None),
    ("LEGAL_DPN", "Demand promissory note", "LEGAL", "PRE_DISBURSEMENT", True, None),
    (
        "LEGAL_LETTER_OF_CONTINUATION",
        "Letter of continuation",
        "LEGAL",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    (
        "LEGAL_DECLARATION_NO_DEFAULT",
        "Declaration of no default",
        "LEGAL",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    (
        "LEGAL_DEED_OF_ASSIGNMENT",
        "Deed of assignment (insurance)",
        "LEGAL",
        "PRE_DISBURSEMENT",
        False,
        None,
    ),
    ("LEGAL_INDEMNITY", "Indemnity bond", "LEGAL", "PRE_DISBURSEMENT", False, None),
    (
        "LEGAL_BOARD_RESO_DRAWDOWN",
        "Board resolution for drawdown",
        "LEGAL",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    # Insurance (8)
    ("INS_HULL_POLICY", "Hull policy original", "INSURANCE", "PRE_DISBURSEMENT", True, 365),
    ("INS_PI_POLICY", "P&I policy original", "INSURANCE", "PRE_DISBURSEMENT", True, 365),
    ("INS_PROPERTY_POLICY", "Property policy original", "INSURANCE", "PRE_DISBURSEMENT", True, 365),
    ("INS_PROJECT_POLICY", "Project insurance policy", "INSURANCE", "PRE_DISBURSEMENT", True, 365),
    (
        "INS_ASSIGNMENT_LETTER",
        "Insurance assignment letter",
        "INSURANCE",
        "PRE_DISBURSEMENT",
        True,
        None,
    ),
    ("INS_PREMIUM_RECEIPT", "Premium payment receipt", "INSURANCE", "PRE_DISBURSEMENT", True, None),
    ("INS_RENEWAL_RECEIPT", "Renewal premium receipt", "INSURANCE", "ONGOING", True, 365),
    ("INS_CLAIM_HISTORY", "Past claim history", "INSURANCE", "APPRAISAL", False, None),
    # Regulatory (12)
    ("REG_CERSAI_FILING", "CERSAI charge filing", "REGULATORY", "POST_DISBURSEMENT", True, None),
    ("REG_ROC_CHG1_FILING", "ROC CHG-1 filing", "REGULATORY", "POST_DISBURSEMENT", False, None),
    (
        "REG_NESL_DDA",
        "NeSL Digital Document Execution",
        "REGULATORY",
        "POST_DISBURSEMENT",
        False,
        None,
    ),
    ("REG_RBI_REPORTING", "RBI exposure reporting", "REGULATORY", "ONGOING", True, None),
    ("REG_CRILC_REPORTING", "CRILC reporting (₹5 cr+)", "REGULATORY", "ONGOING", False, None),
    ("REG_KFS_ACK", "KFS acknowledgement", "REGULATORY", "SANCTION", True, None),
    (
        "REG_FAIR_PRACTICES_DISCLOSURE",
        "Fair Practices Code disclosure",
        "REGULATORY",
        "SANCTION",
        True,
        None,
    ),
    (
        "REG_RATE_RESET_INTIMATION",
        "Rate reset intimation (quarterly)",
        "REGULATORY",
        "ONGOING",
        False,
        None,
    ),
    ("REG_ANNUAL_STATEMENT", "Annual loan statement", "REGULATORY", "ONGOING", True, None),
    ("REG_FORM_16A", "TDS Form 16A (NRI)", "REGULATORY", "ONGOING", False, None),
    (
        "REG_DOC_RELEASE_30D",
        "Document release within 30 days of closure",
        "REGULATORY",
        "POST_DISBURSEMENT",
        True,
        None,
    ),
    (
        "REG_BUREAU_UPDATE",
        "CIBIL update post closure",
        "REGULATORY",
        "POST_DISBURSEMENT",
        True,
        None,
    ),
    ("SUPPORTING_DOCUMENT", "Additional supporting document", "OTHER", "APPLICATION", False, None),
]


# ============================================================================
# 7. NPA buckets (RBI defaults — 90-day NPA universal NBFC-ML/UL)
# ============================================================================

_DEFAULT_EFFECTIVE_FROM = date(2024, 4, 1)


_NPA_BUCKETS = [
    ("STANDARD", "Standard", "STANDARD", 0, 0, 10),
    ("SMA_0", "SMA-0 (1-30 DPD)", "SMA_0", 1, 30, 20),
    ("SMA_1", "SMA-1 (31-60 DPD)", "SMA_1", 31, 60, 30),
    ("SMA_2", "SMA-2 (61-90 DPD)", "SMA_2", 61, 90, 40),
    ("SUBSTANDARD", "Substandard (91-365 DPD)", "SUBSTANDARD", 91, 365, 50),
    ("DOUBTFUL_1", "Doubtful-1 (366-730 DPD)", "DOUBTFUL_1", 366, 730, 60),
    ("DOUBTFUL_2", "Doubtful-2 (731-1095 DPD)", "DOUBTFUL_2", 731, 1095, 70),
    ("DOUBTFUL_3", "Doubtful-3 (1096-1460 DPD)", "DOUBTFUL_3", 1096, 1460, 80),
    ("LOSS", "Loss (1461+ DPD)", "LOSS", 1461, None, 90),
]


# ============================================================================
# 8. Provisioning rates (RBI baseline — NBFC-ML)
# ============================================================================

# Tuples: (asset_classification, secured_unsecured, segment, rate)
_PROVISIONING_RATES = [
    ("STANDARD", "SECURED", "DEFAULT", Decimal("0.40")),
    ("STANDARD", "UNSECURED", "DEFAULT", Decimal("0.40")),
    ("STANDARD", "SECURED", "INFRASTRUCTURE", Decimal("0.40")),
    ("STANDARD", "SECURED", "CRE", Decimal("1.00")),
    ("SMA_0", "SECURED", "DEFAULT", Decimal("0.40")),
    ("SMA_1", "SECURED", "DEFAULT", Decimal("0.40")),
    ("SMA_2", "SECURED", "DEFAULT", Decimal("0.40")),
    ("SUBSTANDARD", "SECURED", "DEFAULT", Decimal("15.00")),
    ("SUBSTANDARD", "UNSECURED", "DEFAULT", Decimal("25.00")),
    ("DOUBTFUL_1", "SECURED", "DEFAULT", Decimal("25.00")),
    ("DOUBTFUL_1", "UNSECURED", "DEFAULT", Decimal("100.00")),
    ("DOUBTFUL_2", "SECURED", "DEFAULT", Decimal("40.00")),
    ("DOUBTFUL_2", "UNSECURED", "DEFAULT", Decimal("100.00")),
    ("DOUBTFUL_3", "SECURED", "DEFAULT", Decimal("100.00")),
    ("DOUBTFUL_3", "UNSECURED", "DEFAULT", Decimal("100.00")),
    ("LOSS", "SECURED", "DEFAULT", Decimal("100.00")),
    ("LOSS", "UNSECURED", "DEFAULT", Decimal("100.00")),
]


# ============================================================================
# 9. Day count conventions
# ============================================================================

_DAY_COUNT = [
    ("ACT_365", "Actual / 365", 365, "Actual days / 365 — standard for retail"),
    ("ACT_360", "Actual / 360", 360, "Actual days / 360 — money-market convention"),
    ("THIRTY_360", "30 / 360", 360, "30-day month / 360-day year"),
]


# ============================================================================
# 10. Rate reset benchmarks
# ============================================================================

_RATE_RESET_BENCHMARKS = [
    ("EBLR", "External Benchmark Lending Rate", Decimal("9.5000")),
    ("RBI_REPO", "RBI Repo Rate", Decimal("6.5000")),
    ("MCLR_6M", "MCLR 6-month", Decimal("9.0000")),
    ("T_BILL_3M", "T-Bill 3-month", Decimal("6.8000")),
    ("INTERNAL_COF", "Internal cost of funds", Decimal("8.5000")),
]


# ============================================================================
# 10b. Governed lending / treasury option sets
# ============================================================================

_LENDING_OPTIONS = [
    ("LENDER_TYPE", "BANK", "Bank", 10),
    ("LENDER_TYPE", "DFI", "Development Finance Institution", 20),
    ("LENDER_TYPE", "NBFC", "NBFC", 30),
    ("LENDER_TYPE", "MUTUAL_FUND", "Mutual Fund", 40),
    ("LENDER_TYPE", "INSURANCE_COMPANY", "Insurance Company", 50),
    ("LENDER_TYPE", "PENSION_FUND", "Pension Fund", 60),
    ("LENDER_TYPE", "FII", "Foreign Institutional Investor", 70),
    ("LENDER_TYPE", "NCD", "NCD Trustee / Bondholders", 80),
    ("LENDER_TYPE", "CP", "Commercial Paper Holders", 90),
    ("LENDER_TYPE", "ECB", "External Commercial Borrowing", 100),
    ("LENDER_TYPE", "SUBORDINATED_DEBT", "Subordinated Debt", 110),
    ("LENDER_TYPE", "RELATED_PARTY", "Related Party", 120),
    ("LENDER_TYPE", "OTHER", "Other", 990),
    ("BORROWING_TYPE", "TERM_LOAN", "Term Loan", 10),
    ("BORROWING_TYPE", "WORKING_CAPITAL", "Working Capital Loan", 20),
    ("BORROWING_TYPE", "CASH_CREDIT", "Cash Credit / Overdraft", 30),
    ("BORROWING_TYPE", "NCD", "Non-Convertible Debentures", 40),
    ("BORROWING_TYPE", "CP", "Commercial Paper", 50),
    ("BORROWING_TYPE", "SUBORDINATED_DEBT", "Subordinated Debt / Tier-II", 60),
    ("BORROWING_TYPE", "ECB", "External Commercial Borrowing", 70),
    ("BORROWING_TYPE", "REFINANCE", "Refinance Facility", 80),
    ("BORROWING_TYPE", "ICD", "Inter-Corporate Deposit", 90),
    ("PRODUCT_CATEGORY", "TERM_LOAN", "Term Loan", 10),
    ("PRODUCT_CATEGORY", "PROJECT_FINANCE", "Project Finance", 20),
    ("PRODUCT_CATEGORY", "WORKING_CAPITAL", "Working Capital", 30),
    ("PRODUCT_CATEGORY", "DEMAND_LOAN", "Demand Loan", 40),
    ("PRODUCT_CATEGORY", "OVERDRAFT", "Overdraft", 50),
    ("PRODUCT_CATEGORY", "CASH_CREDIT", "Cash Credit", 60),
    ("PRODUCT_CATEGORY", "LETTER_OF_CREDIT", "Letter of Credit", 70),
    ("PRODUCT_CATEGORY", "BANK_GUARANTEE", "Bank Guarantee", 80),
    ("PRODUCT_CATEGORY", "BILL_DISCOUNTING", "Bill Discounting", 90),
    ("RATE_TYPE", "FIXED", "Fixed Rate", 10),
    ("RATE_TYPE", "FLOATING", "Floating Rate", 20),
    ("REPAYMENT_FREQUENCY", "MONTHLY", "Monthly", 10),
    ("REPAYMENT_FREQUENCY", "QUARTERLY", "Quarterly", 20),
    ("REPAYMENT_FREQUENCY", "HALF_YEARLY", "Half-Yearly", 30),
    ("REPAYMENT_FREQUENCY", "YEARLY", "Yearly", 40),
    ("REPAYMENT_FREQUENCY", "BULLET", "Bullet", 50),
    ("REPAYMENT_MODE", "EMI", "Equated Monthly Instalment", 10),
    ("REPAYMENT_MODE", "STRUCTURED", "Structured Repayment", 20),
    ("REPAYMENT_MODE", "BULLET", "Bullet Repayment", 30),
    ("REPAYMENT_MODE", "BALLOON", "Balloon Repayment", 40),
    ("REPAYMENT_MODE", "STEP_UP", "Step-Up Repayment", 50),
    ("REPAYMENT_MODE", "STEP_DOWN", "Step-Down Repayment", 60),
    ("SECURITY_TYPE", "SECURED", "Secured", 10),
    ("SECURITY_TYPE", "UNSECURED", "Unsecured", 20),
    ("RATING_AGENCY", "CRISIL", "CRISIL", 10),
    ("RATING_AGENCY", "ICRA", "ICRA", 20),
    ("RATING_AGENCY", "CARE", "CARE Ratings", 30),
    ("RATING_AGENCY", "INDIA_RATINGS", "India Ratings", 40),
    ("RATING_AGENCY", "ACUITE", "Acuite Ratings", 50),
    ("RATING_AGENCY", "BRICKWORK", "Brickwork Ratings", 60),
    ("RATING_AGENCY", "OTHER", "Other", 990),
    ("ENTITY_TYPE_CORPORATE", "CORPORATE", "Company / Corporate", 10),
    ("ENTITY_TYPE_CORPORATE", "LLP", "Limited Liability Partnership", 20),
    ("ENTITY_TYPE_CORPORATE", "PARTNERSHIP", "Partnership Firm", 30),
    ("ENTITY_TYPE_CORPORATE", "GOVT_ENTITY", "Government Entity / PSU", 40),
    ("ENTITY_TYPE_CORPORATE", "SPV", "Special Purpose Vehicle", 50),
    ("INDUSTRY_SECTOR", "SHIPBUILDING", "Shipbuilding", 10),
    ("INDUSTRY_SECTOR", "SHIP_REPAIR", "Ship Repair", 20),
    ("INDUSTRY_SECTOR", "PORT_INFRA", "Port Infrastructure", 30),
    ("INDUSTRY_SECTOR", "INLAND_WATERWAYS", "Inland Waterways", 40),
    ("INDUSTRY_SECTOR", "MARITIME_ANCILLARY", "Maritime Ancillary", 50),
    ("MARITIME_SEGMENT", "SHIPBUILDING", "Shipbuilding", 10),
    ("MARITIME_SEGMENT", "SHIP_REPAIR", "Ship Repair", 20),
    ("MARITIME_SEGMENT", "PORT_LOGISTICS", "Port Logistics", 30),
    ("MARITIME_SEGMENT", "DREDGING", "Dredging", 40),
    ("MARITIME_SEGMENT", "COASTAL_SHIPPING", "Coastal Shipping", 50),
    ("RISK_GRADE", "LOW", "Low Risk", 10),
    ("RISK_GRADE", "MEDIUM", "Medium Risk", 20),
    ("RISK_GRADE", "HIGH", "High Risk", 30),
    ("RISK_GRADE", "WATCHLIST", "Watchlist", 40),
    ("KYC_DOCUMENT_TYPE", "PAN", "PAN", 10),
    ("KYC_DOCUMENT_TYPE", "CIN", "Corporate Identity Number", 20),
    ("KYC_DOCUMENT_TYPE", "GSTIN", "GST Registration", 30),
    ("KYC_DOCUMENT_TYPE", "MOA_AOA", "MoA / AoA", 40),
    ("KYC_DOCUMENT_TYPE", "BOARD_RESOLUTION", "Board Resolution", 50),
    ("CONTACT_TYPE", "AUTHORIZED_SIGNATORY", "Authorized Signatory", 10),
    ("CONTACT_TYPE", "FINANCE_CONTACT", "Finance Contact", 20),
    ("CONTACT_TYPE", "TECHNICAL_CONTACT", "Technical Contact", 30),
    ("CONTACT_TYPE", "PROMOTER_DIRECTOR", "Promoter / Director", 40),
    ("ADDRESS_TYPE", "REGISTERED_OFFICE", "Registered Office", 10),
    ("ADDRESS_TYPE", "CORPORATE_OFFICE", "Corporate Office", 20),
    ("ADDRESS_TYPE", "PROJECT_SITE", "Project Site", 30),
    ("ADDRESS_TYPE", "COMMUNICATION", "Communication Address", 40),
    ("BANK_ACCOUNT_TYPE", "CURRENT", "Current Account", 10),
    ("BANK_ACCOUNT_TYPE", "ESCROW", "Escrow Account", 20),
    ("BANK_ACCOUNT_TYPE", "TRA_ACCOUNT", "Trust and Retention Account", 30),
    ("APPLICATION_PURPOSE", "CAPEX", "Capital Expenditure", 10),
    ("APPLICATION_PURPOSE", "PROJECT_FINANCE", "Project Finance", 20),
    ("APPLICATION_PURPOSE", "WORKING_CAPITAL", "Working Capital", 30),
    ("APPLICATION_PURPOSE", "REFINANCE", "Refinance", 40),
    ("RATE_RESET_FREQUENCY", "MONTHLY", "Monthly", 10),
    ("RATE_RESET_FREQUENCY", "QUARTERLY", "Quarterly", 20),
    ("RATE_RESET_FREQUENCY", "HALF_YEARLY", "Half-Yearly", 30),
    ("RATE_RESET_FREQUENCY", "YEARLY", "Yearly", 40),
    ("INTEREST_CALCULATION_METHOD", "REDUCING_BALANCE", "Reducing Balance", 10),
    ("INTEREST_CALCULATION_METHOD", "SIMPLE_INTEREST", "Simple Interest", 20),
    ("INTEREST_CALCULATION_METHOD", "DAILY_ACCRUAL", "Daily Accrual", 30),
    ("INTEREST_COMPOUNDING", "NONE", "No Compounding", 10),
    ("INTEREST_COMPOUNDING", "MONTHLY", "Monthly", 20),
    ("INTEREST_COMPOUNDING", "QUARTERLY", "Quarterly", 30),
    ("MORATORIUM_TYPE", "NONE", "No Moratorium", 10),
    ("MORATORIUM_TYPE", "PRINCIPAL_ONLY", "Principal Moratorium", 20),
    ("MORATORIUM_TYPE", "PRINCIPAL_AND_INTEREST", "Principal and Interest Moratorium", 30),
    ("SCHEDULE_CALCULATION_METHOD", "EMI", "Equated Instalment", 10),
    ("SCHEDULE_CALCULATION_METHOD", "EPI", "Equated Principal Instalment", 20),
    ("SCHEDULE_CALCULATION_METHOD", "STRUCTURED", "Structured / Sculpted", 30),
    ("SCHEDULE_CALCULATION_METHOD", "BULLET", "Bullet", 40),
    ("SECURITY_CATEGORY", "IMMOVABLE_PROPERTY", "Immovable Property", 10),
    ("SECURITY_CATEGORY", "VESSEL", "Vessel", 20),
    ("SECURITY_CATEGORY", "EQUIPMENT", "Plant and Machinery", 30),
    ("SECURITY_CATEGORY", "RECEIVABLES", "Receivables Assignment", 40),
    ("SECURITY_CATEGORY", "GUARANTEE", "Guarantee", 50),
    ("SECURITY_NATURE", "PRIMARY", "Primary Security", 10),
    ("SECURITY_NATURE", "COLLATERAL", "Collateral Security", 20),
    ("SECURITY_NATURE", "ADDITIONAL", "Additional Security", 30),
    ("CHARGE_TYPE", "HYPOTHECATION", "Hypothecation", 10),
    ("CHARGE_TYPE", "MORTGAGE", "Mortgage", 20),
    ("CHARGE_TYPE", "PLEDGE", "Pledge", 30),
    ("CHARGE_TYPE", "ASSIGNMENT", "Assignment", 40),
    ("CHARGE_TYPE", "FIRST", "First Charge", 50),
    ("CHARGE_TYPE", "SECOND", "Second Charge", 60),
    ("CHARGE_TYPE", "PARI_PASSU", "Pari Passu Charge", 70),
    ("CHARGE_TYPE", "SUBSERVIENT", "Subservient Charge", 80),
    ("VALUATION_METHOD", "MARKET_VALUE", "Market Value", 10),
    ("VALUATION_METHOD", "DISTRESS_VALUE", "Distress Value", 20),
    ("VALUATION_METHOD", "BOOK_VALUE", "Book Value", 30),
    ("AREA_UNIT", "SQ_FT", "Square Feet", 10),
    ("AREA_UNIT", "SQ_M", "Square Metres", 20),
    ("AREA_UNIT", "ACRE", "Acre", 30),
    ("COLLATERAL_DOCUMENT_TYPE", "TITLE_DEED", "Title Deed", 10),
    ("COLLATERAL_DOCUMENT_TYPE", "VALUATION_REPORT", "Valuation Report", 20),
    ("COLLATERAL_DOCUMENT_TYPE", "LEGAL_OPINION", "Legal Opinion", 30),
    ("COLLATERAL_DOCUMENT_TYPE", "INSURANCE_POLICY", "Insurance Policy", 40),
    ("CONDITION_TYPE", "CONDITION_PRECEDENT", "Condition Precedent", 10),
    ("CONDITION_TYPE", "CONDITION_SUBSEQUENT", "Condition Subsequent", 20),
    ("CONDITION_TYPE", "SPECIAL_CONDITION", "Special Condition", 30),
    ("CONDITION_CATEGORY", "LEGAL", "Legal", 10),
    ("CONDITION_CATEGORY", "FINANCIAL", "Financial", 20),
    ("CONDITION_CATEGORY", "SECURITY", "Security", 30),
    ("CONDITION_CATEGORY", "COMPLIANCE", "Compliance", 40),
    ("COVENANT_TYPE", "FINANCIAL", "Financial Covenant", 10),
    ("COVENANT_TYPE", "OPERATIONAL", "Operational Covenant", 20),
    ("COVENANT_TYPE", "REPORTING", "Reporting Covenant", 30),
    ("COVENANT_TYPE", "NEGATIVE", "Negative Covenant", 40),
    ("COVENANT_FREQUENCY", "MONTHLY", "Monthly", 10),
    ("COVENANT_FREQUENCY", "QUARTERLY", "Quarterly", 20),
    ("COVENANT_FREQUENCY", "HALF_YEARLY", "Half-Yearly", 30),
    ("COVENANT_FREQUENCY", "YEARLY", "Yearly", 40),
    ("COVENANT_FREQUENCY", "EVENT_BASED", "Event Based", 50),
    ("WAIVER_AUTHORITY", "CREDIT_HEAD", "Credit Head", 10),
    ("WAIVER_AUTHORITY", "CFO", "CFO", 20),
    ("WAIVER_AUTHORITY", "BOARD", "Board / Committee", 30),
    ("DISBURSEMENT_TYPE", "INITIAL", "Initial Disbursement", 10),
    ("DISBURSEMENT_TYPE", "TRANCHE", "Tranche Disbursement", 20),
    ("DISBURSEMENT_TYPE", "REIMBURSEMENT", "Reimbursement", 30),
    ("DISBURSEMENT_MODE", "NEFT", "NEFT", 10),
    ("DISBURSEMENT_MODE", "RTGS", "RTGS", 20),
    ("DISBURSEMENT_MODE", "CHEQUE", "Cheque", 30),
    ("RECEIPT_TYPE", "INSTALMENT", "Instalment", 10),
    ("RECEIPT_TYPE", "PREPAYMENT", "Prepayment", 20),
    ("RECEIPT_TYPE", "CHARGES", "Charges", 30),
    ("RECEIPT_MODE", "NEFT", "NEFT", 10),
    ("RECEIPT_MODE", "RTGS", "RTGS", 20),
    ("RECEIPT_MODE", "CHEQUE", "Cheque", 30),
    ("OTS_PAYMENT_MODE", "LUMP_SUM", "Lump Sum", 10),
    ("OTS_PAYMENT_MODE", "INSTALLMENTS", "Installments", 20),
    ("OTS_PAYMENT_MODE", "HYBRID", "Upfront + Installments", 30),
    ("RESTRUCTURE_TYPE", "TENURE_EXTENSION", "Tenure Extension", 10),
    ("RESTRUCTURE_TYPE", "EMI_REDUCTION", "Instalment Reduction", 20),
    ("RESTRUCTURE_TYPE", "MORATORIUM", "Moratorium", 30),
    ("RESTRUCTURE_TYPE", "RATE_REDUCTION", "Rate Reduction", 40),
    ("RESTRUCTURE_TYPE", "PRINCIPAL_HAIRCUT", "Principal Haircut", 50),
    ("RESTRUCTURE_TYPE", "INTEREST_WAIVER", "Interest Waiver", 60),
    ("RESTRUCTURE_TYPE", "COMPREHENSIVE", "Comprehensive", 70),
    ("RESTRUCTURE_TYPE", "COVID_RESTRUCTURE", "COVID Restructure", 80),
    ("MORATORIUM_INTEREST_TREATMENT", "CAPITALIZE", "Capitalize into Principal", 10),
    ("MORATORIUM_INTEREST_TREATMENT", "DEFER", "Defer and Collect Later", 20),
    ("MORATORIUM_INTEREST_TREATMENT", "WAIVE", "Waive", 30),
    ("APPROVAL_AUTHORITY", "GM_CREDIT", "GM Credit", 10),
    ("APPROVAL_AUTHORITY", "DGM_CREDIT", "DGM Credit", 20),
    ("APPROVAL_AUTHORITY", "AGM_CREDIT", "AGM Credit", 30),
    ("APPROVAL_AUTHORITY", "CREDIT_COMMITTEE", "Credit Committee", 40),
    ("APPROVAL_AUTHORITY", "BOARD", "Board", 50),
    ("FOLLOW_UP_TYPE", "CALL", "Call", 10),
    ("FOLLOW_UP_TYPE", "EMAIL", "Email", 20),
    ("FOLLOW_UP_TYPE", "MEETING", "Meeting", 30),
    ("FOLLOW_UP_TYPE", "FIELD_VISIT", "Field Visit", 40),
    ("LEGAL_CASE_TYPE", "SARFAESI", "SARFAESI", 10),
    ("LEGAL_CASE_TYPE", "DRT", "DRT", 20),
    ("LEGAL_CASE_TYPE", "NCLT", "NCLT", 30),
    ("LEGAL_CASE_TYPE", "ARBITRATION", "Arbitration", 40),
    ("IIF_ELIGIBLE_LOAN_TYPE", "TERM_LOAN_CAPEX", "Term Loan - Capex", 10),
    ("IIF_ELIGIBLE_LOAN_TYPE", "PROJECT_FINANCE", "Project Finance", 20),
    ("IIF_ELIGIBLE_LOAN_TYPE", "WORKING_CAPITAL", "Working Capital", 30),
    ("IIF_CLAIM_FREQUENCY", "MONTHLY", "Monthly", 10),
    ("IIF_CLAIM_FREQUENCY", "QUARTERLY", "Quarterly", 20),
    ("IIF_CLAIM_FREQUENCY", "HALF_YEARLY", "Half-Yearly", 30),
    ("IIF_CLAIM_FREQUENCY", "YEARLY", "Yearly", 40),
    ("IIF_CLAIM_DOCUMENT_TYPE", "INTEREST_CERTIFICATE", "Interest Certificate", 10),
    ("IIF_CLAIM_DOCUMENT_TYPE", "REPAYMENT_PROOF", "Repayment Proof", 20),
    ("IIF_CLAIM_DOCUMENT_TYPE", "CA_CERTIFICATE", "CA Certificate", 30),
    ("COLLECTION_AGEING_BUCKET", "CURRENT", "Current", 10),
    ("COLLECTION_AGEING_BUCKET", "1_30", "1-30 DPD", 20),
    ("COLLECTION_AGEING_BUCKET", "31_60", "31-60 DPD", 30),
    ("COLLECTION_AGEING_BUCKET", "61_90", "61-90 DPD", 40),
    ("COLLECTION_AGEING_BUCKET", "90_PLUS", "90+ DPD", 50),
    ("ALM_BUCKET", "1_7_DAYS", "1-7 days", 10),
    ("ALM_BUCKET", "8_14_DAYS", "8-14 days", 20),
    ("ALM_BUCKET", "15_30_DAYS", "15-30 days", 30),
    ("ALM_BUCKET", "31_60_DAYS", "31-60 days", 40),
    ("ALM_BUCKET", "61_90_DAYS", "61-90 days", 50),
    ("ALM_BUCKET", "91_180_DAYS", "91-180 days", 60),
    ("ALM_BUCKET", "181_365_DAYS", "181-365 days", 70),
    ("ALM_BUCKET", "1_3_YEARS", "1-3 years", 80),
    ("ALM_BUCKET", "3_5_YEARS", "3-5 years", 90),
    ("ALM_BUCKET", "OVER_5_YEARS", "Over 5 years", 100),
    ("IRS_SHOCK_SCENARIO", "DOWN_200_BPS", "-200 bps", 10),
    ("IRS_SHOCK_SCENARIO", "DOWN_100_BPS", "-100 bps", 20),
    ("IRS_SHOCK_SCENARIO", "UP_100_BPS", "+100 bps", 30),
    ("IRS_SHOCK_SCENARIO", "UP_200_BPS", "+200 bps", 40),
]


# ============================================================================
# 11. NACH return reason codes (NPCI)
# ============================================================================

_NACH_RETURN_REASONS = [
    ("01", "Account closed", "ACCOUNT_RELATED", False, True),
    ("02", "No such account", "ACCOUNT_RELATED", False, True),
    ("03", "Account blocked / frozen", "ACCOUNT_RELATED", False, True),
    ("04", "Customer signature differs", "TECHNICAL", True, True),
    ("05", "Payment stopped by drawer", "MANDATE_RELATED", False, True),
    ("06", "Payment stopped by attachment", "MANDATE_RELATED", False, True),
    ("07", "Insufficient funds", "INSUFFICIENT_FUNDS", True, True),
    ("08", "Funds insufficient — refer to drawer", "INSUFFICIENT_FUNDS", True, True),
    ("09", "Account inoperative", "ACCOUNT_RELATED", False, True),
    ("10", "Mandate not registered", "MANDATE_RELATED", False, True),
    ("11", "Mandate cancelled", "MANDATE_RELATED", False, True),
    ("12", "Mandate expired", "MANDATE_RELATED", False, True),
    ("13", "Image not clear", "TECHNICAL", True, False),
    ("14", "Amount payable per mandate exceeds limit", "MANDATE_RELATED", False, True),
    ("15", "Account type does not match mandate", "MANDATE_RELATED", False, True),
    ("16", "Other reason", "OTHER", False, True),
]


# ============================================================================
# Seed runner
# ============================================================================


async def seed_for_organization(session: AsyncSession, organization_id: UUID) -> dict[str, int]:
    """Seed all 21 masters for one organization. Returns counts per table."""
    counts: dict[str, int] = {}

    async def _exists(model, **filters) -> bool:
        stmt = select(model).filter_by(**filters).limit(1)
        return (await session.execute(stmt)).scalar_one_or_none() is not None

    # 1. Asset classes
    inserted = 0
    for row in _ASSET_CLASSES:
        if await _exists(AssetClass, organization_id=organization_id, code=row["code"]):
            continue
        session.add(
            AssetClass(
                organization_id=organization_id,
                code=row["code"],
                name=row["name"],
                description=row.get("description"),
                details_schema=row.get("details_schema", {}),
                valuation_required=row.get("valuation_required", True),
                valuation_frequency_months=row.get("valuation_frequency_months", 12),
                insurance_required=row.get("insurance_required", True),
                mandatory_insurance_types=row.get("mandatory_insurance_types", []),
                registration_authority_code=row.get("registration_authority_code"),
                default_provisioning_band=row.get("default_provisioning_band"),
                sort_order=row.get("sort_order", 0),
                is_system=True,
            )
        )
        inserted += 1
    counts["asset_class"] = inserted

    # 2. Lifecycle event catalog
    inserted = 0
    for row in _LIFECYCLE_EVENT_CATALOG:
        if await _exists(LifecycleEventCatalog, organization_id=organization_id, code=row["code"]):
            continue
        session.add(
            LifecycleEventCatalog(
                organization_id=organization_id,
                code=row["code"],
                label=row["label"],
                phase=row.get("phase"),
                is_borrower_visible_default=row.get("borrower_visible", False),
                regulatory_tags=row.get("regulatory_tags", []),
                is_system=True,
            )
        )
        inserted += 1
    counts["lifecycle_event_catalog"] = inserted

    # 3. Insurance types
    inserted = 0
    for code, name, desc in _INSURANCE_TYPES:
        if await _exists(InsuranceType, organization_id=organization_id, code=code):
            continue
        session.add(
            InsuranceType(
                organization_id=organization_id,
                code=code,
                name=name,
                description=desc,
                is_system=True,
            )
        )
        inserted += 1
    counts["insurance_type"] = inserted

    # 4. Registration authorities
    inserted = 0
    for code, name, url in _REGISTRATION_AUTHORITIES:
        if await _exists(RegistrationAuthority, organization_id=organization_id, code=code):
            continue
        session.add(
            RegistrationAuthority(
                organization_id=organization_id,
                code=code,
                name=name,
                portal_url=url,
                is_system=True,
            )
        )
        inserted += 1
    counts["registration_authority"] = inserted

    # 5. Fee types
    inserted = 0
    for code, name, stage, gst, gst_rate, refundable in _FEE_TYPES:
        if await _exists(FeeType, organization_id=organization_id, code=code):
            continue
        session.add(
            FeeType(
                organization_id=organization_id,
                code=code,
                name=name,
                is_gst_applicable=gst,
                gst_rate_percent=Decimal(gst_rate),
                is_refundable=refundable,
                collection_stage=stage,
                is_system=True,
            )
        )
        inserted += 1
    counts["fee_type"] = inserted

    # 5b. Fee GL mapping — one placeholder row per fee type with NULL GL
    # accounts. This gives operators a concrete punch-list of mappings to
    # fill in once their chart of accounts is set up. Without this, the
    # admin UI wouldn't know which fee types need mapping.
    inserted = 0
    for code, _name, _stage, _gst, _gst_rate, _refundable in _FEE_TYPES:
        if await _exists(FeeGlMapping, organization_id=organization_id, fee_type_code=code):
            continue
        session.add(
            FeeGlMapping(
                organization_id=organization_id,
                fee_type_code=code,
                income_account_id=None,
                receivable_account_id=None,
                gst_payable_account_id=None,
                notes="Map to tenant chart of accounts before posting accrues.",
            )
        )
        inserted += 1
    counts["fee_gl_mapping"] = inserted

    # 6. Default penal-charge policy (one baseline row)
    if not await _exists(PenalChargePolicy, organization_id=organization_id, code="DEFAULT"):
        session.add(
            PenalChargePolicy(
                organization_id=organization_id,
                code="DEFAULT",
                description="RBI Apr-2024 compliant baseline — flat penal charge per missed instalment, not capitalisable.",
                flat_amount=Decimal("500.00"),
                percent_of_overdue=Decimal("0"),
                grace_days=5,
                is_capitalisable=False,
                effective_from=_DEFAULT_EFFECTIVE_FROM,
                is_system=True,
            )
        )
        counts["penal_charge_policy"] = 1
    else:
        counts["penal_charge_policy"] = 0

    # 7. Checklist item catalog
    inserted = 0
    for code, label, category, stage, mandatory, expiry in _CHECKLIST_ITEMS:
        if await _exists(ChecklistItemCatalog, organization_id=organization_id, code=code):
            continue
        session.add(
            ChecklistItemCatalog(
                organization_id=organization_id,
                code=code,
                label=label,
                category=category,
                stage=stage,
                is_mandatory_default=mandatory,
                expiry_days=expiry,
                is_system=True,
            )
        )
        inserted += 1
    counts["checklist_item_catalog"] = inserted

    # 8. NPA buckets
    inserted = 0
    for code, label, classification, min_dpd, max_dpd, sort_order in _NPA_BUCKETS:
        if await _exists(
            NpaBucket,
            organization_id=organization_id,
            code=code,
            effective_from=_DEFAULT_EFFECTIVE_FROM,
        ):
            continue
        session.add(
            NpaBucket(
                organization_id=organization_id,
                code=code,
                label=label,
                asset_classification=classification,
                min_dpd=min_dpd,
                max_dpd=max_dpd,
                sort_order=sort_order,
                effective_from=_DEFAULT_EFFECTIVE_FROM,
                is_system=True,
            )
        )
        inserted += 1
    counts["npa_bucket"] = inserted

    # 9. Provisioning rates
    inserted = 0
    for classification, secured, segment, rate in _PROVISIONING_RATES:
        if await _exists(
            ProvisioningRate,
            organization_id=organization_id,
            asset_classification=classification,
            secured_unsecured=secured,
            loan_segment=segment,
            effective_from=_DEFAULT_EFFECTIVE_FROM,
        ):
            continue
        session.add(
            ProvisioningRate(
                organization_id=organization_id,
                asset_classification=classification,
                secured_unsecured=secured,
                loan_segment=segment,
                rate_percent=rate,
                effective_from=_DEFAULT_EFFECTIVE_FROM,
                is_system=True,
            )
        )
        inserted += 1
    counts["provisioning_rate"] = inserted

    # 10. Day count
    inserted = 0
    for code, name, days, desc in _DAY_COUNT:
        if await _exists(DayCountConvention, organization_id=organization_id, code=code):
            continue
        session.add(
            DayCountConvention(
                organization_id=organization_id,
                code=code,
                name=name,
                days_in_year=days,
                description=desc,
                is_system=True,
            )
        )
        inserted += 1
    counts["day_count_convention"] = inserted

    # 11. Approval matrix — 5 bands
    inserted = 0
    bands = [
        (Decimal("0"), Decimal("10000000"), "CREDIT_OFFICER", 24),
        (Decimal("10000001"), Decimal("50000000"), "CREDIT_MANAGER", 48),
        (Decimal("50000001"), Decimal("250000000"), "GM_CREDIT", 72),
        (Decimal("250000001"), Decimal("1000000000"), "ED", 120),
        (Decimal("1000000001"), None, "BOARD", 240),
    ]
    for action in (
        "SANCTION_APPROVE",
        "DISBURSEMENT_APPROVE",
        "OTS_APPROVE",
        "RESTRUCTURE_APPROVE",
        "WRITE_OFF_APPROVE",
        "INTEREST_REVIVAL_APPROVE",
    ):
        for band_min, band_max, role, sla in bands:
            if await _exists(
                ApprovalMatrix,
                organization_id=organization_id,
                action_code=action,
                band_min=band_min,
                effective_from=_DEFAULT_EFFECTIVE_FROM,
            ):
                continue
            session.add(
                ApprovalMatrix(
                    organization_id=organization_id,
                    action_code=action,
                    band_min=band_min,
                    band_max=band_max,
                    authority_role=role,
                    requires_maker_checker=True,
                    sla_hours=sla,
                    effective_from=_DEFAULT_EFFECTIVE_FROM,
                    is_system=True,
                )
            )
            inserted += 1
    counts["approval_matrix"] = inserted

    # 12. SLA matrix — defaults from FPC
    inserted = 0
    for stage, action, tat in [
        ("APPLICATION", "INTAKE_REVIEW", 24),
        ("APPRAISAL", "CREDIT_REVIEW", 72),
        ("SANCTION", "APPROVE", 120),
        ("SANCTION", "KFS_ISSUE", 24),
        ("DISBURSEMENT", "PROCESS", 48),
        ("SERVICING", "STATEMENT_REQUEST", 24),
        ("SERVICING", "FORECLOSURE_QUOTE", 48),
        ("CLOSURE", "NDC_ISSUANCE", 168),
        ("CLOSURE", "DOC_RELEASE", 720),  # 30 days per RBI
    ]:
        if await _exists(
            SLAMatrix,
            organization_id=organization_id,
            stage=stage,
            action_code=action,
            product_code="DEFAULT",
        ):
            continue
        session.add(
            SLAMatrix(
                organization_id=organization_id,
                stage=stage,
                action_code=action,
                tat_hours=tat,
                is_system=True,
            )
        )
        inserted += 1
    counts["sla_matrix"] = inserted

    # 13. Document templates — short stubs; operator extends via admin UI
    inserted = 0
    document_templates = [
        (
            "KFS",
            "Key Facts Statement",
            "# Key Facts Statement\n\n{{borrower_name}} — Loan {{loan_account_number}}\n\nSee Annex A of RBI master direction 15 Apr 2024.",
        ),
        (
            "SANCTION_LETTER",
            "Sanction letter",
            "# Sanction Letter\n\nDear {{borrower_name}},\n\nWe are pleased to sanction a loan of {{sanctioned_amount}} on the terms specified.",
        ),
        (
            "WELCOME_LETTER",
            "Welcome letter",
            "# Welcome\n\nDear {{borrower_name}},\n\nYour loan account {{loan_account_number}} is now active.",
        ),
        (
            "INTEREST_CERT",
            "Interest certificate (24B)",
            "# Interest Certificate FY {{financial_year}}\n\nIssued to {{borrower_name}} (PAN {{borrower_pan}}) for loan {{loan_account_number}}.",
        ),
        (
            "PROVISIONAL_INTEREST_CERT",
            "Provisional interest certificate",
            "# Provisional Interest Certificate\n\nProjected for FY {{financial_year}}.",
        ),
        ("PRINCIPAL_PAID_CERT", "Principal-paid certificate", "# Principal Paid Certificate"),
        (
            "NDC",
            "No-dues certificate",
            "# No-Dues Certificate\n\nThis is to certify that {{borrower_name}}'s loan account {{loan_account_number}} has been fully settled as on {{closure_date}}.",
        ),
        (
            "FORECLOSURE_LETTER",
            "Foreclosure / outstanding letter",
            "# Foreclosure Letter\n\nOutstanding as on {{quote_date}} for loan {{loan_account_number}}: {{total_outstanding}}.",
        ),
        (
            "BALANCE_CONFIRMATION",
            "Balance confirmation",
            "# Balance Confirmation as on {{as_of_date}}",
        ),
        (
            "CHARGE_RELEASE_LETTER",
            "Charge release letter",
            "# Charge Release\n\nWe confirm that the charges on your assets have been released.",
        ),
        (
            "ANNUAL_LOAN_STATEMENT",
            "Annual loan statement",
            "# Annual Loan Statement FY {{financial_year}}",
        ),
        (
            "RATE_REVISION_INTIMATION",
            "Rate revision intimation",
            "# Rate Revision\n\nYour loan's interest rate has been revised from {{old_rate}}% to {{new_rate}}% effective {{effective_from}}.",
        ),
        (
            "DEMAND_NOTICE",
            "Demand notice",
            "# Demand Notice\n\nYou are hereby called upon to pay {{overdue_amount}} within 7 days.",
        ),
        (
            "SARFAESI_13_2_NOTICE",
            "SARFAESI 13(2) demand notice",
            "# Notice under Section 13(2) SARFAESI Act, 2002",
        ),
        ("OTS_LETTER", "OTS sanction letter", "# One-Time Settlement Letter"),
        (
            "RESTRUCTURE_ADDENDUM",
            "Restructure addendum",
            "# Restructure Addendum to Loan Agreement",
        ),
        (
            "WILFUL_DEFAULTER_NOTICE",
            "Wilful defaulter show-cause notice",
            "# Show-cause Notice — Wilful Defaulter",
        ),
        (
            "STATEMENT_OF_ACCOUNT",
            "Statement of account",
            "# Statement of Account {{from_date}} to {{to_date}}",
        ),
    ]
    for code, name, body in document_templates:
        if await _exists(
            DocumentTemplate,
            organization_id=organization_id,
            code=code,
            template_version=1,
            locale="en",
        ):
            continue
        session.add(
            DocumentTemplate(
                organization_id=organization_id,
                code=code,
                name=name,
                body=body,
                body_format="MARKDOWN",
                locale="en",
                template_version=1,
                is_current=True,
                is_system=True,
            )
        )
        inserted += 1
    counts["document_template"] = inserted

    # 14. Communication templates — one per major borrower-facing event
    inserted = 0
    comm_templates = [
        (
            "APPLICATION_SUBMITTED",
            "EMAIL",
            "Application received",
            "Dear {{borrower_name}}, your loan application {{application_number}} has been received. We will reach out with next steps.",
        ),
        (
            "APPLICATION_SUBMITTED",
            "SMS",
            None,
            "Loan application {{application_number}} received. We'll be in touch.",
        ),
        (
            "QUERY_RAISED",
            "EMAIL",
            "We need more information",
            "Dear {{borrower_name}}, the credit team has raised a query on your application. Please log in to respond.",
        ),
        (
            "QUERY_RAISED",
            "SMS",
            None,
            "A query was raised on your loan application. Log in to respond: {{portal_url}}",
        ),
        (
            "KFS_ISSUED",
            "EMAIL",
            "Key Facts Statement issued",
            "Dear {{borrower_name}}, please review the Key Facts Statement attached to this email. Acknowledge it on the portal to proceed.",
        ),
        (
            "KFS_ISSUED",
            "SMS",
            None,
            "KFS issued for loan {{application_number}}. Acknowledge on portal to proceed.",
        ),
        (
            "SANCTION_APPROVED",
            "EMAIL",
            "Loan sanctioned",
            "Dear {{borrower_name}}, your loan has been sanctioned. Sanction letter attached.",
        ),
        (
            "SANCTION_APPROVED",
            "SMS",
            None,
            "Your loan {{application_number}} is sanctioned. Check email for sanction letter.",
        ),
        (
            "DISBURSEMENT_PROCESSED",
            "EMAIL",
            "Disbursement processed",
            "Dear {{borrower_name}}, disbursement of {{amount}} has been processed. UTR: {{utr_number}}.",
        ),
        (
            "DISBURSEMENT_PROCESSED",
            "SMS",
            None,
            "Disbursement {{amount}} processed for loan {{loan_account_number}}. UTR {{utr_number}}.",
        ),
        (
            "RECEIPT_BOUNCED",
            "EMAIL",
            "Payment bounced",
            "Dear {{borrower_name}}, your payment of {{amount}} bounced. Please ensure funds are available.",
        ),
        (
            "RECEIPT_BOUNCED",
            "SMS",
            None,
            "Your payment for loan {{loan_account_number}} bounced. Reason: {{bounce_reason}}.",
        ),
        (
            "NACH_BOUNCED",
            "SMS",
            None,
            "NACH presentation for loan {{loan_account_number}} bounced. Reason: {{bounce_reason}}. Charge applicable.",
        ),
        (
            "RATE_RESET_DUE",
            "EMAIL",
            "Your loan's interest rate will be reset",
            "Dear {{borrower_name}}, your floating-rate loan {{loan_account_number}} is due for a rate reset on {{reset_date}}. New rate: {{new_rate}}%.",
        ),
        (
            "FORECLOSURE_QUOTE_ISSUED",
            "EMAIL",
            "Foreclosure quote",
            "Dear {{borrower_name}}, the foreclosure quote for your loan is attached. Valid till {{valid_till}}.",
        ),
        (
            "NDC_ISSUED",
            "EMAIL",
            "No-dues certificate",
            "Dear {{borrower_name}}, your No-Dues Certificate for loan {{loan_account_number}} is attached.",
        ),
        (
            "VENDOR_PORTAL_OTP",
            "SMS",
            None,
            "Your verification code is {{otp_code}}. Valid for {{expiry_minutes}} minutes.",
        ),
        (
            "DEMAND_NOTICE_ISSUED",
            "EMAIL",
            "Demand notice",
            "Dear {{borrower_name}}, please find attached the demand notice for the overdue on your loan.",
        ),
        (
            "ORIGINAL_DOCS_RELEASED",
            "EMAIL",
            "Original documents available for collection",
            "Dear {{borrower_name}}, your original property documents are ready for collection. RBI mandates release within 30 days of closure.",
        ),
        (
            "LEGAL_NOTICE_13_2",
            "EMAIL",
            "SARFAESI 13(2) notice",
            "Dear {{borrower_name}}, please find attached the demand notice under Section 13(2) of SARFAESI Act.",
        ),
        (
            "WRITE_OFF_FINAL",
            "EMAIL",
            "Account closure",
            "Dear {{borrower_name}}, your loan account has been formally closed in our books.",
        ),
        (
            "OTS_BORROWER_ACCEPTED",
            "EMAIL",
            "OTS acceptance confirmed",
            "Dear {{borrower_name}}, your acceptance of the One-Time Settlement has been recorded.",
        ),
        (
            "APPLICATION_REJECTED",
            "EMAIL",
            "Application not approved",
            "Dear {{borrower_name}}, we regret to inform you that your loan application has not been approved at this time.",
        ),
        (
            "TAKEOVER_LETTER_ISSUED",
            "EMAIL",
            "Takeover NoC issued",
            "Dear {{borrower_name}}, the No-Objection Certificate for loan takeover has been issued.",
        ),
    ]
    for event, channel, subject, body in comm_templates:
        if await _exists(
            CommunicationTemplate,
            organization_id=organization_id,
            event_code=event,
            channel=channel,
            locale="en",
            template_version=1,
        ):
            continue
        session.add(
            CommunicationTemplate(
                organization_id=organization_id,
                event_code=event,
                channel=channel,
                locale="en",
                template_version=1,
                is_current=True,
                subject=subject,
                body=body,
                is_system=True,
            )
        )
        inserted += 1
    counts["communication_template"] = inserted

    # 15. Rate reset benchmarks
    inserted = 0
    for code, name, value in _RATE_RESET_BENCHMARKS:
        if await _exists(
            RateResetBenchmark,
            organization_id=organization_id,
            code=code,
            effective_from=_DEFAULT_EFFECTIVE_FROM,
        ):
            continue
        session.add(
            RateResetBenchmark(
                organization_id=organization_id,
                code=code,
                name=name,
                current_value_percent=value,
                effective_from=_DEFAULT_EFFECTIVE_FROM,
                is_system=True,
            )
        )
        inserted += 1
    counts["rate_reset_benchmark"] = inserted

    # 15b. Governed option sets used by treasury and borrowing UI dropdowns
    inserted = 0
    for group, code, label, sort_order in _LENDING_OPTIONS:
        if await _exists(
            LendingOption,
            organization_id=organization_id,
            option_group=group,
            code=code,
        ):
            continue
        session.add(
            LendingOption(
                organization_id=organization_id,
                option_group=group,
                code=code,
                label=label,
                sort_order=sort_order,
                is_system=True,
            )
        )
        inserted += 1
    counts["lending_option"] = inserted

    # 16. Charge trigger rules
    inserted = 0
    for trigger, fee_type, flat in [
        ("NACH_BOUNCED", "NACH_BOUNCE_CHARGE", Decimal("500.00")),
        ("RECEIPT_BOUNCED", "EMI_BOUNCE_CHARGE", Decimal("500.00")),
        ("STATEMENT_ISSUED", "STATEMENT_CHARGE", Decimal("50.00")),
        ("EMI_DATE_CHANGED", "EMI_DATE_CHANGE_CHARGE", Decimal("250.00")),
    ]:
        if await _exists(
            ChargeTriggerRule,
            organization_id=organization_id,
            trigger_event_code=trigger,
            fee_type_code=fee_type,
        ):
            continue
        session.add(
            ChargeTriggerRule(
                organization_id=organization_id,
                trigger_event_code=trigger,
                fee_type_code=fee_type,
                flat_amount=flat,
                apply_gst=True,
                is_active=True,
                is_system=True,
            )
        )
        inserted += 1
    counts["charge_trigger_rule"] = inserted

    # 17. NACH return reasons
    inserted = 0
    for code, desc, category, retry, charge in _NACH_RETURN_REASONS:
        if await _exists(NachReturnReason, organization_id=organization_id, code=code):
            continue
        session.add(
            NachReturnReason(
                organization_id=organization_id,
                code=code,
                description=desc,
                category=category,
                auto_retry_eligible=retry,
                triggers_charge=charge,
                is_system=True,
            )
        )
        inserted += 1
    counts["nach_return_reason"] = inserted

    # 18. Classification override policies — ship one inactive template per
    # historical exception so operators can see the shape and toggle one on
    # if a similar regulator action repeats. These are off by default
    # (`is_active=False` via the standard `is_active` mixin) so they do not
    # silently bend asset-classification math.
    inserted = 0
    for code, name, desc, segment, grace, cap_pct in [
        (
            "COVID_GRACE_2020",
            "COVID-19 90-day grace (Mar-Aug 2020)",
            "Template policy mirroring the Mar-2020 RBI COVID-19 moratorium. "
            "Off by default — toggle on only if a similar dispensation is announced.",
            None,
            90,
            None,
        ),
        (
            "INFRA_PROJECT_GRACE",
            "Infrastructure project grace",
            "Optional grace-period extension for large infrastructure projects "
            "during construction/commissioning. Off by default — operator "
            "activates per project at sanction time.",
            "INFRASTRUCTURE",
            60,
            None,
        ),
        (
            "INTEREST_REVIVAL_CAP_50",
            "Interest revival — 50% cap",
            "Caps the revivable suspended interest at 50% of accrued for OTS "
            "settlements that recover above written-off principal.",
            None,
            0,
            Decimal("50.00"),
        ),
    ]:
        if await _exists(ClassificationOverridePolicy, organization_id=organization_id, code=code):
            continue
        row = ClassificationOverridePolicy(
            organization_id=organization_id,
            code=code,
            name=name,
            description=desc,
            applies_to_segment=segment,
            grace_days_addition=grace,
            revivable_interest_cap_percent=cap_pct,
            effective_from=_DEFAULT_EFFECTIVE_FROM,
            is_system=True,
        )
        # Off by default — operator opts in.
        row.is_active = False
        session.add(row)
        inserted += 1
    counts["classification_override_policy"] = inserted

    await session.flush()
    return counts


async def main(organization_id: UUID | None = None) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        if organization_id is not None:
            org_ids = [organization_id]
        else:
            result = await session.execute(select(Organization.id))
            org_ids = [row[0] for row in result.all()]

        for oid in org_ids:
            counts = await seed_for_organization(session, oid)
            print(f"[seed] org={oid}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))

        await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
