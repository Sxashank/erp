"""
Direct database seed script for Legal Module master data.
Inserts data directly into the database without requiring API authentication.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_legal_data_direct.py
"""

import asyncio
from datetime import date
from decimal import Decimal
from uuid import UUID
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp"
)

# Import models - need to import all models to resolve relationships
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import base first
from app.models.base import BaseModel

# Import all models to register them with SQLAlchemy
from app.models import *  # noqa

# Import lending models (for LegalCase relationship)
from app.models.lending.collections import LegalCase

# Import specific legal models we need
from app.models.legal.statutory_period import StatutoryPeriod
from app.models.legal.notice import NoticeTemplate
from app.models.legal.court import Court, CourtFeeSlab
from app.models.legal.expense import ExpenseCategory


# =============================================================================
# STATUTORY PERIODS DATA
# =============================================================================

STATUTORY_PERIODS = [
    {
        "provision_code": "SARFAESI_13_2",
        "provision_name": "Section 13(2) Demand Notice Response Period",
        "act_name": "SARFAESI Act 2002",
        "section_reference": "Section 13(2)",
        "period_days": 60,
        "period_description": "60 days",
        "start_event": "Date of receipt of demand notice by borrower",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Lender can proceed with possession under Section 13(4)",
        "applicable_forums": ["DRT", "HIGH_COURT"],
        "applicable_case_types": ["SARFAESI"],
        "alert_before_days": [30, 15, 7, 3, 1],
        "legal_reference": "SARFAESI Act 2002, Section 13(2) read with Rule 3",
    },
    {
        "provision_code": "SARFAESI_13_3A",
        "provision_name": "Section 13(3A) Objection Response Period",
        "act_name": "SARFAESI Act 2002",
        "section_reference": "Section 13(3A)",
        "period_days": 15,
        "period_description": "15 days",
        "start_event": "Date of receipt of objection by secured creditor",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "If no response, objection deemed rejected",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["SARFAESI"],
        "alert_before_days": [7, 3, 1],
        "legal_reference": "SARFAESI Act 2002, Section 13(3A)",
    },
    {
        "provision_code": "SARFAESI_13_4",
        "provision_name": "Section 13(4) Possession Notice Period",
        "act_name": "SARFAESI Act 2002",
        "section_reference": "Section 13(4) / Rule 8(1)",
        "period_days": 15,
        "period_description": "15 days",
        "start_event": "Date of affixing possession notice",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Secured creditor can take physical possession after 15 days",
        "applicable_forums": ["DRT", "HIGH_COURT"],
        "applicable_case_types": ["SARFAESI"],
        "alert_before_days": [7, 3, 1],
        "legal_reference": "Security Interest (Enforcement) Rules 2002, Rule 8(1)",
    },
    {
        "provision_code": "SARFAESI_AUCTION_NOTICE",
        "provision_name": "Auction Notice Publication Period",
        "act_name": "SARFAESI Act 2002",
        "section_reference": "Rule 8(6) & 9(1)",
        "period_days": 30,
        "period_description": "30 days",
        "start_event": "Date of publication of sale notice",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "No bids received or operational reasons",
        "consequence": "Sale can be conducted after 30 days from publication",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["SARFAESI"],
        "alert_before_days": [15, 7, 3],
        "legal_reference": "Security Interest (Enforcement) Rules 2002, Rules 8(6) and 9(1)",
    },
    {
        "provision_code": "SARFAESI_17_APPEAL",
        "provision_name": "Section 17 Appeal to DRT",
        "act_name": "SARFAESI Act 2002",
        "section_reference": "Section 17",
        "period_days": 45,
        "period_description": "45 days",
        "start_event": "Date of measure taken by secured creditor",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Sufficient cause shown",
        "consequence": "Right to challenge SARFAESI action may be lost",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["SARFAESI"],
        "alert_before_days": [30, 15, 7, 3],
        "legal_reference": "SARFAESI Act 2002, Section 17",
    },
    {
        "provision_code": "NI_ACT_138_NOTICE",
        "provision_name": "Section 138 Cheque Bounce Notice Period",
        "act_name": "Negotiable Instruments Act 1881",
        "section_reference": "Section 138(b)",
        "period_days": 15,
        "period_description": "15 days",
        "start_event": "Date of receipt of dishonour notice by drawer",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Drawer gets 15 days to make payment",
        "applicable_forums": ["MAGISTRATE_COURT"],
        "applicable_case_types": ["CHEQUE_BOUNCE"],
        "alert_before_days": [7, 3, 1],
        "legal_reference": "NI Act 1881, Section 138(c)",
    },
    {
        "provision_code": "NI_ACT_138_COMPLAINT",
        "provision_name": "Section 138 Complaint Filing Period",
        "act_name": "Negotiable Instruments Act 1881",
        "section_reference": "Section 142",
        "period_days": 30,
        "period_description": "30 days from expiry of notice period",
        "start_event": "Expiry of 15 days notice period",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Sufficient cause as per Section 142(b)",
        "consequence": "Right to file criminal complaint may be lost",
        "applicable_forums": ["MAGISTRATE_COURT"],
        "applicable_case_types": ["CHEQUE_BOUNCE"],
        "alert_before_days": [15, 7, 3],
        "legal_reference": "NI Act 1881, Section 142(b)",
    },
    {
        "provision_code": "DRT_APPLICATION",
        "provision_name": "DRT Application Filing Limitation",
        "act_name": "Recovery of Debts Due to Banks and FIs Act 1993",
        "section_reference": "Section 24",
        "period_days": 1095,
        "period_years": 3,
        "period_description": "3 years",
        "start_event": "Date of cause of action (NPA date)",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Delay can be condoned by DRT",
        "consequence": "Application may be barred by limitation",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["DRT_SUIT"],
        "alert_before_days": [180, 90, 60, 30, 15],
        "legal_reference": "DRT Act 1993, Section 24",
    },
    {
        "provision_code": "DRAT_APPEAL",
        "provision_name": "DRAT Appeal Period",
        "act_name": "Recovery of Debts Due to Banks and FIs Act 1993",
        "section_reference": "Section 20",
        "period_days": 45,
        "period_description": "45 days",
        "start_event": "Date of DRT order",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Delay can be condoned by DRAT",
        "consequence": "Right of appeal may be lost",
        "applicable_forums": ["DRAT"],
        "applicable_case_types": ["DRT_APPEAL"],
        "alert_before_days": [30, 15, 7, 3],
        "legal_reference": "DRT Act 1993, Section 20",
    },
    {
        "provision_code": "DRT_RC_EXECUTION",
        "provision_name": "DRT Recovery Certificate Execution",
        "act_name": "Recovery of Debts Due to Banks and FIs Act 1993",
        "section_reference": "Section 25",
        "period_days": 4380,
        "period_years": 12,
        "period_description": "12 years",
        "start_event": "Date of Recovery Certificate",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Recovery Certificate becomes time-barred",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["EXECUTION"],
        "alert_before_days": [365, 180, 90, 30],
        "legal_reference": "Limitation Act 1963, Article 136",
    },
    {
        "provision_code": "IBC_APPLICATION",
        "provision_name": "IBC Application Filing (Section 7)",
        "act_name": "Insolvency and Bankruptcy Code 2016",
        "section_reference": "Section 7",
        "period_days": 1095,
        "period_years": 3,
        "period_description": "3 years from date of default",
        "start_event": "Date of default",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Application under Section 7 may be time-barred",
        "applicable_forums": ["NCLT"],
        "applicable_case_types": ["IBC"],
        "alert_before_days": [180, 90, 60, 30],
        "legal_reference": "IBC 2016, Section 7",
    },
    {
        "provision_code": "NCLAT_APPEAL",
        "provision_name": "NCLAT Appeal Period",
        "act_name": "Insolvency and Bankruptcy Code 2016",
        "section_reference": "Section 61",
        "period_days": 30,
        "period_description": "30 days (extendable by 15 days)",
        "start_event": "Date of NCLT order",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Further 15 days if sufficient cause shown",
        "consequence": "Right of appeal may be lost",
        "applicable_forums": ["NCLAT"],
        "applicable_case_types": ["IBC_APPEAL"],
        "alert_before_days": [15, 7, 3],
        "legal_reference": "IBC 2016, Section 61(2)",
    },
    {
        "provision_code": "CERSAI_REGISTRATION",
        "provision_name": "CERSAI Registration Timeline",
        "act_name": "SARFAESI Act 2002",
        "section_reference": "Section 23",
        "period_days": 30,
        "period_description": "30 days",
        "start_event": "Date of creation of security interest",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Late fee applicable for delayed registration",
        "consequence": "Late fee penalty; unregistered security loses priority",
        "applicable_forums": [],
        "applicable_case_types": ["ALL"],
        "alert_before_days": [15, 7, 3],
        "legal_reference": "SARFAESI Act 2002, Section 23",
    },
]


