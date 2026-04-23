"""Seed ESS Portal master data.

This script seeds:
1. IT Declaration Sections (80C, 80D, HRA, etc.)
2. Reimbursement Categories
3. Helpdesk Categories
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


# ==================== IT DECLARATION SECTIONS ====================
# Based on Indian Income Tax Act provisions for FY 2024-25

IT_DECLARATION_SECTIONS = [
    # Section 80C - Investments
    {
        "section_code": "80C",
        "section_name": "Section 80C - Investments",
        "description": "Deduction for investments in PPF, ELSS, Life Insurance Premium, NSC, etc.",
        "max_limit": Decimal("150000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Investment receipts, premium payment receipts, certificates",
        "display_order": 1,
    },
    # Section 80CCC - Pension Funds
    {
        "section_code": "80CCC",
        "section_name": "Section 80CCC - Pension Funds",
        "description": "Deduction for contribution to pension funds (LIC Jeevan Suraksha, etc.)",
        "max_limit": Decimal("150000.00"),  # Combined with 80C
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Premium payment receipts",
        "display_order": 2,
    },
    # Section 80CCD(1) - NPS Employee Contribution
    {
        "section_code": "80CCD1",
        "section_name": "Section 80CCD(1) - NPS Employee Contribution",
        "description": "Employee contribution to National Pension System (up to 10% of salary)",
        "max_limit": Decimal("150000.00"),  # Combined with 80C
        "is_active": True,
        "requires_proof": True,
        "proof_description": "NPS contribution statement",
        "display_order": 3,
    },
    # Section 80CCD(1B) - Additional NPS
    {
        "section_code": "80CCD1B",
        "section_name": "Section 80CCD(1B) - Additional NPS Contribution",
        "description": "Additional deduction for NPS contribution (over and above 80C limit)",
        "max_limit": Decimal("50000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "NPS contribution statement",
        "display_order": 4,
    },
    # Section 80CCD(2) - Employer NPS Contribution
    {
        "section_code": "80CCD2",
        "section_name": "Section 80CCD(2) - Employer NPS Contribution",
        "description": "Employer contribution to NPS (up to 14% for Central Govt, 10% for others)",
        "max_limit": Decimal("0.00"),  # No fixed limit, percentage based
        "is_active": True,
        "requires_proof": False,
        "proof_description": "Automatically computed from salary",
        "display_order": 5,
    },
    # Section 80D - Medical Insurance (Self & Family)
    {
        "section_code": "80D_SELF",
        "section_name": "Section 80D - Medical Insurance (Self & Family)",
        "description": "Premium for medical insurance for self, spouse and dependent children",
        "max_limit": Decimal("25000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Premium payment receipts, policy documents",
        "display_order": 6,
    },
    # Section 80D - Medical Insurance (Parents)
    {
        "section_code": "80D_PARENTS",
        "section_name": "Section 80D - Medical Insurance (Parents)",
        "description": "Premium for medical insurance for parents (₹50,000 if senior citizen)",
        "max_limit": Decimal("50000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Premium payment receipts, policy documents",
        "display_order": 7,
    },
    # Section 80D - Preventive Health Check-up
    {
        "section_code": "80D_PHC",
        "section_name": "Section 80D - Preventive Health Check-up",
        "description": "Preventive health check-up expenses (within 80D limit)",
        "max_limit": Decimal("5000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Medical bills, receipts",
        "display_order": 8,
    },
    # Section 80DD - Disabled Dependent
    {
        "section_code": "80DD",
        "section_name": "Section 80DD - Disabled Dependent",
        "description": "Deduction for maintenance of disabled dependent (₹1.25L for severe disability)",
        "max_limit": Decimal("125000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Disability certificate from medical authority",
        "display_order": 9,
    },
    # Section 80DDB - Medical Treatment
    {
        "section_code": "80DDB",
        "section_name": "Section 80DDB - Medical Treatment",
        "description": "Expenses on treatment of specified diseases (₹1L for senior citizen)",
        "max_limit": Decimal("100000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Medical bills, prescription from specialist",
        "display_order": 10,
    },
    # Section 80E - Education Loan Interest
    {
        "section_code": "80E",
        "section_name": "Section 80E - Education Loan Interest",
        "description": "Interest on education loan for higher studies (no limit)",
        "max_limit": Decimal("0.00"),  # No upper limit
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Interest certificate from bank/NBFC",
        "display_order": 11,
    },
    # Section 80EE - Home Loan Interest (First-time buyers)
    {
        "section_code": "80EE",
        "section_name": "Section 80EE - Home Loan Interest (First-time)",
        "description": "Additional deduction for first-time home buyers (loan up to ₹35L, property up to ₹50L)",
        "max_limit": Decimal("50000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Interest certificate from bank, property documents",
        "display_order": 12,
    },
    # Section 80EEA - Affordable Housing
    {
        "section_code": "80EEA",
        "section_name": "Section 80EEA - Affordable Housing Interest",
        "description": "Interest on home loan for affordable housing (stamp duty up to ₹45L)",
        "max_limit": Decimal("150000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Interest certificate, stamp duty value certificate",
        "display_order": 13,
    },
    # Section 80G - Donations
    {
        "section_code": "80G",
        "section_name": "Section 80G - Donations",
        "description": "Donations to specified funds and charitable institutions",
        "max_limit": Decimal("0.00"),  # Varies by donation type
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Donation receipts with PAN of donee, 80G certificate",
        "display_order": 14,
    },
    # Section 80GG - Rent Paid (No HRA)
    {
        "section_code": "80GG",
        "section_name": "Section 80GG - Rent Paid (No HRA)",
        "description": "Rent paid when HRA is not part of salary (max ₹5,000/month)",
        "max_limit": Decimal("60000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Rent receipts, rental agreement, landlord PAN (if rent > ₹1L/year)",
        "display_order": 15,
    },
    # Section 80TTA - Savings Interest
    {
        "section_code": "80TTA",
        "section_name": "Section 80TTA - Savings Account Interest",
        "description": "Interest from savings accounts (banks, post office)",
        "max_limit": Decimal("10000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Bank statements showing interest earned",
        "display_order": 16,
    },
    # Section 80TTB - Senior Citizen Interest
    {
        "section_code": "80TTB",
        "section_name": "Section 80TTB - Senior Citizen Interest",
        "description": "Interest income for senior citizens (60+ years) from deposits",
        "max_limit": Decimal("50000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Interest certificates from banks/post office",
        "display_order": 17,
    },
    # Section 80U - Self Disability
    {
        "section_code": "80U",
        "section_name": "Section 80U - Person with Disability",
        "description": "Deduction for person with disability (₹1.25L for severe disability)",
        "max_limit": Decimal("125000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Disability certificate from medical authority",
        "display_order": 18,
    },
    # Section 24b - Home Loan Interest
    {
        "section_code": "24B",
        "section_name": "Section 24(b) - Home Loan Interest",
        "description": "Interest on housing loan for self-occupied property",
        "max_limit": Decimal("200000.00"),
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Interest certificate from bank/HFC, possession certificate",
        "display_order": 19,
    },
    # HRA Exemption
    {
        "section_code": "HRA",
        "section_name": "HRA Exemption - House Rent Allowance",
        "description": "Exemption under Section 10(13A) for HRA received",
        "max_limit": Decimal("0.00"),  # Computed based on rules
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Rent receipts, rental agreement, landlord PAN (if rent > ₹1L/year)",
        "display_order": 20,
    },
    # LTA Exemption
    {
        "section_code": "LTA",
        "section_name": "LTA Exemption - Leave Travel Allowance",
        "description": "Exemption under Section 10(5) for travel within India",
        "max_limit": Decimal("0.00"),  # Based on actuals
        "is_active": True,
        "requires_proof": True,
        "proof_description": "Travel tickets, boarding passes (economy class)",
        "display_order": 21,
    },
]


# ==================== REIMBURSEMENT CATEGORIES ====================

REIMBURSEMENT_CATEGORIES = [
    # Medical Reimbursement
    {
        "code": "MED",
        "name": "Medical Reimbursement",
        "description": "Reimbursement for medical expenses not covered by insurance",
        "max_amount_per_claim": Decimal("50000.00"),
        "max_amount_per_year": Decimal("100000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 1,
    },
    # Travel Reimbursement
    {
        "code": "TRV",
        "name": "Travel Reimbursement",
        "description": "Local and outstation travel expenses for official work",
        "max_amount_per_claim": Decimal("25000.00"),
        "max_amount_per_year": Decimal("200000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 2,
    },
    # Conveyance Reimbursement
    {
        "code": "CONV",
        "name": "Conveyance Reimbursement",
        "description": "Daily commute and local travel expenses",
        "max_amount_per_claim": Decimal("5000.00"),
        "max_amount_per_year": Decimal("50000.00"),
        "requires_receipt": False,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 3,
    },
    # Food & Meals
    {
        "code": "FOOD",
        "name": "Food & Meals Reimbursement",
        "description": "Meals during official work hours or client meetings",
        "max_amount_per_claim": Decimal("5000.00"),
        "max_amount_per_year": Decimal("60000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 4,
    },
    # Mobile & Internet
    {
        "code": "COMM",
        "name": "Communication Reimbursement",
        "description": "Mobile phone and internet expenses for official use",
        "max_amount_per_claim": Decimal("2000.00"),
        "max_amount_per_year": Decimal("24000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 5,
    },
    # Books & Subscriptions
    {
        "code": "BOOKS",
        "name": "Books & Subscriptions",
        "description": "Professional books, journals, and online subscriptions",
        "max_amount_per_claim": Decimal("10000.00"),
        "max_amount_per_year": Decimal("25000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 6,
    },
    # Training & Certification
    {
        "code": "TRAIN",
        "name": "Training & Certification",
        "description": "Professional training courses and certification exams",
        "max_amount_per_claim": Decimal("50000.00"),
        "max_amount_per_year": Decimal("100000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "HR",
        "is_active": True,
        "display_order": 7,
    },
    # Work From Home
    {
        "code": "WFH",
        "name": "Work From Home Expenses",
        "description": "Equipment and utilities for remote work setup",
        "max_amount_per_claim": Decimal("15000.00"),
        "max_amount_per_year": Decimal("30000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "HR",
        "is_active": True,
        "display_order": 8,
    },
    # Relocation Expenses
    {
        "code": "RELOC",
        "name": "Relocation Expenses",
        "description": "Expenses for job-related relocation",
        "max_amount_per_claim": Decimal("200000.00"),
        "max_amount_per_year": Decimal("200000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "HR_HEAD",
        "is_active": True,
        "display_order": 9,
    },
    # Client Entertainment
    {
        "code": "CLIENT",
        "name": "Client Entertainment",
        "description": "Business entertainment expenses for clients",
        "max_amount_per_claim": Decimal("25000.00"),
        "max_amount_per_year": Decimal("100000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "DEPARTMENT_HEAD",
        "is_active": True,
        "display_order": 10,
    },
    # Miscellaneous
    {
        "code": "MISC",
        "name": "Miscellaneous Expenses",
        "description": "Other work-related expenses not covered above",
        "max_amount_per_claim": Decimal("10000.00"),
        "max_amount_per_year": Decimal("50000.00"),
        "requires_receipt": True,
        "requires_approval": True,
        "approval_level": "MANAGER",
        "is_active": True,
        "display_order": 11,
    },
]


# ==================== HELPDESK CATEGORIES ====================

HELPDESK_CATEGORIES = [
    # HR Queries
    {
        "code": "HR_GENERAL",
        "name": "HR General Query",
        "description": "General HR-related queries and information requests",
        "department": "HR",
        "response_sla_hours": 24,
        "resolution_sla_hours": 72,
        "is_active": True,
        "display_order": 1,
    },
    {
        "code": "HR_LEAVE",
        "name": "Leave & Attendance",
        "description": "Queries related to leave balance, attendance, regularization",
        "department": "HR",
        "response_sla_hours": 8,
        "resolution_sla_hours": 48,
        "is_active": True,
        "display_order": 2,
    },
    {
        "code": "HR_PAYROLL",
        "name": "Payroll & Salary",
        "description": "Queries about salary, deductions, payslips, reimbursements",
        "department": "HR",
        "response_sla_hours": 8,
        "resolution_sla_hours": 48,
        "is_active": True,
        "display_order": 3,
    },
    {
        "code": "HR_BENEFITS",
        "name": "Benefits & Insurance",
        "description": "Medical insurance, PF, gratuity, ESIC related queries",
        "department": "HR",
        "response_sla_hours": 24,
        "resolution_sla_hours": 72,
        "is_active": True,
        "display_order": 4,
    },
    {
        "code": "HR_POLICY",
        "name": "Policy Clarification",
        "description": "Clarifications on company policies and procedures",
        "department": "HR",
        "response_sla_hours": 24,
        "resolution_sla_hours": 96,
        "is_active": True,
        "display_order": 5,
    },
    {
        "code": "HR_DOCS",
        "name": "Document Request",
        "description": "Employment letters, experience certificates, etc.",
        "department": "HR",
        "response_sla_hours": 8,
        "resolution_sla_hours": 72,
        "is_active": True,
        "display_order": 6,
    },
    {
        "code": "HR_COMPLAINT",
        "name": "Grievance & Complaint",
        "description": "Employee grievances and workplace complaints",
        "department": "HR",
        "response_sla_hours": 4,
        "resolution_sla_hours": 168,  # 7 days
        "is_active": True,
        "display_order": 7,
    },
    # IT Support
    {
        "code": "IT_GENERAL",
        "name": "IT General Support",
        "description": "General IT support and queries",
        "department": "IT",
        "response_sla_hours": 4,
        "resolution_sla_hours": 24,
        "is_active": True,
        "display_order": 8,
    },
    {
        "code": "IT_HARDWARE",
        "name": "Hardware Issue",
        "description": "Laptop, desktop, printer, peripherals issues",
        "department": "IT",
        "response_sla_hours": 4,
        "resolution_sla_hours": 48,
        "is_active": True,
        "display_order": 9,
    },
    {
        "code": "IT_SOFTWARE",
        "name": "Software Issue",
        "description": "Application errors, software installation, updates",
        "department": "IT",
        "response_sla_hours": 4,
        "resolution_sla_hours": 24,
        "is_active": True,
        "display_order": 10,
    },
    {
        "code": "IT_ACCESS",
        "name": "Access Request",
        "description": "System access, password reset, permissions",
        "department": "IT",
        "response_sla_hours": 4,
        "resolution_sla_hours": 24,
        "is_active": True,
        "display_order": 11,
    },
    {
        "code": "IT_NETWORK",
        "name": "Network & Connectivity",
        "description": "Internet, VPN, email, network connectivity issues",
        "department": "IT",
        "response_sla_hours": 2,
        "resolution_sla_hours": 8,
        "is_active": True,
        "display_order": 12,
    },
    {
        "code": "IT_SECURITY",
        "name": "Security Incident",
        "description": "Security concerns, suspicious activity, data breach",
        "department": "IT",
        "response_sla_hours": 1,
        "resolution_sla_hours": 24,
        "is_active": True,
        "display_order": 13,
    },
    # Admin/Facilities
    {
        "code": "ADMIN_FACILITY",
        "name": "Facility Request",
        "description": "Office facility, seating, parking, access cards",
        "department": "ADMIN",
        "response_sla_hours": 8,
        "resolution_sla_hours": 48,
        "is_active": True,
        "display_order": 14,
    },
    {
        "code": "ADMIN_TRANSPORT",
        "name": "Transport",
        "description": "Company transport, cab booking, travel arrangements",
        "department": "ADMIN",
        "response_sla_hours": 4,
        "resolution_sla_hours": 24,
        "is_active": True,
        "display_order": 15,
    },
    # Finance
    {
        "code": "FIN_EXPENSE",
        "name": "Expense Reimbursement",
        "description": "Queries about expense claims and reimbursements",
        "department": "FINANCE",
        "response_sla_hours": 8,
        "resolution_sla_hours": 48,
        "is_active": True,
        "display_order": 16,
    },
    {
        "code": "FIN_TAX",
        "name": "Tax Related",
        "description": "IT declarations, Form 16, TDS queries",
        "department": "FINANCE",
        "response_sla_hours": 24,
        "resolution_sla_hours": 72,
        "is_active": True,
        "display_order": 17,
    },
]


async def seed_it_declaration_sections(session: AsyncSession, org_id: str):
    """Seed IT declaration sections."""
    print("\nSeeding IT Declaration Sections...")

    for section in IT_DECLARATION_SECTIONS:
        # Check if exists
        result = await session.execute(
            text("""
                SELECT id FROM mst_it_declaration_section
                WHERE organization_id = :org_id AND section_code = :code
            """),
            {"org_id": org_id, "code": section["section_code"]}
        )
        existing = result.fetchone()

        if existing:
            print(f"  - {section['section_code']}: Already exists, skipping")
            continue

        section_id = str(uuid4())
        await session.execute(
            text("""
                INSERT INTO mst_it_declaration_section (
                    id, organization_id, section_code, section_name, description,
                    category, max_limit, requires_proof, help_text, display_order,
                    applicable_from_fy, applicable_in_old_regime, applicable_in_new_regime,
                    is_active, created_at, updated_at
                ) VALUES (
                    :id, :org_id, :section_code, :section_name, :description,
                    :category, :max_limit, :requires_proof, :help_text, :display_order,
                    :applicable_from_fy, :applicable_in_old_regime, :applicable_in_new_regime,
                    :is_active, NOW(), NOW()
                )
            """),
            {
                "id": section_id,
                "org_id": org_id,
                "section_code": section["section_code"],
                "section_name": section["section_name"],
                "description": section["description"],
                "category": "DEDUCTION",  # Default category
                "max_limit": section["max_limit"],
                "requires_proof": section["requires_proof"],
                "help_text": section["proof_description"],  # Map proof_description to help_text
                "display_order": section["display_order"],
                "applicable_from_fy": "2024-25",
                "applicable_in_old_regime": True,
                "applicable_in_new_regime": False,
                "is_active": section["is_active"],
            }
        )
        print(f"  - {section['section_code']}: Created")

    await session.commit()
    print(f"  Total: {len(IT_DECLARATION_SECTIONS)} sections processed")


async def seed_reimbursement_categories(session: AsyncSession, org_id: str):
    """Seed reimbursement categories."""
    print("\nSeeding Reimbursement Categories...")

    for category in REIMBURSEMENT_CATEGORIES:
        # Check if exists
        result = await session.execute(
            text("""
                SELECT id FROM mst_reimbursement_category
                WHERE organization_id = :org_id AND code = :code
            """),
            {"org_id": org_id, "code": category["code"]}
        )
        existing = result.fetchone()

        if existing:
            print(f"  - {category['code']}: Already exists, skipping")
            continue

        category_id = str(uuid4())
        await session.execute(
            text("""
                INSERT INTO mst_reimbursement_category (
                    id, organization_id, code, name, description,
                    claim_type, max_amount_per_claim, max_amount_per_year,
                    requires_bills, requires_approval, is_active,
                    created_at, updated_at
                ) VALUES (
                    :id, :org_id, :code, :name, :description,
                    :claim_type, :max_amount_per_claim, :max_amount_per_year,
                    :requires_bills, :requires_approval, :is_active,
                    NOW(), NOW()
                )
            """),
            {
                "id": category_id,
                "org_id": org_id,
                "code": category["code"],
                "name": category["name"],
                "description": category["description"],
                "claim_type": category["code"],  # Use code as claim_type
                "max_amount_per_claim": category["max_amount_per_claim"],
                "max_amount_per_year": category["max_amount_per_year"],
                "requires_bills": category["requires_receipt"],
                "requires_approval": category["requires_approval"],
                "is_active": category["is_active"],
            }
        )
        print(f"  - {category['code']}: Created")

    await session.commit()
    print(f"  Total: {len(REIMBURSEMENT_CATEGORIES)} categories processed")


async def seed_helpdesk_categories(session: AsyncSession, org_id: str):
    """Seed helpdesk ticket categories."""
    print("\nSeeding Helpdesk Categories...")

    for category in HELPDESK_CATEGORIES:
        # Check if exists
        result = await session.execute(
            text("""
                SELECT id FROM mst_helpdesk_category
                WHERE organization_id = :org_id AND code = :code
            """),
            {"org_id": org_id, "code": category["code"]}
        )
        existing = result.fetchone()

        if existing:
            print(f"  - {category['code']}: Already exists, skipping")
            continue

        category_id = str(uuid4())
        await session.execute(
            text("""
                INSERT INTO mst_helpdesk_category (
                    id, organization_id, code, name, description,
                    category_type, department, response_sla_hours, resolution_sla_hours,
                    is_active, created_at, updated_at
                ) VALUES (
                    :id, :org_id, :code, :name, :description,
                    :category_type, :department, :response_sla_hours, :resolution_sla_hours,
                    :is_active, NOW(), NOW()
                )
            """),
            {
                "id": category_id,
                "org_id": org_id,
                "code": category["code"],
                "name": category["name"],
                "description": category["description"],
                "category_type": category["department"],  # Use department as category_type
                "department": category["department"],
                "response_sla_hours": category["response_sla_hours"],
                "resolution_sla_hours": category["resolution_sla_hours"],
                "is_active": category["is_active"],
            }
        )
        print(f"  - {category['code']}: Created")

    await session.commit()
    print(f"  Total: {len(HELPDESK_CATEGORIES)} categories processed")


async def main():
    """Main function to run all seeders."""
    print("=" * 60)
    print("ESS Portal Master Data Seeder")
    print("=" * 60)

    # Get database URL
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Create engine
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get default organization
        result = await session.execute(
            text("SELECT id, name FROM mst_organization WHERE is_active = true LIMIT 1")
        )
        org = result.fetchone()

        if not org:
            print("\nERROR: No active organization found. Please create an organization first.")
            return

        org_id = str(org[0])
        print(f"\nUsing Organization: {org[1]} ({org_id})")

        # Run seeders
        await seed_it_declaration_sections(session, org_id)
        await seed_reimbursement_categories(session, org_id)
        await seed_helpdesk_categories(session, org_id)

        print("\n" + "=" * 60)
        print("ESS Portal Master Data Seeding Complete!")
        print("=" * 60)

        # Print summary
        print("\nSummary:")
        print(f"  - IT Declaration Sections: {len(IT_DECLARATION_SECTIONS)}")
        print(f"  - Reimbursement Categories: {len(REIMBURSEMENT_CATEGORIES)}")
        print(f"  - Helpdesk Categories: {len(HELPDESK_CATEGORIES)}")


if __name__ == "__main__":
    asyncio.run(main())
