"""
Direct database seed script for Treasury Module master data.
Inserts data directly into the database without requiring API authentication.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_treasury_data.py
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
# INVESTMENT CATEGORIES DATA
# =============================================================================

INVESTMENT_CATEGORIES = [
    # Government Securities
    {
        "category_code": "INV-GSEC",
        "category_name": "Government Securities",
        "description": "Central and State Government Securities",
        "investment_type": "DEBT",
        "risk_category": "LOW",
        "slr_eligible": True,
        "npa_classification_days": None,
        "valuation_method": "MARK_TO_MARKET",
        "is_active": True,
    },
    {
        "category_code": "INV-TBILL",
        "category_name": "Treasury Bills",
        "description": "91-day, 182-day, and 364-day Treasury Bills",
        "investment_type": "DEBT",
        "risk_category": "LOW",
        "slr_eligible": True,
        "npa_classification_days": None,
        "valuation_method": "AMORTIZED_COST",
        "is_active": True,
    },
    # Corporate Bonds
    {
        "category_code": "INV-CORP-AAA",
        "category_name": "Corporate Bonds - AAA Rated",
        "description": "AAA rated corporate bonds and debentures",
        "investment_type": "DEBT",
        "risk_category": "LOW",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "MARK_TO_MARKET",
        "is_active": True,
    },
    {
        "category_code": "INV-CORP-AA",
        "category_name": "Corporate Bonds - AA Rated",
        "description": "AA and AA+ rated corporate bonds",
        "investment_type": "DEBT",
        "risk_category": "MEDIUM",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "MARK_TO_MARKET",
        "is_active": True,
    },
    {
        "category_code": "INV-CORP-A",
        "category_name": "Corporate Bonds - A Rated",
        "description": "A and A+ rated corporate bonds",
        "investment_type": "DEBT",
        "risk_category": "MEDIUM",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "MARK_TO_MARKET",
        "is_active": True,
    },
    # Bank Deposits
    {
        "category_code": "INV-FD-SCH",
        "category_name": "Fixed Deposits - Scheduled Banks",
        "description": "Term deposits with scheduled commercial banks",
        "investment_type": "DEPOSIT",
        "risk_category": "LOW",
        "slr_eligible": False,
        "npa_classification_days": None,
        "valuation_method": "COST",
        "is_active": True,
    },
    {
        "category_code": "INV-FD-COOP",
        "category_name": "Fixed Deposits - Cooperative Banks",
        "description": "Term deposits with cooperative banks",
        "investment_type": "DEPOSIT",
        "risk_category": "MEDIUM",
        "slr_eligible": False,
        "npa_classification_days": None,
        "valuation_method": "COST",
        "is_active": True,
    },
    # Mutual Funds
    {
        "category_code": "INV-MF-DEBT",
        "category_name": "Debt Mutual Funds",
        "description": "Liquid, ultra-short, and debt mutual funds",
        "investment_type": "MUTUAL_FUND",
        "risk_category": "LOW",
        "slr_eligible": False,
        "npa_classification_days": None,
        "valuation_method": "NAV",
        "is_active": True,
    },
    {
        "category_code": "INV-MF-HYBRID",
        "category_name": "Hybrid Mutual Funds",
        "description": "Balanced and hybrid mutual funds",
        "investment_type": "MUTUAL_FUND",
        "risk_category": "MEDIUM",
        "slr_eligible": False,
        "npa_classification_days": None,
        "valuation_method": "NAV",
        "is_active": True,
    },
    # Commercial Paper
    {
        "category_code": "INV-CP",
        "category_name": "Commercial Paper",
        "description": "Commercial paper from rated corporates",
        "investment_type": "DEBT",
        "risk_category": "MEDIUM",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "AMORTIZED_COST",
        "is_active": True,
    },
    # Certificate of Deposit
    {
        "category_code": "INV-CD",
        "category_name": "Certificate of Deposit",
        "description": "CDs issued by scheduled banks",
        "investment_type": "DEPOSIT",
        "risk_category": "LOW",
        "slr_eligible": False,
        "npa_classification_days": None,
        "valuation_method": "AMORTIZED_COST",
        "is_active": True,
    },
    # NBFC Bonds
    {
        "category_code": "INV-NBFC-AAA",
        "category_name": "NBFC Bonds - AAA Rated",
        "description": "AAA rated NBFC bonds and NCDs",
        "investment_type": "DEBT",
        "risk_category": "LOW",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "MARK_TO_MARKET",
        "is_active": True,
    },
    {
        "category_code": "INV-NBFC-AA",
        "category_name": "NBFC Bonds - AA Rated",
        "description": "AA rated NBFC bonds and NCDs",
        "investment_type": "DEBT",
        "risk_category": "MEDIUM",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "MARK_TO_MARKET",
        "is_active": True,
    },
    # Subordinate Debt
    {
        "category_code": "INV-SUB-DEBT",
        "category_name": "Subordinate Debt",
        "description": "Tier-2 capital eligible subordinate debt",
        "investment_type": "DEBT",
        "risk_category": "HIGH",
        "slr_eligible": False,
        "npa_classification_days": 90,
        "valuation_method": "COST",
        "is_active": True,
    },
]


# =============================================================================
# COUNTERPARTIES DATA
# =============================================================================

COUNTERPARTIES = [
    # Banks
    {
        "counterparty_code": "CP-SBI",
        "counterparty_name": "State Bank of India",
        "counterparty_type": "BANK",
        "credit_rating": "AAA",
        "rating_agency": "CRISIL",
        "exposure_limit": Decimal("50000000000.00"),  # 5000 Cr
        "is_active": True,
    },
    {
        "counterparty_code": "CP-HDFC",
        "counterparty_name": "HDFC Bank Limited",
        "counterparty_type": "BANK",
        "credit_rating": "AAA",
        "rating_agency": "CRISIL",
        "exposure_limit": Decimal("50000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-ICICI",
        "counterparty_name": "ICICI Bank Limited",
        "counterparty_type": "BANK",
        "credit_rating": "AAA",
        "rating_agency": "ICRA",
        "exposure_limit": Decimal("40000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-AXIS",
        "counterparty_name": "Axis Bank Limited",
        "counterparty_type": "BANK",
        "credit_rating": "AAA",
        "rating_agency": "CRISIL",
        "exposure_limit": Decimal("30000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-KOTAK",
        "counterparty_name": "Kotak Mahindra Bank",
        "counterparty_type": "BANK",
        "credit_rating": "AAA",
        "rating_agency": "ICRA",
        "exposure_limit": Decimal("25000000000.00"),
        "is_active": True,
    },
    # Mutual Funds
    {
        "counterparty_code": "CP-HDFCMF",
        "counterparty_name": "HDFC Asset Management",
        "counterparty_type": "MUTUAL_FUND",
        "credit_rating": None,
        "rating_agency": None,
        "exposure_limit": Decimal("10000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-ICICIMF",
        "counterparty_name": "ICICI Prudential AMC",
        "counterparty_type": "MUTUAL_FUND",
        "credit_rating": None,
        "rating_agency": None,
        "exposure_limit": Decimal("10000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-SBIMF",
        "counterparty_name": "SBI Mutual Fund",
        "counterparty_type": "MUTUAL_FUND",
        "credit_rating": None,
        "rating_agency": None,
        "exposure_limit": Decimal("10000000000.00"),
        "is_active": True,
    },
    # Corporates
    {
        "counterparty_code": "CP-RELIND",
        "counterparty_name": "Reliance Industries Limited",
        "counterparty_type": "CORPORATE",
        "credit_rating": "AAA",
        "rating_agency": "CRISIL",
        "exposure_limit": Decimal("5000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-TATA",
        "counterparty_name": "Tata Sons Private Limited",
        "counterparty_type": "CORPORATE",
        "credit_rating": "AAA",
        "rating_agency": "CRISIL",
        "exposure_limit": Decimal("5000000000.00"),
        "is_active": True,
    },
    # NBFCs
    {
        "counterparty_code": "CP-BAJFIN",
        "counterparty_name": "Bajaj Finance Limited",
        "counterparty_type": "NBFC",
        "credit_rating": "AAA",
        "rating_agency": "CRISIL",
        "exposure_limit": Decimal("3000000000.00"),
        "is_active": True,
    },
    {
        "counterparty_code": "CP-MAHFIN",
        "counterparty_name": "Mahindra & Mahindra Financial Services",
        "counterparty_type": "NBFC",
        "credit_rating": "AAA",
        "rating_agency": "ICRA",
        "exposure_limit": Decimal("2000000000.00"),
        "is_active": True,
    },
]


# =============================================================================
# ALM BUCKETS DATA
# =============================================================================

ALM_BUCKETS = [
    {"bucket_code": "ALM-1D", "bucket_name": "1 Day", "min_days": 0, "max_days": 1, "display_order": 1},
    {"bucket_code": "ALM-2-7D", "bucket_name": "2-7 Days", "min_days": 2, "max_days": 7, "display_order": 2},
    {"bucket_code": "ALM-8-14D", "bucket_name": "8-14 Days", "min_days": 8, "max_days": 14, "display_order": 3},
    {"bucket_code": "ALM-15-30D", "bucket_name": "15-30 Days", "min_days": 15, "max_days": 30, "display_order": 4},
    {"bucket_code": "ALM-31-60D", "bucket_name": "31-60 Days", "min_days": 31, "max_days": 60, "display_order": 5},
    {"bucket_code": "ALM-61-90D", "bucket_name": "61-90 Days", "min_days": 61, "max_days": 90, "display_order": 6},
    {"bucket_code": "ALM-91-180D", "bucket_name": "91-180 Days", "min_days": 91, "max_days": 180, "display_order": 7},
    {"bucket_code": "ALM-181-365D", "bucket_name": "181-365 Days", "min_days": 181, "max_days": 365, "display_order": 8},
    {"bucket_code": "ALM-1-3Y", "bucket_name": "1-3 Years", "min_days": 366, "max_days": 1095, "display_order": 9},
    {"bucket_code": "ALM-3-5Y", "bucket_name": "3-5 Years", "min_days": 1096, "max_days": 1825, "display_order": 10},
    {"bucket_code": "ALM-5Y+", "bucket_name": "Over 5 Years", "min_days": 1826, "max_days": 99999, "display_order": 11},
]


# =============================================================================
# RISK LIMITS DATA
# =============================================================================

RISK_LIMITS = [
    # Interest Rate Risk
    {
        "limit_code": "RISK-IRR-DUR",
        "limit_name": "Duration Gap Limit",
        "risk_type": "INTEREST_RATE",
        "limit_value": Decimal("2.00"),
        "limit_unit": "YEARS",
        "warning_threshold": Decimal("80.00"),
        "is_active": True,
    },
    {
        "limit_code": "RISK-IRR-NII",
        "limit_name": "NII at Risk Limit",
        "risk_type": "INTEREST_RATE",
        "limit_value": Decimal("5.00"),
        "limit_unit": "PERCENTAGE",
        "warning_threshold": Decimal("80.00"),
        "is_active": True,
    },
    # Liquidity Risk
    {
        "limit_code": "RISK-LIQ-LCR",
        "limit_name": "Liquidity Coverage Ratio",
        "risk_type": "LIQUIDITY",
        "limit_value": Decimal("100.00"),
        "limit_unit": "PERCENTAGE",
        "warning_threshold": Decimal("110.00"),
        "is_active": True,
    },
    {
        "limit_code": "RISK-LIQ-GAP",
        "limit_name": "Cumulative Gap Limit (30 days)",
        "risk_type": "LIQUIDITY",
        "limit_value": Decimal("-15.00"),
        "limit_unit": "PERCENTAGE",
        "warning_threshold": Decimal("-10.00"),
        "is_active": True,
    },
    # Counterparty Risk
    {
        "limit_code": "RISK-CP-SINGLE",
        "limit_name": "Single Counterparty Exposure",
        "risk_type": "COUNTERPARTY",
        "limit_value": Decimal("15.00"),
        "limit_unit": "PERCENTAGE_NETWORTH",
        "warning_threshold": Decimal("80.00"),
        "is_active": True,
    },
    {
        "limit_code": "RISK-CP-GROUP",
        "limit_name": "Group Counterparty Exposure",
        "risk_type": "COUNTERPARTY",
        "limit_value": Decimal("25.00"),
        "limit_unit": "PERCENTAGE_NETWORTH",
        "warning_threshold": Decimal("80.00"),
        "is_active": True,
    },
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("Treasury Module Direct Seed Script")
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

            # Seed Investment Categories
            print("\n--- Seeding Investment Categories ---")
            count = 0
            for cat_data in INVESTMENT_CATEGORIES:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_investment_category WHERE organization_id = :org_id AND category_code = :code"),
                    {"org_id": org_id, "code": cat_data["category_code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {cat_data['category_code']}")
                    continue

                # Insert investment category
                await session.execute(
                    text("""
                        INSERT INTO mst_investment_category (
                            organization_id, category_code, category_name, description,
                            investment_type, risk_category, slr_eligible,
                            npa_classification_days, valuation_method, is_active, created_by_id
                        ) VALUES (
                            :org_id, :category_code, :category_name, :description,
                            :investment_type, :risk_category, :slr_eligible,
                            :npa_classification_days, :valuation_method, :is_active, :user_id
                        )
                    """),
                    {
                        "org_id": org_id,
                        "category_code": cat_data["category_code"],
                        "category_name": cat_data["category_name"],
                        "description": cat_data["description"],
                        "investment_type": cat_data["investment_type"],
                        "risk_category": cat_data["risk_category"],
                        "slr_eligible": cat_data["slr_eligible"],
                        "npa_classification_days": cat_data["npa_classification_days"],
                        "valuation_method": cat_data["valuation_method"],
                        "is_active": cat_data["is_active"],
                        "user_id": user_id,
                    }
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} investment categories")

            print("\n" + "=" * 60)
            print("✓ Treasury Module seed data created successfully!")
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