# =============================================================================
# NOTICE TEMPLATES DATA
# =============================================================================

NOTICE_TEMPLATES = [
    {
        "template_code": "SARFAESI_13_2_NOTICE",
        "template_name": "Section 13(2) Demand Notice - SARFAESI",
        "notice_type": "SARFAESI_13_2",
        "act_reference": "SARFAESI Act 2002, Section 13(2)",
        "section_reference": "Section 13(2)",
        "statutory_period_days": 60,
        "response_period_days": 60,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": {"fields": ["borrower_name", "loan_account_number", "total_amount", "security_description"]},
        "template_content": "<html><body>SARFAESI Section 13(2) Demand Notice Template</body></html>",
    },
    {
        "template_code": "SARFAESI_13_4_POSSESSION",
        "template_name": "Section 13(4) Possession Notice",
        "notice_type": "SARFAESI_13_4_POSSESSION",
        "act_reference": "SARFAESI Act 2002, Section 13(4)",
        "section_reference": "Section 13(4) / Rule 8",
        "statutory_period_days": 15,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": {"fields": ["borrower_name", "security_address", "total_amount"]},
        "template_content": "<html><body>SARFAESI Possession Notice Template</body></html>",
    },
    {
        "template_code": "SARFAESI_AUCTION_NOTICE",
        "template_name": "Auction/Sale Notice under SARFAESI",
        "notice_type": "SARFAESI_AUCTION",
        "act_reference": "SARFAESI Act 2002, Rule 8(6) and Rule 9",
        "section_reference": "Rule 8(6) & 9",
        "statutory_period_days": 30,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": {"fields": ["reserve_price", "auction_date", "property_description"]},
        "template_content": "<html><body>SARFAESI Auction Notice Template</body></html>",
    },
    {
        "template_code": "NI_ACT_138_NOTICE",
        "template_name": "Section 138 Cheque Bounce Notice",
        "notice_type": "NI_ACT_138",
        "act_reference": "Negotiable Instruments Act 1881, Section 138",
        "section_reference": "Section 138",
        "statutory_period_days": 15,
        "response_period_days": 15,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": {"fields": ["drawer_name", "cheque_number", "cheque_amount"]},
        "template_content": "<html><body>NI Act Section 138 Notice Template</body></html>",
    },
    {
        "template_code": "LOAN_RECALL_NOTICE",
        "template_name": "Loan Recall Notice",
        "notice_type": "RECALL_NOTICE",
        "act_reference": "As per Loan Agreement Terms",
        "section_reference": "Loan Agreement",
        "statutory_period_days": 15,
        "response_period_days": 15,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": {"fields": ["borrower_name", "total_amount", "loan_account_number"]},
        "template_content": "<html><body>Loan Recall Notice Template</body></html>",
    },
]


