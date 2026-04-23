"""
Seed script for Legal Module master data.
Creates statutory periods, notice templates, courts, court fees, and expense categories.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    python scripts/seed_legal_data.py

Prerequisites:
    - Database must be running
    - Run `python scripts/seed_data.py` first to create organization
    - API server must be running at http://localhost:8000
"""

import asyncio
from datetime import date
from decimal import Decimal
from typing import Optional
import httpx

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"

# Store created IDs
created_ids = {
    "organization_id": None,
    "statutory_periods": {},
    "notice_templates": {},
    "courts": {},
    "court_fee_slabs": [],
    "expense_categories": {},
}


class APIClient:
    """HTTP client for API calls."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def login(self, username: str, password: str) -> dict:
        """Login and get access token."""
        response = await self.client.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        data = response.json()
        self.access_token = data["access_token"]
        print(f"✓ Logged in as {username}")
        return data

    async def get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request."""
        response = await self.client.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._headers(),
        )
        if response.status_code >= 400:
            print(f"GET {endpoint} failed: {response.status_code} - {response.text}")
            return None
        return response.json()

    async def post(self, endpoint: str, data: dict) -> dict:
        """Make POST request."""
        response = await self.client.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self._headers(),
        )
        if response.status_code >= 400:
            print(f"POST {endpoint} failed: {response.status_code} - {response.text}")
            return None
        return response.json()


async def get_organization_id(client: APIClient) -> str:
    """Get existing organization ID."""
    print("\n--- Getting Organization ---")
    existing = await client.get("/organizations", {"skip": 0, "limit": 1})
    if existing and existing.get("items"):
        org_id = existing["items"][0]["id"]
        print(f"✓ Using organization: {org_id}")
        return org_id
    raise Exception("No organization found. Run seed_data.py first.")


# =============================================================================
# STATUTORY PERIODS - Indian Legal Limitation Periods
# =============================================================================

STATUTORY_PERIODS = [
    # SARFAESI Act 2002
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
        "legal_reference": "SARFAESI Act 2002, Section 13(2) read with Rule 3 of Security Interest Rules 2002",
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
        "consequence": "If no response, objection deemed rejected and borrower can approach DRT",
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
        "extension_grounds": "No bids received or for operational reasons",
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
        "start_event": "Date of measure taken by secured creditor (possession/auction)",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Sufficient cause shown, DRT may condone delay",
        "consequence": "Right to challenge SARFAESI action may be lost",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["SARFAESI"],
        "alert_before_days": [30, 15, 7, 3],
        "legal_reference": "SARFAESI Act 2002, Section 17 - Appeal period for borrower",
    },
    # Negotiable Instruments Act
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
        "consequence": "Drawer gets 15 days to make payment, failing which criminal complaint can be filed",
        "applicable_forums": ["MAGISTRATE_COURT"],
        "applicable_case_types": ["CHEQUE_BOUNCE"],
        "alert_before_days": [7, 3, 1],
        "legal_reference": "Negotiable Instruments Act 1881, Section 138(c)",
    },
    {
        "provision_code": "NI_ACT_138_COMPLAINT",
        "provision_name": "Section 138 Complaint Filing Period",
        "act_name": "Negotiable Instruments Act 1881",
        "section_reference": "Section 142",
        "period_days": 30,
        "period_description": "30 days (from expiry of 15 days notice period)",
        "start_event": "Expiry of 15 days notice period",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Sufficient cause shown as per Section 142(b)",
        "consequence": "Right to file criminal complaint under Section 138 may be lost",
        "applicable_forums": ["MAGISTRATE_COURT"],
        "applicable_case_types": ["CHEQUE_BOUNCE"],
        "alert_before_days": [15, 7, 3],
        "legal_reference": "Negotiable Instruments Act 1881, Section 142(b)",
    },
    # DRT Act
    {
        "provision_code": "DRT_APPLICATION",
        "provision_name": "DRT Application Filing Limitation",
        "act_name": "Recovery of Debts Due to Banks and Financial Institutions Act 1993",
        "section_reference": "Section 24",
        "period_days": 1095,  # 3 years
        "period_years": 3,
        "period_description": "3 years",
        "start_event": "Date of cause of action (loan recall/NPA date)",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Delay can be condoned by DRT if sufficient cause shown",
        "consequence": "Application may be barred by limitation",
        "applicable_forums": ["DRT"],
        "applicable_case_types": ["DRT_SUIT"],
        "alert_before_days": [180, 90, 60, 30, 15],
        "legal_reference": "DRT Act 1993, Section 24 read with Limitation Act 1963",
    },
    {
        "provision_code": "DRAT_APPEAL",
        "provision_name": "DRAT Appeal Period",
        "act_name": "Recovery of Debts Due to Banks and Financial Institutions Act 1993",
        "section_reference": "Section 20",
        "period_days": 45,
        "period_description": "45 days",
        "start_event": "Date of DRT order",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Delay can be condoned by DRAT if sufficient cause shown",
        "consequence": "Right of appeal may be lost",
        "applicable_forums": ["DRAT"],
        "applicable_case_types": ["DRT_APPEAL"],
        "alert_before_days": [30, 15, 7, 3],
        "legal_reference": "DRT Act 1993, Section 20",
    },
    # Execution
    {
        "provision_code": "DRT_RC_EXECUTION",
        "provision_name": "DRT Recovery Certificate Execution",
        "act_name": "Recovery of Debts Due to Banks and Financial Institutions Act 1993",
        "section_reference": "Section 25",
        "period_days": 4380,  # 12 years
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
        "provision_code": "CIVIL_DECREE_EXECUTION",
        "provision_name": "Civil Decree Execution Period",
        "act_name": "Limitation Act 1963",
        "section_reference": "Article 136",
        "period_days": 4380,  # 12 years
        "period_years": 12,
        "period_description": "12 years",
        "start_event": "Date of decree",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Decree becomes time-barred for execution",
        "applicable_forums": ["DISTRICT_COURT", "HIGH_COURT"],
        "applicable_case_types": ["EXECUTION"],
        "alert_before_days": [365, 180, 90, 30],
        "legal_reference": "Limitation Act 1963, Article 136",
    },
    # IBC
    {
        "provision_code": "IBC_APPLICATION",
        "provision_name": "IBC Application Filing (Section 7)",
        "act_name": "Insolvency and Bankruptcy Code 2016",
        "section_reference": "Section 7",
        "period_days": 1095,  # 3 years from default
        "period_years": 3,
        "period_description": "3 years from date of default",
        "start_event": "Date of default",
        "includes_holidays": True,
        "extension_allowed": False,
        "consequence": "Application under Section 7 may be time-barred",
        "applicable_forums": ["NCLT"],
        "applicable_case_types": ["IBC"],
        "alert_before_days": [180, 90, 60, 30],
        "legal_reference": "IBC 2016, Section 7 read with Limitation Act 1963",
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
    # Arbitration
    {
        "provision_code": "ARBITRATION_INVOCATION",
        "provision_name": "Arbitration Invocation Limitation",
        "act_name": "Arbitration and Conciliation Act 1996",
        "section_reference": "Section 43",
        "period_days": 1095,  # 3 years
        "period_years": 3,
        "period_description": "3 years",
        "start_event": "Date of cause of action",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "As per Limitation Act 1963",
        "consequence": "Claim may be time-barred in arbitration",
        "applicable_forums": ["ARBITRATION_CENTER"],
        "applicable_case_types": ["ARBITRATION"],
        "alert_before_days": [180, 90, 60, 30],
        "legal_reference": "Arbitration Act 1996, Section 43 read with Limitation Act 1963",
    },
    {
        "provision_code": "ARBITRATION_AWARD_CHALLENGE",
        "provision_name": "Arbitration Award Challenge Period",
        "act_name": "Arbitration and Conciliation Act 1996",
        "section_reference": "Section 34",
        "period_days": 90,
        "period_description": "3 months (plus 30 days condonable)",
        "start_event": "Date of receipt of arbitral award",
        "includes_holidays": True,
        "extension_allowed": True,
        "extension_grounds": "Further 30 days if sufficient cause shown",
        "consequence": "Right to challenge award may be lost",
        "applicable_forums": ["DISTRICT_COURT", "HIGH_COURT"],
        "applicable_case_types": ["ARBITRATION"],
        "alert_before_days": [60, 30, 15, 7],
        "legal_reference": "Arbitration Act 1996, Section 34(3)",
    },
    # CERSAI
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
        "legal_reference": "SARFAESI Act 2002, Section 23; CERSAI Regulations",
    },
]


