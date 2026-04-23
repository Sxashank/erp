"""
Direct database seed script for KYC & Compliance Module master data.
Inserts data directly into the database without requiring API authentication.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_kyc_data.py
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp"
)

# Import models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# KYC DOCUMENT TYPES DATA
# =============================================================================

KYC_DOCUMENT_TYPES = [
    # Identity Proof
    {
        "document_code": "KYC-ID-PAN",
        "document_name": "PAN Card",
        "document_category": "IDENTITY",
        "description": "Permanent Account Number card issued by Income Tax Department",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": None,  # No expiry
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 1,
        "is_active": True,
    },
    {
        "document_code": "KYC-ID-AADHAAR",
        "document_name": "Aadhaar Card",
        "document_category": "IDENTITY",
        "description": "Unique Identification Number issued by UIDAI",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": None,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 2,
        "is_active": True,
    },
    {
        "document_code": "KYC-ID-PASSPORT",
        "document_name": "Passport",
        "document_category": "IDENTITY",
        "description": "Valid Indian Passport",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": None,  # Has expiry date on document
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 3,
        "is_active": True,
    },
    {
        "document_code": "KYC-ID-VOTER",
        "document_name": "Voter ID Card",
        "document_category": "IDENTITY",
        "description": "Election Commission Voter Identity Card",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": None,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 4,
        "is_active": True,
    },
    {
        "document_code": "KYC-ID-DL",
        "document_name": "Driving License",
        "document_category": "IDENTITY",
        "description": "Valid Driving License issued by RTO",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": None,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 5,
        "is_active": True,
    },
    # Address Proof
    {
        "document_code": "KYC-ADDR-UTIL",
        "document_name": "Utility Bill",
        "document_category": "ADDRESS",
        "description": "Electricity, Water, Gas, or Telephone Bill (not older than 3 months)",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 3,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 10,
        "is_active": True,
    },
    {
        "document_code": "KYC-ADDR-BANK",
        "document_name": "Bank Statement",
        "document_category": "ADDRESS",
        "description": "Latest Bank Statement or Passbook (not older than 3 months)",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 3,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 11,
        "is_active": True,
    },
    {
        "document_code": "KYC-ADDR-RENT",
        "document_name": "Rent Agreement",
        "document_category": "ADDRESS",
        "description": "Registered Rent Agreement with landlord NOC",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP"],
        "validity_months": 12,
        "max_file_size_mb": 10,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 12,
        "is_active": True,
    },
    {
        "document_code": "KYC-ADDR-PROP",
        "document_name": "Property Documents",
        "document_category": "ADDRESS",
        "description": "Sale Deed, Registry, or Property Tax Receipt",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": None,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 13,
        "is_active": True,
    },
    # Income Proof
    {
        "document_code": "KYC-INC-ITR",
        "document_name": "Income Tax Return",
        "document_category": "INCOME",
        "description": "ITR for last 2-3 financial years with acknowledgment",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 12,
        "max_file_size_mb": 10,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 20,
        "is_active": True,
    },
    {
        "document_code": "KYC-INC-SALARY",
        "document_name": "Salary Slips",
        "document_category": "INCOME",
        "description": "Latest 3-6 months salary slips",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": 3,
        "max_file_size_mb": 10,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 21,
        "is_active": True,
    },
    {
        "document_code": "KYC-INC-FORM16",
        "document_name": "Form 16",
        "document_category": "INCOME",
        "description": "Form 16 for salaried individuals",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": 12,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 22,
        "is_active": True,
    },
    {
        "document_code": "KYC-INC-BANKSTMT",
        "document_name": "Bank Statement (Income)",
        "document_category": "INCOME",
        "description": "Last 6-12 months bank statement",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 1,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 23,
        "is_active": True,
    },
    # Business Documents
    {
        "document_code": "KYC-BUS-COI",
        "document_name": "Certificate of Incorporation",
        "document_category": "BUSINESS",
        "description": "MCA Certificate of Incorporation",
        "is_mandatory": True,
        "applies_to": ["COMPANY", "LLP"],
        "validity_months": None,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 30,
        "is_active": True,
    },
    {
        "document_code": "KYC-BUS-MOA",
        "document_name": "Memorandum of Association",
        "document_category": "BUSINESS",
        "description": "MOA for Company",
        "is_mandatory": True,
        "applies_to": ["COMPANY"],
        "validity_months": None,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 31,
        "is_active": True,
    },
    {
        "document_code": "KYC-BUS-AOA",
        "document_name": "Articles of Association",
        "document_category": "BUSINESS",
        "description": "AOA for Company",
        "is_mandatory": True,
        "applies_to": ["COMPANY"],
        "validity_months": None,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 32,
        "is_active": True,
    },
    {
        "document_code": "KYC-BUS-PARTNER",
        "document_name": "Partnership Deed",
        "document_category": "BUSINESS",
        "description": "Registered Partnership Deed",
        "is_mandatory": True,
        "applies_to": ["PARTNERSHIP"],
        "validity_months": None,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 33,
        "is_active": True,
    },
    {
        "document_code": "KYC-BUS-GST",
        "document_name": "GST Registration Certificate",
        "document_category": "BUSINESS",
        "description": "GST Registration Certificate",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP"],
        "validity_months": None,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 34,
        "is_active": True,
    },
    {
        "document_code": "KYC-BUS-UDYAM",
        "document_name": "Udyam Registration Certificate",
        "document_category": "BUSINESS",
        "description": "MSME Udyam Registration",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP"],
        "validity_months": None,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": True,
        "display_order": 35,
        "is_active": True,
    },
    {
        "document_code": "KYC-BUS-SHOP",
        "document_name": "Shop & Establishment License",
        "document_category": "BUSINESS",
        "description": "Shop Act Registration Certificate",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP"],
        "validity_months": 12,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 36,
        "is_active": True,
    },
    # Financial Documents
    {
        "document_code": "KYC-FIN-AUD",
        "document_name": "Audited Financial Statements",
        "document_category": "FINANCIAL",
        "description": "Audited Balance Sheet, P&L for last 2-3 years",
        "is_mandatory": True,
        "applies_to": ["COMPANY", "PARTNERSHIP", "LLP"],
        "validity_months": 12,
        "max_file_size_mb": 50,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 40,
        "is_active": True,
    },
    {
        "document_code": "KYC-FIN-GSTR",
        "document_name": "GST Returns",
        "document_category": "FINANCIAL",
        "description": "GSTR-1 and GSTR-3B for last 12 months",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP"],
        "validity_months": 3,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 41,
        "is_active": True,
    },
    # Collateral Documents
    {
        "document_code": "KYC-COLL-TITLE",
        "document_name": "Property Title Deed",
        "document_category": "COLLATERAL",
        "description": "Original Sale Deed or Conveyance Deed",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": None,
        "max_file_size_mb": 50,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 50,
        "is_active": True,
    },
    {
        "document_code": "KYC-COLL-EC",
        "document_name": "Encumbrance Certificate",
        "document_category": "COLLATERAL",
        "description": "EC for last 13-30 years",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 1,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 51,
        "is_active": True,
    },
    {
        "document_code": "KYC-COLL-VALUATION",
        "document_name": "Property Valuation Report",
        "document_category": "COLLATERAL",
        "description": "Valuation report from empaneled valuer",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 6,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 52,
        "is_active": True,
    },
    {
        "document_code": "KYC-COLL-TAX",
        "document_name": "Property Tax Receipt",
        "document_category": "COLLATERAL",
        "description": "Latest Property Tax Payment Receipt",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": 12,
        "max_file_size_mb": 5,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 53,
        "is_active": True,
    },
    {
        "document_code": "KYC-COLL-MAP",
        "document_name": "Approved Building Plan",
        "document_category": "COLLATERAL",
        "description": "Sanctioned Building Plan from local authority",
        "is_mandatory": False,
        "applies_to": ["INDIVIDUAL", "COMPANY", "PARTNERSHIP", "LLP", "TRUST", "HUF"],
        "validity_months": None,
        "max_file_size_mb": 20,
        "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
        "verification_required": True,
        "ocr_enabled": False,
        "display_order": 54,
        "is_active": True,
    },
    # Photo & Signature
    {
        "document_code": "KYC-PHOTO",
        "document_name": "Passport Size Photo",
        "document_category": "PHOTO",
        "description": "Recent passport size photograph",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": 6,
        "max_file_size_mb": 2,
        "allowed_formats": ["JPG", "JPEG", "PNG"],
        "verification_required": False,
        "ocr_enabled": False,
        "display_order": 60,
        "is_active": True,
    },
    {
        "document_code": "KYC-SIGN",
        "document_name": "Signature Specimen",
        "document_category": "SIGNATURE",
        "description": "Specimen signature for verification",
        "is_mandatory": True,
        "applies_to": ["INDIVIDUAL"],
        "validity_months": None,
        "max_file_size_mb": 1,
        "allowed_formats": ["JPG", "JPEG", "PNG"],
        "verification_required": False,
        "ocr_enabled": False,
        "display_order": 61,
        "is_active": True,
    },
]


# =============================================================================
# CREDIT BUREAUS DATA
# =============================================================================

CREDIT_BUREAUS = [
    {
        "bureau_code": "CIBIL",
        "bureau_name": "TransUnion CIBIL",
        "description": "Credit Information Bureau (India) Limited",
        "api_endpoint": "https://api.cibil.com/v1",
        "report_validity_days": 30,
        "score_range_min": 300,
        "score_range_max": 900,
        "good_score_threshold": 750,
        "is_active": True,
    },
    {
        "bureau_code": "EQUIFAX",
        "bureau_name": "Equifax India",
        "description": "Equifax Credit Information Services",
        "api_endpoint": "https://api.equifax.in/v1",
        "report_validity_days": 30,
        "score_range_min": 300,
        "score_range_max": 900,
        "good_score_threshold": 750,
        "is_active": True,
    },
    {
        "bureau_code": "EXPERIAN",
        "bureau_name": "Experian India",
        "description": "Experian Credit Information Company",
        "api_endpoint": "https://api.experian.in/v1",
        "report_validity_days": 30,
        "score_range_min": 300,
        "score_range_max": 900,
        "good_score_threshold": 750,
        "is_active": True,
    },
    {
        "bureau_code": "CRIF",
        "bureau_name": "CRIF High Mark",
        "description": "CRIF High Mark Credit Information Services",
        "api_endpoint": "https://api.crifhighmark.com/v1",
        "report_validity_days": 30,
        "score_range_min": 300,
        "score_range_max": 900,
        "good_score_threshold": 750,
        "is_active": True,
    },
]


# =============================================================================
# KYC VERIFICATION AGENCIES DATA
# =============================================================================

KYC_VERIFICATION_AGENCIES = [
    {
        "agency_code": "DIGILOCKER",
        "agency_name": "DigiLocker",
        "description": "Government digital document wallet",
        "verification_type": "DIGITAL",
        "api_endpoint": "https://api.digilocker.gov.in/v1",
        "documents_supported": ["AADHAAR", "PAN", "DL", "VOTER_ID"],
        "is_active": True,
    },
    {
        "agency_code": "NSDL",
        "agency_name": "NSDL e-Gov",
        "description": "PAN Verification through NSDL",
        "verification_type": "API",
        "api_endpoint": "https://pan.nsdl.com/api/v1",
        "documents_supported": ["PAN"],
        "is_active": True,
    },
    {
        "agency_code": "UIDAI",
        "agency_name": "UIDAI",
        "description": "Aadhaar verification through UIDAI",
        "verification_type": "API",
        "api_endpoint": "https://uidai.gov.in/api/v1",
        "documents_supported": ["AADHAAR"],
        "is_active": True,
    },
    {
        "agency_code": "MCA",
        "agency_name": "MCA Portal",
        "description": "Company/LLP verification through MCA",
        "verification_type": "API",
        "api_endpoint": "https://www.mca.gov.in/api/v1",
        "documents_supported": ["COI", "DIR_KYC", "CIN"],
        "is_active": True,
    },
    {
        "agency_code": "GST",
        "agency_name": "GST Portal",
        "description": "GSTIN verification through GST Portal",
        "verification_type": "API",
        "api_endpoint": "https://gst.gov.in/api/v1",
        "documents_supported": ["GSTIN"],
        "is_active": True,
    },
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("KYC & Compliance Module Direct Seed Script")
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

            # Seed KYC Document Types
            print("\n--- Seeding KYC Document Types ---")
            count = 0
            for doc_data in KYC_DOCUMENT_TYPES:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_kyc_document_type WHERE organization_id = :org_id AND document_code = :code"),
                    {"org_id": org_id, "code": doc_data["document_code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {doc_data['document_code']}")
                    continue

                # Insert document type
                await session.execute(
                    text("""
                        INSERT INTO mst_kyc_document_type (
                            organization_id, document_code, document_name, document_category,
                            description, is_mandatory, applies_to, validity_months,
                            max_file_size_mb, allowed_formats, verification_required,
                            ocr_enabled, display_order, is_active, created_by_id
                        ) VALUES (
                            :org_id, :document_code, :document_name, :document_category,
                            :description, :is_mandatory, :applies_to, :validity_months,
                            :max_file_size_mb, :allowed_formats, :verification_required,
                            :ocr_enabled, :display_order, :is_active, :user_id
                        )
                    """),
                    {
                        "org_id": org_id,
                        "document_code": doc_data["document_code"],
                        "document_name": doc_data["document_name"],
                        "document_category": doc_data["document_category"],
                        "description": doc_data["description"],
                        "is_mandatory": doc_data["is_mandatory"],
                        "applies_to": doc_data["applies_to"],
                        "validity_months": doc_data["validity_months"],
                        "max_file_size_mb": doc_data["max_file_size_mb"],
                        "allowed_formats": doc_data["allowed_formats"],
                        "verification_required": doc_data["verification_required"],
                        "ocr_enabled": doc_data["ocr_enabled"],
                        "display_order": doc_data["display_order"],
                        "is_active": doc_data["is_active"],
                        "user_id": user_id,
                    }
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} KYC document types")

            print("\n" + "=" * 60)
            print("✓ KYC & Compliance Module seed data created successfully!")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