# =============================================================================
# COURTS DATA
# =============================================================================

COURTS = [
    # DRT - Major cities
    {"court_code": "DRT-DEL-1", "court_name": "Debt Recovery Tribunal-I, New Delhi", "court_type": "DRT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "Delhi NCR", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-DEL-2", "court_name": "Debt Recovery Tribunal-II, New Delhi", "court_type": "DRT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "Delhi NCR", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-MUM-1", "court_name": "Debt Recovery Tribunal-I, Mumbai", "court_type": "DRT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Mumbai Metropolitan", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-MUM-2", "court_name": "Debt Recovery Tribunal-II, Mumbai", "court_type": "DRT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Mumbai Metropolitan", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-CHN-1", "court_name": "Debt Recovery Tribunal-I, Chennai", "court_type": "DRT", "state_code": "TN", "city": "Chennai", "jurisdiction": "Tamil Nadu North", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-KOL-1", "court_name": "Debt Recovery Tribunal-I, Kolkata", "court_type": "DRT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "West Bengal", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-BLR-1", "court_name": "Debt Recovery Tribunal-I, Bengaluru", "court_type": "DRT", "state_code": "KA", "city": "Bengaluru", "jurisdiction": "Karnataka", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-HYD-1", "court_name": "Debt Recovery Tribunal-I, Hyderabad", "court_type": "DRT", "state_code": "TS", "city": "Hyderabad", "jurisdiction": "Telangana", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-AMD-1", "court_name": "Debt Recovery Tribunal-I, Ahmedabad", "court_type": "DRT", "state_code": "GJ", "city": "Ahmedabad", "jurisdiction": "Gujarat", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-PUN", "court_name": "Debt Recovery Tribunal, Pune", "court_type": "DRT", "state_code": "MH", "city": "Pune", "jurisdiction": "Western Maharashtra", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    # DRAT
    {"court_code": "DRAT-DEL", "court_name": "Debt Recovery Appellate Tribunal, Delhi", "court_type": "DRAT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "North India DRTs", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-MUM", "court_name": "Debt Recovery Appellate Tribunal, Mumbai", "court_type": "DRAT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "West India DRTs", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-CHN", "court_name": "Debt Recovery Appellate Tribunal, Chennai", "court_type": "DRAT", "state_code": "TN", "city": "Chennai", "jurisdiction": "South India DRTs", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-KOL", "court_name": "Debt Recovery Appellate Tribunal, Kolkata", "court_type": "DRAT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "East India DRTs", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    # NCLT
    {"court_code": "NCLT-DEL-PB", "court_name": "NCLT Principal Bench, New Delhi", "court_type": "NCLT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "All India Principal", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-MUM", "court_name": "NCLT Mumbai Bench", "court_type": "NCLT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Maharashtra", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-CHN", "court_name": "NCLT Chennai Bench", "court_type": "NCLT", "state_code": "TN", "city": "Chennai", "jurisdiction": "Tamil Nadu", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-KOL", "court_name": "NCLT Kolkata Bench", "court_type": "NCLT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "West Bengal", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-BLR", "court_name": "NCLT Bengaluru Bench", "court_type": "NCLT", "state_code": "KA", "city": "Bengaluru", "jurisdiction": "Karnataka", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-HYD", "court_name": "NCLT Hyderabad Bench", "court_type": "NCLT", "state_code": "TS", "city": "Hyderabad", "jurisdiction": "Telangana, Andhra Pradesh", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    # NCLAT
    {"court_code": "NCLAT-DEL", "court_name": "National Company Law Appellate Tribunal, Delhi", "court_type": "NCLAT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "All India Principal", "e_filing_enabled": True, "e_filing_portal": "https://nclat.nic.in"},
]


# =============================================================================
# COURT FEE SLABS DATA
# =============================================================================

COURT_FEE_SLABS = [
    # DRT Filing Fees
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": Decimal("0"), "max_claim_amount": Decimal("1000000"), "calculation_type": "FIXED", "fixed_fee": Decimal("12000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": Decimal("1000001"), "max_claim_amount": Decimal("10000000"), "calculation_type": "SLAB", "fixed_fee": Decimal("12000"), "percentage_rate": Decimal("0.5"), "effective_from": date(2024, 1, 1)},
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": Decimal("10000001"), "max_claim_amount": Decimal("100000000"), "calculation_type": "SLAB", "fixed_fee": Decimal("57000"), "percentage_rate": Decimal("0.25"), "effective_from": date(2024, 1, 1)},
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": Decimal("100000001"), "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": Decimal("282000"), "max_fee": Decimal("282000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "DRT", "fee_type": "INTERIM_APPLICATION", "min_claim_amount": Decimal("0"), "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": Decimal("500"), "effective_from": date(2024, 1, 1)},
    {"court_type": "DRT", "fee_type": "EXECUTION", "min_claim_amount": Decimal("0"), "max_claim_amount": None, "calculation_type": "PERCENTAGE", "percentage_rate": Decimal("0.5"), "min_fee": Decimal("1000"), "max_fee": Decimal("100000"), "effective_from": date(2024, 1, 1)},
    # DRAT Appeal Fees
    {"court_type": "DRAT", "fee_type": "APPEAL", "min_claim_amount": Decimal("0"), "max_claim_amount": Decimal("1000000"), "calculation_type": "FIXED", "fixed_fee": Decimal("15000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "DRAT", "fee_type": "APPEAL", "min_claim_amount": Decimal("1000001"), "max_claim_amount": Decimal("10000000"), "calculation_type": "SLAB", "fixed_fee": Decimal("15000"), "percentage_rate": Decimal("0.5"), "effective_from": date(2024, 1, 1)},
    # NCLT Fees
    {"court_type": "NCLT", "fee_type": "FILING", "min_claim_amount": Decimal("0"), "max_claim_amount": Decimal("10000000"), "calculation_type": "FIXED", "fixed_fee": Decimal("5000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "NCLT", "fee_type": "FILING", "min_claim_amount": Decimal("10000001"), "max_claim_amount": Decimal("100000000"), "calculation_type": "FIXED", "fixed_fee": Decimal("10000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "NCLT", "fee_type": "FILING", "min_claim_amount": Decimal("100000001"), "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": Decimal("25000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "NCLT", "fee_type": "INTERIM_APPLICATION", "min_claim_amount": Decimal("0"), "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": Decimal("2000"), "effective_from": date(2024, 1, 1)},
    # NCLAT Fees
    {"court_type": "NCLAT", "fee_type": "APPEAL", "min_claim_amount": Decimal("0"), "max_claim_amount": Decimal("10000000"), "calculation_type": "FIXED", "fixed_fee": Decimal("10000"), "effective_from": date(2024, 1, 1)},
    {"court_type": "NCLAT", "fee_type": "APPEAL", "min_claim_amount": Decimal("10000001"), "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": Decimal("25000"), "effective_from": date(2024, 1, 1)},
]


# =============================================================================
# EXPENSE CATEGORIES DATA
# =============================================================================

EXPENSE_CATEGORIES = [
    {"category_code": "COURT_FEE", "category_name": "Court Filing Fee", "category_type": "COURT_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 1, "display_order": 1},
    {"category_code": "FILING_FEE", "category_name": "Document Filing Fee", "category_type": "FILING_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 2, "display_order": 2},
    {"category_code": "PROCESS_FEE", "category_name": "Process Fee", "category_type": "PROCESS_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 3, "display_order": 3},
    {"category_code": "EXECUTION_FEE", "category_name": "Execution Fee", "category_type": "EXECUTION_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 4, "display_order": 4},
    {"category_code": "ADV_RETAINER", "category_name": "Advocate Retainer Fee", "category_type": "ADVOCATE_RETAINER", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 10, "display_order": 10},
    {"category_code": "ADV_APPEARANCE", "category_name": "Advocate Appearance Fee", "category_type": "ADVOCATE_APPEARANCE", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 11, "display_order": 11},
    {"category_code": "VALUATION", "category_name": "Valuation Charges", "category_type": "VALUATION_CHARGES", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": True, "gst_rate": Decimal("18.00"), "hsn_sac_code": "998399", "recoverable_from_borrower": True, "recovery_priority": 20, "display_order": 20},
    {"category_code": "PUBLICATION", "category_name": "Newspaper Publication Charges", "category_type": "PUBLICATION_CHARGES", "tds_applicable": True, "tds_section": "194C", "tds_rate": Decimal("2.00"), "gst_applicable": True, "gst_rate": Decimal("5.00"), "recoverable_from_borrower": True, "recovery_priority": 21, "display_order": 21},
    {"category_code": "STAMP_DUTY", "category_name": "Stamp Duty", "category_type": "STAMP_DUTY", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 5, "display_order": 5},
    {"category_code": "COURIER", "category_name": "Courier & Postage", "category_type": "COURIER_POSTAGE", "tds_applicable": False, "gst_applicable": True, "gst_rate": Decimal("18.00"), "recoverable_from_borrower": True, "recovery_priority": 30, "display_order": 30},
    {"category_code": "CERSAI", "category_name": "CERSAI Charges", "category_type": "CERSAI_CHARGES", "tds_applicable": False, "gst_applicable": True, "gst_rate": Decimal("18.00"), "recoverable_from_borrower": True, "recovery_priority": 6, "display_order": 6},
    {"category_code": "MISC", "category_name": "Miscellaneous Expenses", "category_type": "MISCELLANEOUS", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 99, "display_order": 99},
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("Legal Module Direct Seed Script")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Get organization ID
            result = await session.execute(text("SELECT id FROM mst_organization LIMIT 1"))
            org_row = result.fetchone()
            if not org_row:
                print("✗ No organization found. Please run seed_data.py first.")
                return
            org_id = org_row[0]
            print(f"✓ Using organization: {org_id}")

            # Get user ID for created_by
            result = await session.execute(text("SELECT id FROM mst_user WHERE is_active = true LIMIT 1"))
            user_row = result.fetchone()
            user_id = user_row[0] if user_row else None

            # Seed Statutory Periods
            print("\n--- Seeding Statutory Periods ---")
            count = 0
            for period_data in STATUTORY_PERIODS:
                # Check if exists
                result = await session.execute(
                    select(StatutoryPeriod).where(
                        StatutoryPeriod.organization_id == org_id,
                        StatutoryPeriod.provision_code == period_data["provision_code"]
                    )
                )
                if result.scalar_one_or_none():
                    print(f"  - Skipped (exists): {period_data['provision_code']}")
                    continue

                period = StatutoryPeriod(
                    organization_id=org_id,
                    created_by_id=user_id,
                    **period_data
                )
                session.add(period)
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} statutory periods")

            # Seed Notice Templates
            print("\n--- Seeding Notice Templates ---")
            count = 0
            for template_data in NOTICE_TEMPLATES:
                result = await session.execute(
                    select(NoticeTemplate).where(
                        NoticeTemplate.organization_id == org_id,
                        NoticeTemplate.template_code == template_data["template_code"]
                    )
                )
                if result.scalar_one_or_none():
                    print(f"  - Skipped (exists): {template_data['template_code']}")
                    continue

                template = NoticeTemplate(
                    organization_id=org_id,
                    created_by_id=user_id,
                    **template_data
                )
                session.add(template)
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} notice templates")

            # Seed Courts
            print("\n--- Seeding Courts ---")
            count = 0
            for court_data in COURTS:
                result = await session.execute(
                    select(Court).where(
                        Court.organization_id == org_id,
                        Court.court_code == court_data["court_code"]
                    )
                )
                if result.scalar_one_or_none():
                    print(f"  - Skipped (exists): {court_data['court_code']}")
                    continue

                court = Court(
                    organization_id=org_id,
                    created_by_id=user_id,
                    is_operational=True,
                    working_days=["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
                    working_hours="10:30 AM - 5:00 PM",
                    **court_data
                )
                session.add(court)
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} courts")

            # Seed Court Fee Slabs
            print("\n--- Seeding Court Fee Slabs ---")
            count = 0
            for slab_data in COURT_FEE_SLABS:
                slab = CourtFeeSlab(
                    organization_id=org_id,
                    created_by_id=user_id,
                    **slab_data
                )
                session.add(slab)
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} court fee slabs")

            # Seed Expense Categories
            print("\n--- Seeding Expense Categories ---")
            count = 0
            for category_data in EXPENSE_CATEGORIES:
                result = await session.execute(
                    select(ExpenseCategory).where(
                        ExpenseCategory.organization_id == org_id,
                        ExpenseCategory.category_code == category_data["category_code"]
                    )
                )
                if result.scalar_one_or_none():
                    print(f"  - Skipped (exists): {category_data['category_code']}")
                    continue

                category = ExpenseCategory(
                    organization_id=org_id,
                    created_by_id=user_id,
                    **category_data
                )
                session.add(category)
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} expense categories")

            print("\n" + "=" * 60)
            print("✓ Legal Module seed data created successfully!")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