async def seed_statutory_periods(client: APIClient, org_id: str):
    """Seed statutory period master data."""
    print("\n=== Seeding Statutory Periods ===")

    for period in STATUTORY_PERIODS:
        period_data = {
            "organization_id": org_id,
            **period,
        }
        result = await client.post("/legal/statutory-periods", period_data)
        if result:
            created_ids["statutory_periods"][period["provision_code"]] = result["id"]
            print(f"  ✓ {period['provision_code']}: {period['provision_name']}")
        else:
            print(f"  ✗ Failed: {period['provision_code']}")

    print(f"\n  Created {len(created_ids['statutory_periods'])} statutory periods")


# =============================================================================
# NOTICE TEMPLATES - Legal Notice Templates
# =============================================================================

NOTICE_TEMPLATES = [
    # SARFAESI Notices
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
        "placeholders": [
            "borrower_name", "borrower_address", "loan_account_number",
            "sanction_date", "sanction_amount", "principal_outstanding",
            "interest_outstanding", "total_amount", "security_description",
            "security_address", "npa_date", "notice_date", "company_name",
            "authorized_officer_name", "authorized_officer_designation"
        ],
        "template_content": """
<!DOCTYPE html>
<html>
<head><title>Notice under Section 13(2) of SARFAESI Act 2002</title></head>
<body style="font-family: Times New Roman, serif; font-size: 14px; margin: 40px;">
<div style="text-align: center; font-weight: bold; font-size: 16px;">
NOTICE UNDER SECTION 13(2) OF THE SECURITISATION AND RECONSTRUCTION OF FINANCIAL ASSETS AND ENFORCEMENT OF SECURITY INTEREST ACT, 2002
<br/>READ WITH RULE 3 OF THE SECURITY INTEREST (ENFORCEMENT) RULES, 2002
</div>
<br/><br/>
<div><strong>Date:</strong> {{notice_date}}</div>
<br/>
<div><strong>To,</strong></div>
<div>{{borrower_name}}</div>
<div>{{borrower_address}}</div>
<br/>
<div><strong>Loan Account No:</strong> {{loan_account_number}}</div>
<br/>
<div>Dear Sir/Madam,</div>
<br/>
<div style="text-align: justify;">
WHEREAS, you had availed a loan facility from {{company_name}} (hereinafter referred to as "the Secured Creditor") vide Loan Agreement dated {{sanction_date}} for an amount of Rs. {{sanction_amount}}/- (Rupees {{sanction_amount_words}} only).

AND WHEREAS, you have committed default in repayment of the loan amount and your loan account has been classified as Non-Performing Asset (NPA) on {{npa_date}}.

AND WHEREAS, the following amounts are due and payable by you as on date:

<table style="width: 100%; border: 1px solid black; margin: 20px 0;">
<tr><td style="border: 1px solid black; padding: 5px;">Principal Outstanding</td>
<td style="border: 1px solid black; padding: 5px; text-align: right;">Rs. {{principal_outstanding}}/-</td></tr>
<tr><td style="border: 1px solid black; padding: 5px;">Interest Outstanding</td>
<td style="border: 1px solid black; padding: 5px; text-align: right;">Rs. {{interest_outstanding}}/-</td></tr>
<tr><td style="border: 1px solid black; padding: 5px; font-weight: bold;">Total Amount Due</td>
<td style="border: 1px solid black; padding: 5px; text-align: right; font-weight: bold;">Rs. {{total_amount}}/-</td></tr>
</table>

AND WHEREAS, the said loan is secured by way of mortgage/hypothecation of the following property:

<div style="margin: 10px 0; padding: 10px; border: 1px solid black;">
<strong>Security Description:</strong> {{security_description}}
<br/><strong>Property Address:</strong> {{security_address}}
</div>

NOW THEREFORE, in exercise of powers conferred under Section 13(2) of the SARFAESI Act, 2002, you are hereby called upon to discharge your liability in full within SIXTY (60) DAYS from the date of receipt of this notice, failing which the Secured Creditor shall be entitled to exercise all or any of the rights under Section 13(4) of the said Act, which includes taking possession of the secured assets and selling the same without the intervention of the Court.

You may also note that in case of failure to pay, the interest shall continue to accrue on the outstanding amount at the agreed rate till the date of realization.

Please note that this is a legal notice and you are advised to take it seriously and comply with the same within the stipulated time period to avoid further legal action.
</div>
<br/><br/>
<div style="text-align: right;">
For {{company_name}}
<br/><br/><br/>
{{authorized_officer_name}}
<br/>{{authorized_officer_designation}}
<br/>(Authorized Officer)
</div>
</body>
</html>
""",
    },
    {
        "template_code": "SARFAESI_13_4_POSSESSION",
        "template_name": "Section 13(4) Possession Notice",
        "notice_type": "SARFAESI_13_4_POSSESSION",
        "act_reference": "SARFAESI Act 2002, Section 13(4) read with Rule 8",
        "section_reference": "Section 13(4) / Rule 8",
        "statutory_period_days": 15,
        "response_period_days": None,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": [
            "borrower_name", "borrower_address", "loan_account_number",
            "security_description", "security_address", "total_amount",
            "demand_notice_date", "notice_date", "company_name",
            "authorized_officer_name", "authorized_officer_designation"
        ],
        "template_content": """
<!DOCTYPE html>
<html>
<head><title>Possession Notice under SARFAESI Act 2002</title></head>
<body style="font-family: Times New Roman, serif; font-size: 14px; margin: 40px;">
<div style="text-align: center; font-weight: bold; font-size: 16px; color: red;">
POSSESSION NOTICE
<br/>UNDER SECTION 13(4) OF THE SARFAESI ACT, 2002
<br/>READ WITH RULE 8 OF THE SECURITY INTEREST (ENFORCEMENT) RULES, 2002
</div>
<br/><br/>
<div><strong>Date:</strong> {{notice_date}}</div>
<div><strong>Loan Account No:</strong> {{loan_account_number}}</div>
<br/>
<div style="text-align: justify;">
WHEREAS, {{borrower_name}}, residing at {{borrower_address}}, having Loan Account No. {{loan_account_number}}, has failed to repay the loan amount despite the Demand Notice dated {{demand_notice_date}} issued under Section 13(2) of the SARFAESI Act, 2002.

AND WHEREAS, the statutory period of 60 days has expired without payment or any valid objection.

NOW THEREFORE, notice is hereby given that the undersigned, being the Authorized Officer of {{company_name}}, has taken SYMBOLIC POSSESSION of the following secured asset(s) under Section 13(4) of the SARFAESI Act, 2002:

<div style="margin: 20px 0; padding: 15px; border: 2px solid black;">
<strong>SECURED ASSET:</strong>
<br/>{{security_description}}
<br/><strong>Address:</strong> {{security_address}}
</div>

The borrower and the public in general is hereby cautioned not to deal with the property described above as any dealing with the property will be subject to the charge of {{company_name}} for an amount of Rs. {{total_amount}}/- plus interest and costs.

The borrower's attention is invited to the provisions of Section 13(8) of the SARFAESI Act, 2002 under which the borrower is entitled to redeem the secured asset by tendering the dues in full before the date fixed for sale.

Date of affixing this notice: {{notice_date}}
</div>
<br/><br/>
<div style="text-align: right;">
For {{company_name}}
<br/><br/><br/>
{{authorized_officer_name}}
<br/>{{authorized_officer_designation}}
<br/>(Authorized Officer)
</div>
</body>
</html>
""",
    },
    {
        "template_code": "SARFAESI_AUCTION_NOTICE",
        "template_name": "Auction/Sale Notice under SARFAESI",
        "notice_type": "SARFAESI_AUCTION",
        "act_reference": "SARFAESI Act 2002, Rule 8(6) and Rule 9",
        "section_reference": "Rule 8(6) & 9",
        "statutory_period_days": 30,
        "response_period_days": None,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": [
            "borrower_name", "loan_account_number", "security_description",
            "security_address", "reserve_price", "emd_amount", "bid_increment",
            "auction_date", "auction_time", "auction_venue", "inspection_dates",
            "company_name", "contact_person", "contact_phone", "contact_email"
        ],
        "template_content": """
<!DOCTYPE html>
<html>
<head><title>E-Auction Sale Notice</title></head>
<body style="font-family: Times New Roman, serif; font-size: 14px; margin: 40px;">
<div style="text-align: center; font-weight: bold; font-size: 18px;">
E-AUCTION SALE NOTICE
<br/><span style="font-size: 14px;">FOR SALE OF IMMOVABLE PROPERTY</span>
<br/><span style="font-size: 12px;">Under SARFAESI Act 2002 read with Rule 8 & 9 of Security Interest Rules 2002</span>
</div>
<br/>
<div style="text-align: justify;">
{{company_name}} (Secured Creditor) invites sealed/online bids for the sale of the following secured asset:

<table style="width: 100%; border: 2px solid black; margin: 20px 0; border-collapse: collapse;">
<tr style="background-color: #f0f0f0;">
<th style="border: 1px solid black; padding: 10px;" colspan="2">PROPERTY DETAILS</th>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px; width: 30%;">Borrower Name</td>
<td style="border: 1px solid black; padding: 8px;">{{borrower_name}}</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">Loan Account No.</td>
<td style="border: 1px solid black; padding: 8px;">{{loan_account_number}}</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">Property Description</td>
<td style="border: 1px solid black; padding: 8px;">{{security_description}}</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">Property Address</td>
<td style="border: 1px solid black; padding: 8px;">{{security_address}}</td>
</tr>
<tr style="background-color: #ffffcc;">
<td style="border: 1px solid black; padding: 8px; font-weight: bold;">Reserve Price</td>
<td style="border: 1px solid black; padding: 8px; font-weight: bold;">Rs. {{reserve_price}}/-</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">EMD (Earnest Money Deposit)</td>
<td style="border: 1px solid black; padding: 8px;">Rs. {{emd_amount}}/- (10% of Reserve Price)</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">Bid Increment</td>
<td style="border: 1px solid black; padding: 8px;">Rs. {{bid_increment}}/-</td>
</tr>
<tr style="background-color: #ccffcc;">
<td style="border: 1px solid black; padding: 8px; font-weight: bold;">Auction Date & Time</td>
<td style="border: 1px solid black; padding: 8px; font-weight: bold;">{{auction_date}} at {{auction_time}}</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">Venue/Platform</td>
<td style="border: 1px solid black; padding: 8px;">{{auction_venue}}</td>
</tr>
<tr>
<td style="border: 1px solid black; padding: 8px;">Property Inspection</td>
<td style="border: 1px solid black; padding: 8px;">{{inspection_dates}}</td>
</tr>
</table>

<strong>TERMS AND CONDITIONS:</strong>
<ol>
<li>The property is being sold on "AS IS WHERE IS" and "AS IS WHAT IS" basis.</li>
<li>EMD should be paid by DD/RTGS/NEFT before the auction date.</li>
<li>Successful bidder shall deposit 25% of the bid amount (less EMD) within 24 hours.</li>
<li>Balance 75% shall be paid within 15 days from the date of confirmation of sale.</li>
<li>All statutory dues, taxes, and registration charges shall be borne by the purchaser.</li>
<li>Secured Creditor reserves the right to accept or reject any bid without assigning any reason.</li>
</ol>

<strong>Contact Details:</strong>
<br/>{{contact_person}} | Phone: {{contact_phone}} | Email: {{contact_email}}
</div>
<br/>
<div style="text-align: right;">
For {{company_name}}
<br/>Authorized Officer
</div>
</body>
</html>
""",
    },
    # NI Act Notices
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
        "placeholders": [
            "drawer_name", "drawer_address", "cheque_number", "cheque_date",
            "cheque_amount", "bank_name", "dishonour_date", "dishonour_reason",
            "notice_date", "payee_name", "payee_address"
        ],
        "template_content": """
<!DOCTYPE html>
<html>
<head><title>Legal Notice under Section 138 NI Act</title></head>
<body style="font-family: Times New Roman, serif; font-size: 14px; margin: 40px;">
<div style="text-align: center; font-weight: bold; font-size: 16px;">
LEGAL NOTICE
<br/>UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881
</div>
<br/>
<div style="text-align: right;"><strong>Date:</strong> {{notice_date}}</div>
<br/>
<div><strong>RPAD/Speed Post</strong></div>
<br/>
<div><strong>To,</strong></div>
<div>{{drawer_name}}</div>
<div>{{drawer_address}}</div>
<br/>
<div style="text-align: justify;">
<strong>Subject: Legal Notice for dishonour of cheque bearing No. {{cheque_number}} dated {{cheque_date}} for Rs. {{cheque_amount}}/-</strong>

Dear Sir/Madam,

Under instructions from and on behalf of my client, {{payee_name}}, I hereby serve upon you the following Legal Notice:

1. That you had issued Cheque No. {{cheque_number}} dated {{cheque_date}} for an amount of Rs. {{cheque_amount}}/- (Rupees {{cheque_amount_words}} only) drawn on {{bank_name}} in favour of my client towards discharge of your legally enforceable debt/liability.

2. That the said cheque was presented for encashment on the due date but the same was returned unpaid/dishonoured on {{dishonour_date}} with the endorsement "{{dishonour_reason}}".

3. That you are well aware that dishonour of cheque is an offence under Section 138 of the Negotiable Instruments Act, 1881 punishable with imprisonment up to two years and/or fine which may extend to twice the amount of the cheque.

4. That you are hereby called upon to make the payment of the said amount of Rs. {{cheque_amount}}/- within FIFTEEN (15) DAYS from the date of receipt of this notice, failing which my client shall be constrained to initiate criminal proceedings against you under Section 138 of the NI Act, 1881, entirely at your risk, cost and consequences.

5. A copy of this notice is retained in my office for record and further necessary action.

Please govern yourself accordingly.
</div>
<br/><br/>
<div style="text-align: right;">
Yours faithfully,
<br/><br/><br/>
Advocate for {{payee_name}}
<br/>{{payee_address}}
</div>
</body>
</html>
""",
    },
    # Recall Notice
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
        "placeholders": [
            "borrower_name", "borrower_address", "loan_account_number",
            "sanction_amount", "disbursement_date", "principal_outstanding",
            "interest_outstanding", "total_amount", "default_date",
            "notice_date", "company_name"
        ],
        "template_content": """
<!DOCTYPE html>
<html>
<head><title>Loan Recall Notice</title></head>
<body style="font-family: Times New Roman, serif; font-size: 14px; margin: 40px;">
<div style="text-align: center; font-weight: bold; font-size: 16px;">
LOAN RECALL NOTICE
</div>
<br/>
<div><strong>Date:</strong> {{notice_date}}</div>
<div><strong>Loan Account No:</strong> {{loan_account_number}}</div>
<br/>
<div><strong>To,</strong></div>
<div>{{borrower_name}}</div>
<div>{{borrower_address}}</div>
<br/>
<div style="text-align: justify;">
Dear Sir/Madam,

<strong>Sub: Recall of Loan Facility - Account No. {{loan_account_number}}</strong>

This is to inform you that you had availed a loan facility of Rs. {{sanction_amount}}/- from {{company_name}} on {{disbursement_date}}.

Despite several reminders and follow-ups, you have failed to service your loan account as per the agreed terms, and your account is in default since {{default_date}}.

The outstanding dues as on date are as follows:
<ul>
<li>Principal Outstanding: Rs. {{principal_outstanding}}/-</li>
<li>Interest Outstanding: Rs. {{interest_outstanding}}/-</li>
<li><strong>Total Amount Due: Rs. {{total_amount}}/-</strong></li>
</ul>

In view of the above, we hereby RECALL the entire loan facility and demand immediate repayment of the entire outstanding amount of Rs. {{total_amount}}/- within FIFTEEN (15) DAYS from the date of receipt of this notice.

Failure to comply with this demand will compel us to initiate appropriate legal action against you for recovery of our dues, including but not limited to:
- Filing of Recovery Suit before the Debt Recovery Tribunal
- Initiation of proceedings under SARFAESI Act, 2002
- Filing of criminal complaint for cheque bounce (if applicable)

We hope you will treat this notice with utmost seriousness and arrange for immediate payment to avoid further legal action.
</div>
<br/><br/>
<div style="text-align: right;">
For {{company_name}}
<br/><br/><br/>
Authorized Signatory
</div>
</body>
</html>
""",
    },
    # Final Demand Notice
    {
        "template_code": "FINAL_DEMAND_NOTICE",
        "template_name": "Final Demand Notice Before Legal Action",
        "notice_type": "FINAL_DEMAND",
        "act_reference": "General",
        "section_reference": "General",
        "statutory_period_days": 7,
        "response_period_days": 7,
        "template_format": "HTML",
        "language": "ENGLISH",
        "is_default": True,
        "placeholders": [
            "borrower_name", "borrower_address", "loan_account_number",
            "total_amount", "previous_notices", "notice_date", "company_name"
        ],
        "template_content": """
<!DOCTYPE html>
<html>
<head><title>Final Demand Notice</title></head>
<body style="font-family: Times New Roman, serif; font-size: 14px; margin: 40px;">
<div style="text-align: center; font-weight: bold; font-size: 18px; color: red;">
FINAL DEMAND NOTICE
<br/><span style="font-size: 14px;">BEFORE INITIATION OF LEGAL PROCEEDINGS</span>
</div>
<br/>
<div style="text-align: right;"><strong>Date:</strong> {{notice_date}}</div>
<br/>
<div><strong>URGENT & IMPORTANT</strong></div>
<br/>
<div><strong>To,</strong></div>
<div>{{borrower_name}}</div>
<div>{{borrower_address}}</div>
<br/>
<div><strong>Re: Loan Account No. {{loan_account_number}}</strong></div>
<br/>
<div style="text-align: justify;">
Dear Sir/Madam,

Reference is made to our earlier notices dated {{previous_notices}} which have remained unheeded.

This is the FINAL NOTICE being served upon you before initiating legal proceedings.

You are hereby called upon to pay the outstanding amount of Rs. {{total_amount}}/- within SEVEN (7) DAYS from the date of this notice.

<strong>PLEASE NOTE:</strong> If payment is not received within the stipulated time, we shall, without any further notice:

1. File appropriate legal proceedings before the competent court/tribunal
2. Initiate proceedings under the SARFAESI Act, 2002
3. Report the default to CIBIL and other credit information companies
4. Take all other legal remedies available under law

All costs, expenses, and consequences of such legal action shall be entirely at your risk.

This is a final opportunity being given to you to settle your dues amicably. Please avail it.
</div>
<br/><br/>
<div style="text-align: right;">
For {{company_name}}
<br/><br/><br/>
Authorized Officer
</div>
</body>
</html>
""",
    },
]


async def seed_notice_templates(client: APIClient, org_id: str):
    """Seed notice template master data."""
    print("\n=== Seeding Notice Templates ===")

    for template in NOTICE_TEMPLATES:
        template_data = {
            "organization_id": org_id,
            **template,
        }
        result = await client.post("/legal/notice-templates", template_data)
        if result:
            created_ids["notice_templates"][template["template_code"]] = result["id"]
            print(f"  ✓ {template['template_code']}: {template['template_name']}")
        else:
            print(f"  ✗ Failed: {template['template_code']}")

    print(f"\n  Created {len(created_ids['notice_templates'])} notice templates")


# =============================================================================
# COURTS - DRT, DRAT, NCLT, High Courts
# =============================================================================

COURTS = [
    # DRT - Debt Recovery Tribunals (All 39 as of 2024)
    # North Zone
    {"court_code": "DRT-DEL-1", "court_name": "Debt Recovery Tribunal-I, New Delhi", "court_type": "DRT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "Delhi NCR", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-DEL-2", "court_name": "Debt Recovery Tribunal-II, New Delhi", "court_type": "DRT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "Delhi NCR", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-DEL-3", "court_name": "Debt Recovery Tribunal-III, New Delhi", "court_type": "DRT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "Delhi NCR", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-CHD", "court_name": "Debt Recovery Tribunal, Chandigarh", "court_type": "DRT", "state_code": "CH", "city": "Chandigarh", "jurisdiction": "Punjab, Haryana, HP, Chandigarh", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-JAI", "court_name": "Debt Recovery Tribunal, Jaipur", "court_type": "DRT", "state_code": "RJ", "city": "Jaipur", "jurisdiction": "Rajasthan", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-LKO", "court_name": "Debt Recovery Tribunal, Lucknow", "court_type": "DRT", "state_code": "UP", "city": "Lucknow", "jurisdiction": "Uttar Pradesh (West)", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-ALD", "court_name": "Debt Recovery Tribunal, Prayagraj (Allahabad)", "court_type": "DRT", "state_code": "UP", "city": "Prayagraj", "jurisdiction": "Uttar Pradesh (East)", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    # West Zone
    {"court_code": "DRT-MUM-1", "court_name": "Debt Recovery Tribunal-I, Mumbai", "court_type": "DRT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Mumbai Metropolitan", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-MUM-2", "court_name": "Debt Recovery Tribunal-II, Mumbai", "court_type": "DRT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Mumbai Metropolitan", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-MUM-3", "court_name": "Debt Recovery Tribunal-III, Mumbai", "court_type": "DRT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Mumbai Metropolitan", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-PUN", "court_name": "Debt Recovery Tribunal, Pune", "court_type": "DRT", "state_code": "MH", "city": "Pune", "jurisdiction": "Western Maharashtra", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-NAG", "court_name": "Debt Recovery Tribunal, Nagpur", "court_type": "DRT", "state_code": "MH", "city": "Nagpur", "jurisdiction": "Vidarbha Region", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-AUR", "court_name": "Debt Recovery Tribunal, Aurangabad", "court_type": "DRT", "state_code": "MH", "city": "Aurangabad", "jurisdiction": "Marathwada Region", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-AMD-1", "court_name": "Debt Recovery Tribunal-I, Ahmedabad", "court_type": "DRT", "state_code": "GJ", "city": "Ahmedabad", "jurisdiction": "North Gujarat", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-AMD-2", "court_name": "Debt Recovery Tribunal-II, Ahmedabad", "court_type": "DRT", "state_code": "GJ", "city": "Ahmedabad", "jurisdiction": "South Gujarat", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    # South Zone
    {"court_code": "DRT-CHN-1", "court_name": "Debt Recovery Tribunal-I, Chennai", "court_type": "DRT", "state_code": "TN", "city": "Chennai", "jurisdiction": "North Tamil Nadu", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-CHN-2", "court_name": "Debt Recovery Tribunal-II, Chennai", "court_type": "DRT", "state_code": "TN", "city": "Chennai", "jurisdiction": "South Tamil Nadu", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-BLR-1", "court_name": "Debt Recovery Tribunal-I, Bengaluru", "court_type": "DRT", "state_code": "KA", "city": "Bengaluru", "jurisdiction": "South Karnataka", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-BLR-2", "court_name": "Debt Recovery Tribunal-II, Bengaluru", "court_type": "DRT", "state_code": "KA", "city": "Bengaluru", "jurisdiction": "North Karnataka", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-HYD-1", "court_name": "Debt Recovery Tribunal-I, Hyderabad", "court_type": "DRT", "state_code": "TS", "city": "Hyderabad", "jurisdiction": "Telangana", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-HYD-2", "court_name": "Debt Recovery Tribunal-II, Hyderabad", "court_type": "DRT", "state_code": "TS", "city": "Hyderabad", "jurisdiction": "Andhra Pradesh", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-COI", "court_name": "Debt Recovery Tribunal, Coimbatore", "court_type": "DRT", "state_code": "TN", "city": "Coimbatore", "jurisdiction": "Western Tamil Nadu", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-EKM", "court_name": "Debt Recovery Tribunal, Ernakulam", "court_type": "DRT", "state_code": "KL", "city": "Ernakulam", "jurisdiction": "Kerala", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    # East Zone
    {"court_code": "DRT-KOL-1", "court_name": "Debt Recovery Tribunal-I, Kolkata", "court_type": "DRT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "West Bengal (South)", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-KOL-2", "court_name": "Debt Recovery Tribunal-II, Kolkata", "court_type": "DRT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "West Bengal (North)", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-GUW", "court_name": "Debt Recovery Tribunal, Guwahati", "court_type": "DRT", "state_code": "AS", "city": "Guwahati", "jurisdiction": "North East States", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-PAT", "court_name": "Debt Recovery Tribunal, Patna", "court_type": "DRT", "state_code": "BR", "city": "Patna", "jurisdiction": "Bihar, Jharkhand", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-RAN", "court_name": "Debt Recovery Tribunal, Ranchi", "court_type": "DRT", "state_code": "JH", "city": "Ranchi", "jurisdiction": "Jharkhand", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRT-CTK", "court_name": "Debt Recovery Tribunal, Cuttack", "court_type": "DRT", "state_code": "OD", "city": "Cuttack", "jurisdiction": "Odisha", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},

    # DRAT - Debt Recovery Appellate Tribunals (5)
    {"court_code": "DRAT-DEL", "court_name": "Debt Recovery Appellate Tribunal, Delhi", "court_type": "DRAT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "DRTs: Delhi, Chandigarh, Jaipur, Lucknow, Allahabad", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-MUM", "court_name": "Debt Recovery Appellate Tribunal, Mumbai", "court_type": "DRAT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "DRTs: Mumbai, Pune, Nagpur, Ahmedabad, Aurangabad", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-CHN", "court_name": "Debt Recovery Appellate Tribunal, Chennai", "court_type": "DRAT", "state_code": "TN", "city": "Chennai", "jurisdiction": "DRTs: Chennai, Bengaluru, Hyderabad, Coimbatore, Ernakulam", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-KOL", "court_name": "Debt Recovery Appellate Tribunal, Kolkata", "court_type": "DRAT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "DRTs: Kolkata, Guwahati, Patna, Ranchi, Cuttack", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},
    {"court_code": "DRAT-ALD", "court_name": "Debt Recovery Appellate Tribunal, Allahabad", "court_type": "DRAT", "state_code": "UP", "city": "Prayagraj", "jurisdiction": "DRTs: Allahabad, Lucknow, additional jurisdiction", "e_filing_enabled": True, "e_filing_portal": "https://drt.gov.in"},

    # NCLT - National Company Law Tribunal (16 Benches)
    {"court_code": "NCLT-DEL-PB", "court_name": "NCLT Principal Bench, New Delhi", "court_type": "NCLT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "All India (Principal)", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-DEL", "court_name": "NCLT New Delhi Bench", "court_type": "NCLT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "Delhi NCR, Haryana", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-MUM", "court_name": "NCLT Mumbai Bench", "court_type": "NCLT", "state_code": "MH", "city": "Mumbai", "jurisdiction": "Maharashtra (Mumbai Metropolitan)", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-CHN", "court_name": "NCLT Chennai Bench", "court_type": "NCLT", "state_code": "TN", "city": "Chennai", "jurisdiction": "Tamil Nadu, Puducherry", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-KOL", "court_name": "NCLT Kolkata Bench", "court_type": "NCLT", "state_code": "WB", "city": "Kolkata", "jurisdiction": "West Bengal, Sikkim, Andaman", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-BLR", "court_name": "NCLT Bengaluru Bench", "court_type": "NCLT", "state_code": "KA", "city": "Bengaluru", "jurisdiction": "Karnataka", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-HYD", "court_name": "NCLT Hyderabad Bench", "court_type": "NCLT", "state_code": "TS", "city": "Hyderabad", "jurisdiction": "Telangana, Andhra Pradesh", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-AMD", "court_name": "NCLT Ahmedabad Bench", "court_type": "NCLT", "state_code": "GJ", "city": "Ahmedabad", "jurisdiction": "Gujarat", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-JAI", "court_name": "NCLT Jaipur Bench", "court_type": "NCLT", "state_code": "RJ", "city": "Jaipur", "jurisdiction": "Rajasthan", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-CHD", "court_name": "NCLT Chandigarh Bench", "court_type": "NCLT", "state_code": "CH", "city": "Chandigarh", "jurisdiction": "Punjab, Haryana, HP, Chandigarh, J&K", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-ALD", "court_name": "NCLT Allahabad Bench", "court_type": "NCLT", "state_code": "UP", "city": "Prayagraj", "jurisdiction": "Uttar Pradesh, Uttarakhand", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-GUW", "court_name": "NCLT Guwahati Bench", "court_type": "NCLT", "state_code": "AS", "city": "Guwahati", "jurisdiction": "North East States", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-CTK", "court_name": "NCLT Cuttack Bench", "court_type": "NCLT", "state_code": "OD", "city": "Cuttack", "jurisdiction": "Odisha", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-KOC", "court_name": "NCLT Kochi Bench", "court_type": "NCLT", "state_code": "KL", "city": "Kochi", "jurisdiction": "Kerala, Lakshadweep", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-IND", "court_name": "NCLT Indore Bench", "court_type": "NCLT", "state_code": "MP", "city": "Indore", "jurisdiction": "Madhya Pradesh, Chhattisgarh", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},
    {"court_code": "NCLT-AUR", "court_name": "NCLT Amaravati Bench", "court_type": "NCLT", "state_code": "AP", "city": "Amaravati", "jurisdiction": "Andhra Pradesh", "e_filing_enabled": True, "e_filing_portal": "https://nclt.gov.in"},

    # NCLAT - National Company Law Appellate Tribunal
    {"court_code": "NCLAT-DEL", "court_name": "National Company Law Appellate Tribunal, Delhi", "court_type": "NCLAT", "state_code": "DL", "city": "New Delhi", "jurisdiction": "All India (Principal)", "e_filing_enabled": True, "e_filing_portal": "https://nclat.nic.in"},
    {"court_code": "NCLAT-CHN", "court_name": "NCLAT Chennai Bench", "court_type": "NCLAT", "state_code": "TN", "city": "Chennai", "jurisdiction": "South India", "e_filing_enabled": True, "e_filing_portal": "https://nclat.nic.in"},
]


async def seed_courts(client: APIClient, org_id: str):
    """Seed court master data."""
    print("\n=== Seeding Courts (DRT/DRAT/NCLT/NCLAT) ===")

    for court in COURTS:
        court_data = {
            "organization_id": org_id,
            "is_operational": True,
            "working_days": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
            "working_hours": "10:30 AM - 5:00 PM",
            "filing_time": "10:30 AM - 1:00 PM",
            **court,
        }
        result = await client.post("/legal/courts", court_data)
        if result:
            created_ids["courts"][court["court_code"]] = result["id"]
            print(f"  ✓ {court['court_code']}: {court['court_name']}")
        else:
            print(f"  ✗ Failed: {court['court_code']}")

    print(f"\n  Created {len(created_ids['courts'])} courts")


# =============================================================================
# COURT FEE SLABS - DRT, NCLT Fee Structures
# =============================================================================

COURT_FEE_SLABS = [
    # DRT Filing Fees (as per DRT Rules)
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": 0, "max_claim_amount": 1000000, "calculation_type": "FIXED", "fixed_fee": 12000, "effective_from": "2024-01-01"},
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": 1000001, "max_claim_amount": 10000000, "calculation_type": "SLAB", "fixed_fee": 12000, "percentage_rate": 0.5, "effective_from": "2024-01-01"},
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": 10000001, "max_claim_amount": 100000000, "calculation_type": "SLAB", "fixed_fee": 57000, "percentage_rate": 0.25, "effective_from": "2024-01-01"},
    {"court_type": "DRT", "fee_type": "FILING", "min_claim_amount": 100000001, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 282000, "max_fee": 282000, "effective_from": "2024-01-01"},
    # DRT Interim Application Fees
    {"court_type": "DRT", "fee_type": "INTERIM_APPLICATION", "min_claim_amount": 0, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 500, "effective_from": "2024-01-01"},
    # DRT Execution Application Fees
    {"court_type": "DRT", "fee_type": "EXECUTION", "min_claim_amount": 0, "max_claim_amount": None, "calculation_type": "PERCENTAGE", "percentage_rate": 0.5, "min_fee": 1000, "max_fee": 100000, "effective_from": "2024-01-01"},
    # DRT Certified Copy Fees
    {"court_type": "DRT", "fee_type": "CERTIFIED_COPY", "min_claim_amount": 0, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 100, "process_fee": 50, "effective_from": "2024-01-01"},

    # DRAT Appeal Fees
    {"court_type": "DRAT", "fee_type": "APPEAL", "min_claim_amount": 0, "max_claim_amount": 1000000, "calculation_type": "FIXED", "fixed_fee": 15000, "effective_from": "2024-01-01"},
    {"court_type": "DRAT", "fee_type": "APPEAL", "min_claim_amount": 1000001, "max_claim_amount": 10000000, "calculation_type": "SLAB", "fixed_fee": 15000, "percentage_rate": 0.5, "effective_from": "2024-01-01"},
    {"court_type": "DRAT", "fee_type": "APPEAL", "min_claim_amount": 10000001, "max_claim_amount": 100000000, "calculation_type": "SLAB", "fixed_fee": 60000, "percentage_rate": 0.25, "effective_from": "2024-01-01"},
    {"court_type": "DRAT", "fee_type": "APPEAL", "min_claim_amount": 100000001, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 285000, "max_fee": 285000, "effective_from": "2024-01-01"},

    # NCLT IBC Fees (Section 7 - Financial Creditor)
    {"court_type": "NCLT", "fee_type": "FILING", "min_claim_amount": 0, "max_claim_amount": 10000000, "calculation_type": "FIXED", "fixed_fee": 5000, "effective_from": "2024-01-01"},
    {"court_type": "NCLT", "fee_type": "FILING", "min_claim_amount": 10000001, "max_claim_amount": 100000000, "calculation_type": "FIXED", "fixed_fee": 10000, "effective_from": "2024-01-01"},
    {"court_type": "NCLT", "fee_type": "FILING", "min_claim_amount": 100000001, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 25000, "effective_from": "2024-01-01"},
    # NCLT Interim Application Fees
    {"court_type": "NCLT", "fee_type": "INTERIM_APPLICATION", "min_claim_amount": 0, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 2000, "effective_from": "2024-01-01"},

    # NCLAT Appeal Fees
    {"court_type": "NCLAT", "fee_type": "APPEAL", "min_claim_amount": 0, "max_claim_amount": 10000000, "calculation_type": "FIXED", "fixed_fee": 10000, "effective_from": "2024-01-01"},
    {"court_type": "NCLAT", "fee_type": "APPEAL", "min_claim_amount": 10000001, "max_claim_amount": 100000000, "calculation_type": "FIXED", "fixed_fee": 15000, "effective_from": "2024-01-01"},
    {"court_type": "NCLAT", "fee_type": "APPEAL", "min_claim_amount": 100000001, "max_claim_amount": None, "calculation_type": "FIXED", "fixed_fee": 25000, "effective_from": "2024-01-01"},

    # High Court Fees (varies by state - sample for Delhi)
    {"court_type": "HIGH_COURT", "fee_type": "FILING", "min_claim_amount": 0, "max_claim_amount": 100000, "calculation_type": "PERCENTAGE", "percentage_rate": 7.5, "min_fee": 200, "effective_from": "2024-01-01"},
    {"court_type": "HIGH_COURT", "fee_type": "FILING", "min_claim_amount": 100001, "max_claim_amount": 500000, "calculation_type": "PERCENTAGE", "percentage_rate": 5.0, "effective_from": "2024-01-01"},
    {"court_type": "HIGH_COURT", "fee_type": "FILING", "min_claim_amount": 500001, "max_claim_amount": None, "calculation_type": "PERCENTAGE", "percentage_rate": 3.0, "max_fee": 150000, "effective_from": "2024-01-01"},
]


async def seed_court_fee_slabs(client: APIClient, org_id: str):
    """Seed court fee slab data."""
    print("\n=== Seeding Court Fee Slabs ===")

    for slab in COURT_FEE_SLABS:
        slab_data = {
            "organization_id": org_id,
            **slab,
        }
        result = await client.post("/legal/court-fee-slabs", slab_data)
        if result:
            created_ids["court_fee_slabs"].append(result["id"])
            print(f"  ✓ {slab['court_type']} - {slab['fee_type']}: Rs.{slab.get('min_claim_amount', 0)}-{slab.get('max_claim_amount', 'Above')}")
        else:
            print(f"  ✗ Failed: {slab['court_type']} - {slab['fee_type']}")

    print(f"\n  Created {len(created_ids['court_fee_slabs'])} court fee slabs")


# =============================================================================
# EXPENSE CATEGORIES - Legal Expense Categories
# =============================================================================

EXPENSE_CATEGORIES = [
    # Court/Filing Fees
    {"category_code": "COURT_FEE", "category_name": "Court Filing Fee", "category_type": "COURT_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 1, "display_order": 1, "description": "Filing fees payable to DRT/NCLT/Court"},
    {"category_code": "FILING_FEE", "category_name": "Document Filing Fee", "category_type": "FILING_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 2, "display_order": 2, "description": "Fee for filing documents and applications"},
    {"category_code": "PROCESS_FEE", "category_name": "Process Fee", "category_type": "PROCESS_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 3, "display_order": 3, "description": "Service/Process fee for summons and notices"},
    {"category_code": "EXECUTION_FEE", "category_name": "Execution Fee", "category_type": "EXECUTION_FEE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 4, "display_order": 4, "description": "Fee for execution proceedings"},

    # Advocate Fees
    {"category_code": "ADV_RETAINER", "category_name": "Advocate Retainer Fee", "category_type": "ADVOCATE_RETAINER", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 10, "display_order": 10, "description": "Monthly/annual retainer fee for advocate"},
    {"category_code": "ADV_APPEARANCE", "category_name": "Advocate Appearance Fee", "category_type": "ADVOCATE_APPEARANCE", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 11, "display_order": 11, "description": "Per appearance fee for court hearings"},
    {"category_code": "ADV_SUCCESS", "category_name": "Advocate Success Fee", "category_type": "ADVOCATE_SUCCESS_FEE", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 12, "display_order": 12, "description": "Success-based fee (percentage of recovery)"},

    # Valuation
    {"category_code": "VALUATION", "category_name": "Valuation Charges", "category_type": "VALUATION_CHARGES", "tds_applicable": True, "tds_section": "194J", "tds_rate": Decimal("10.00"), "gst_applicable": True, "gst_rate": Decimal("18.00"), "hsn_sac_code": "998399", "recoverable_from_borrower": True, "recovery_priority": 20, "display_order": 20, "description": "Property valuation charges"},

    # Publication
    {"category_code": "PUBLICATION", "category_name": "Newspaper Publication Charges", "category_type": "PUBLICATION_CHARGES", "tds_applicable": True, "tds_section": "194C", "tds_rate": Decimal("2.00"), "gst_applicable": True, "gst_rate": Decimal("5.00"), "hsn_sac_code": "998361", "recoverable_from_borrower": True, "recovery_priority": 21, "display_order": 21, "description": "Newspaper advertisement for auction/notice"},

    # Miscellaneous
    {"category_code": "TRAVEL", "category_name": "Travel & Conveyance", "category_type": "TRAVEL_CONVEYANCE", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 30, "display_order": 30, "description": "Travel expenses for court visits and site inspection"},
    {"category_code": "STAMP_DUTY", "category_name": "Stamp Duty", "category_type": "STAMP_DUTY", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 5, "display_order": 5, "description": "Stamp duty on legal documents"},
    {"category_code": "NOTARIZATION", "category_name": "Notarization Charges", "category_type": "NOTARIZATION", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 31, "display_order": 31, "description": "Notary fee for document attestation"},
    {"category_code": "PHOTOCOPY", "category_name": "Photocopying Charges", "category_type": "PHOTOCOPYING", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 32, "display_order": 32, "description": "Document copying and binding charges"},
    {"category_code": "COURIER", "category_name": "Courier & Postage", "category_type": "COURIER_POSTAGE", "tds_applicable": False, "gst_applicable": True, "gst_rate": Decimal("18.00"), "recoverable_from_borrower": True, "recovery_priority": 33, "display_order": 33, "description": "RPAD, Speed Post, Courier charges"},
    {"category_code": "CERSAI", "category_name": "CERSAI Charges", "category_type": "CERSAI_CHARGES", "tds_applicable": False, "gst_applicable": True, "gst_rate": Decimal("18.00"), "recoverable_from_borrower": True, "recovery_priority": 6, "display_order": 6, "description": "CERSAI registration/modification charges"},
    {"category_code": "AUCTION_EXP", "category_name": "Auction Expenses", "category_type": "AUCTION_EXPENSES", "tds_applicable": True, "tds_section": "194C", "tds_rate": Decimal("2.00"), "gst_applicable": True, "gst_rate": Decimal("18.00"), "recoverable_from_borrower": True, "recovery_priority": 22, "display_order": 22, "description": "Expenses for conducting auction"},
    {"category_code": "SECURITY", "category_name": "Security Charges", "category_type": "SECURITY_CHARGES", "tds_applicable": True, "tds_section": "194C", "tds_rate": Decimal("2.00"), "gst_applicable": True, "gst_rate": Decimal("18.00"), "hsn_sac_code": "998513", "recoverable_from_borrower": True, "recovery_priority": 23, "display_order": 23, "description": "Security guard charges for possession"},
    {"category_code": "MISC", "category_name": "Miscellaneous Expenses", "category_type": "MISCELLANEOUS", "tds_applicable": False, "gst_applicable": False, "recoverable_from_borrower": True, "recovery_priority": 99, "display_order": 99, "description": "Other legal expenses"},
]


async def seed_expense_categories(client: APIClient, org_id: str):
    """Seed expense category master data."""
    print("\n=== Seeding Expense Categories ===")

    for category in EXPENSE_CATEGORIES:
        # Convert Decimal to string for JSON serialization
        cat_data = {
            "organization_id": org_id,
            **{k: str(v) if isinstance(v, Decimal) else v for k, v in category.items()},
        }
        result = await client.post("/legal/expense-categories", cat_data)
        if result:
            created_ids["expense_categories"][category["category_code"]] = result["id"]
            print(f"  ✓ {category['category_code']}: {category['category_name']}")
        else:
            print(f"  ✗ Failed: {category['category_code']}")

    print(f"\n  Created {len(created_ids['expense_categories'])} expense categories")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("Legal Module Seed Data Script")
    print("=" * 60)

    client = APIClient(BASE_URL)

    try:
        # Login
        await client.login(ADMIN_USERNAME, ADMIN_PASSWORD)

        # Get organization
        org_id = await get_organization_id(client)
        created_ids["organization_id"] = org_id

        # Seed all master data
        await seed_statutory_periods(client, org_id)
        await seed_notice_templates(client, org_id)
        await seed_courts(client, org_id)
        await seed_court_fee_slabs(client, org_id)
        await seed_expense_categories(client, org_id)

        # Summary
        print("\n" + "=" * 60)
        print("SEED DATA SUMMARY")
        print("=" * 60)
        print(f"  Statutory Periods: {len(created_ids['statutory_periods'])}")
        print(f"  Notice Templates:  {len(created_ids['notice_templates'])}")
        print(f"  Courts:            {len(created_ids['courts'])}")
        print(f"  Court Fee Slabs:   {len(created_ids['court_fee_slabs'])}")
        print(f"  Expense Categories:{len(created_ids['expense_categories'])}")
        print("=" * 60)
        print("✓ Legal Module seed data created successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
