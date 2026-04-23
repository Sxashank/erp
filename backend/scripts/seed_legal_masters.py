"""
Seed script for Legal Module master data.
Works with the existing database schema.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_legal_masters.py
"""

import asyncio
from datetime import date
from uuid import uuid4
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp"
)


# =============================================================================
# STATUTORY PERIODS DATA
# =============================================================================

STATUTORY_PERIODS = [
    {"code": "SARFAESI_13_2", "name": "Section 13(2) Demand Notice Response Period", "act_name": "SARFAESI Act 2002", "section": "Section 13(2)", "period_days": 60, "period_type": "CALENDAR", "trigger_event": "Date of receipt of demand notice by borrower", "consequence": "Lender can proceed with possession under Section 13(4)", "alert_days_before": 7},
    {"code": "SARFAESI_13_3A", "name": "Section 13(3A) Objection Response Period", "act_name": "SARFAESI Act 2002", "section": "Section 13(3A)", "period_days": 15, "period_type": "CALENDAR", "trigger_event": "Date of receipt of objection by secured creditor", "consequence": "If no response, objection deemed rejected", "alert_days_before": 3},
    {"code": "SARFAESI_13_4", "name": "Section 13(4) Possession Notice Period", "act_name": "SARFAESI Act 2002", "section": "Section 13(4)", "period_days": 15, "period_type": "CALENDAR", "trigger_event": "Date of affixing possession notice", "consequence": "Secured creditor can take physical possession", "alert_days_before": 3},
    {"code": "SARFAESI_AUCTION", "name": "Auction Notice Publication Period", "act_name": "SARFAESI Act 2002", "section": "Rule 8(6) & 9(1)", "period_days": 30, "period_type": "CALENDAR", "trigger_event": "Date of publication of sale notice", "consequence": "Sale can be conducted after 30 days", "alert_days_before": 7},
    {"code": "SARFAESI_17", "name": "Section 17 Appeal to DRT", "act_name": "SARFAESI Act 2002", "section": "Section 17", "period_days": 45, "period_type": "CALENDAR", "trigger_event": "Date of measure taken by secured creditor", "consequence": "Right to challenge SARFAESI action may be lost", "alert_days_before": 15},
    {"code": "NI_138_NOTICE", "name": "Section 138 Cheque Bounce Notice Period", "act_name": "Negotiable Instruments Act 1881", "section": "Section 138(b)", "period_days": 15, "period_type": "CALENDAR", "trigger_event": "Date of receipt of dishonour notice", "consequence": "Drawer gets 15 days to make payment", "alert_days_before": 3},
    {"code": "NI_138_COMPLAINT", "name": "Section 138 Complaint Filing Period", "act_name": "Negotiable Instruments Act 1881", "section": "Section 142", "period_days": 30, "period_type": "CALENDAR", "trigger_event": "Expiry of 15 days notice period", "consequence": "Right to file criminal complaint may be lost", "alert_days_before": 7},
    {"code": "DRT_APPLICATION", "name": "DRT Application Filing Limitation", "act_name": "DRT Act 1993", "section": "Section 24", "period_days": 1095, "period_type": "CALENDAR", "trigger_event": "Date of cause of action (NPA date)", "consequence": "Application may be barred by limitation", "alert_days_before": 90},
    {"code": "DRAT_APPEAL", "name": "DRAT Appeal Period", "act_name": "DRT Act 1993", "section": "Section 20", "period_days": 45, "period_type": "CALENDAR", "trigger_event": "Date of DRT order", "consequence": "Right of appeal may be lost", "alert_days_before": 15},
    {"code": "RC_EXECUTION", "name": "Recovery Certificate Execution", "act_name": "Limitation Act 1963", "section": "Article 136", "period_days": 4380, "period_type": "CALENDAR", "trigger_event": "Date of Recovery Certificate", "consequence": "Recovery Certificate becomes time-barred", "alert_days_before": 180},
    {"code": "IBC_SECTION_7", "name": "IBC Application Filing (Section 7)", "act_name": "IBC 2016", "section": "Section 7", "period_days": 1095, "period_type": "CALENDAR", "trigger_event": "Date of default", "consequence": "Application may be time-barred", "alert_days_before": 90},
    {"code": "NCLAT_APPEAL", "name": "NCLAT Appeal Period", "act_name": "IBC 2016", "section": "Section 61", "period_days": 30, "period_type": "CALENDAR", "trigger_event": "Date of NCLT order", "consequence": "Right of appeal may be lost", "alert_days_before": 7},
    {"code": "CERSAI_REG", "name": "CERSAI Registration Timeline", "act_name": "SARFAESI Act 2002", "section": "Section 23", "period_days": 30, "period_type": "CALENDAR", "trigger_event": "Date of creation of security interest", "consequence": "Late fee penalty; loses priority", "alert_days_before": 7},
]


# =============================================================================
# NOTICE TEMPLATES DATA
# =============================================================================

NOTICE_TEMPLATES = [
    {"code": "SARFAESI_13_2", "name": "Section 13(2) Demand Notice - SARFAESI", "notice_type": "SARFAESI_13_2", "template_body": "<html><body><h1>SARFAESI Section 13(2) Demand Notice</h1></body></html>", "statutory_period_days": 60, "act_reference": "SARFAESI Act 2002, Section 13(2)", "section_reference": "Section 13(2)", "language": "en"},
    {"code": "SARFAESI_13_4", "name": "Section 13(4) Possession Notice", "notice_type": "SARFAESI_13_4_POSSESSION", "template_body": "<html><body><h1>SARFAESI Possession Notice</h1></body></html>", "statutory_period_days": 15, "act_reference": "SARFAESI Act 2002, Section 13(4)", "section_reference": "Section 13(4)", "language": "en"},
    {"code": "SARFAESI_AUCTION", "name": "Auction/Sale Notice under SARFAESI", "notice_type": "SARFAESI_AUCTION", "template_body": "<html><body><h1>E-Auction Sale Notice</h1></body></html>", "statutory_period_days": 30, "act_reference": "SARFAESI Act 2002, Rule 8(6) and Rule 9", "section_reference": "Rule 8(6) & 9", "language": "en"},
    {"code": "NI_ACT_138", "name": "Section 138 Cheque Bounce Notice", "notice_type": "NI_ACT_138", "template_body": "<html><body><h1>Legal Notice under Section 138 NI Act</h1></body></html>", "statutory_period_days": 15, "act_reference": "Negotiable Instruments Act 1881, Section 138", "section_reference": "Section 138", "language": "en"},
    {"code": "LOAN_RECALL", "name": "Loan Recall Notice", "notice_type": "RECALL_NOTICE", "template_body": "<html><body><h1>Loan Recall Notice</h1></body></html>", "statutory_period_days": 15, "act_reference": "Loan Agreement Terms", "section_reference": "As per Agreement", "language": "en"},
    {"code": "FINAL_DEMAND", "name": "Final Demand Notice Before Legal Action", "notice_type": "FINAL_DEMAND", "template_body": "<html><body><h1>Final Demand Notice</h1></body></html>", "statutory_period_days": 7, "act_reference": "General", "section_reference": "N/A", "language": "en"},
]


# =============================================================================
# COURTS DATA (matching existing schema)
# =============================================================================

COURTS = [
    # DRT
    {"code": "DRT-DEL-1", "name": "Debt Recovery Tribunal-I, New Delhi", "court_type": "DRT", "jurisdiction": "Delhi NCR", "city": "New Delhi", "state_code": "DL", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-DEL-2", "name": "Debt Recovery Tribunal-II, New Delhi", "court_type": "DRT", "jurisdiction": "Delhi NCR", "city": "New Delhi", "state_code": "DL", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-MUM-1", "name": "Debt Recovery Tribunal-I, Mumbai", "court_type": "DRT", "jurisdiction": "Mumbai Metropolitan", "city": "Mumbai", "state_code": "MH", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-MUM-2", "name": "Debt Recovery Tribunal-II, Mumbai", "court_type": "DRT", "jurisdiction": "Mumbai Metropolitan", "city": "Mumbai", "state_code": "MH", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-CHN-1", "name": "Debt Recovery Tribunal-I, Chennai", "court_type": "DRT", "jurisdiction": "Tamil Nadu North", "city": "Chennai", "state_code": "TN", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-KOL-1", "name": "Debt Recovery Tribunal-I, Kolkata", "court_type": "DRT", "jurisdiction": "West Bengal", "city": "Kolkata", "state_code": "WB", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-BLR-1", "name": "Debt Recovery Tribunal-I, Bengaluru", "court_type": "DRT", "jurisdiction": "Karnataka", "city": "Bengaluru", "state_code": "KA", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-HYD-1", "name": "Debt Recovery Tribunal-I, Hyderabad", "court_type": "DRT", "jurisdiction": "Telangana, AP", "city": "Hyderabad", "state_code": "TS", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-AMD-1", "name": "Debt Recovery Tribunal-I, Ahmedabad", "court_type": "DRT", "jurisdiction": "Gujarat", "city": "Ahmedabad", "state_code": "GJ", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRT-PUN", "name": "Debt Recovery Tribunal, Pune", "court_type": "DRT", "jurisdiction": "Western Maharashtra", "city": "Pune", "state_code": "MH", "filing_portal_url": "https://drt.gov.in"},
    # DRAT
    {"code": "DRAT-DEL", "name": "Debt Recovery Appellate Tribunal, Delhi", "court_type": "DRAT", "jurisdiction": "North India DRTs", "city": "New Delhi", "state_code": "DL", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRAT-MUM", "name": "Debt Recovery Appellate Tribunal, Mumbai", "court_type": "DRAT", "jurisdiction": "West India DRTs", "city": "Mumbai", "state_code": "MH", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRAT-CHN", "name": "Debt Recovery Appellate Tribunal, Chennai", "court_type": "DRAT", "jurisdiction": "South India DRTs", "city": "Chennai", "state_code": "TN", "filing_portal_url": "https://drt.gov.in"},
    {"code": "DRAT-KOL", "name": "Debt Recovery Appellate Tribunal, Kolkata", "court_type": "DRAT", "jurisdiction": "East India DRTs", "city": "Kolkata", "state_code": "WB", "filing_portal_url": "https://drt.gov.in"},
    # NCLT
    {"code": "NCLT-DEL-PB", "name": "NCLT Principal Bench, New Delhi", "court_type": "NCLT", "jurisdiction": "All India Principal", "city": "New Delhi", "state_code": "DL", "filing_portal_url": "https://nclt.gov.in"},
    {"code": "NCLT-MUM", "name": "NCLT Mumbai Bench", "court_type": "NCLT", "jurisdiction": "Maharashtra", "city": "Mumbai", "state_code": "MH", "filing_portal_url": "https://nclt.gov.in"},
    {"code": "NCLT-CHN", "name": "NCLT Chennai Bench", "court_type": "NCLT", "jurisdiction": "Tamil Nadu", "city": "Chennai", "state_code": "TN", "filing_portal_url": "https://nclt.gov.in"},
    {"code": "NCLT-KOL", "name": "NCLT Kolkata Bench", "court_type": "NCLT", "jurisdiction": "West Bengal", "city": "Kolkata", "state_code": "WB", "filing_portal_url": "https://nclt.gov.in"},
    {"code": "NCLT-BLR", "name": "NCLT Bengaluru Bench", "court_type": "NCLT", "jurisdiction": "Karnataka", "city": "Bengaluru", "state_code": "KA", "filing_portal_url": "https://nclt.gov.in"},
    {"code": "NCLT-HYD", "name": "NCLT Hyderabad Bench", "court_type": "NCLT", "jurisdiction": "Telangana, AP", "city": "Hyderabad", "state_code": "TS", "filing_portal_url": "https://nclt.gov.in"},
    # NCLAT
    {"code": "NCLAT-DEL", "name": "NCLAT, New Delhi", "court_type": "NCLAT", "jurisdiction": "All India", "city": "New Delhi", "state_code": "DL", "filing_portal_url": "https://nclat.nic.in"},
]


# =============================================================================
# COURT FEE SLABS DATA
# =============================================================================

# DRT Court Fee Slabs (as per DRT Rules)
# Fee is typically 1% of claim amount subject to min/max caps
COURT_FEE_SLABS = [
    # DRT Fee Structure (Application under Section 19 of DRT Act)
    {"court_type": "DRT", "case_type": "OA", "claim_min": 0, "claim_max": 1000000, "fee_type": "FIXED", "fee_value": 12000},
    {"court_type": "DRT", "case_type": "OA", "claim_min": 1000001, "claim_max": 2000000, "fee_type": "FIXED", "fee_value": 20000},
    {"court_type": "DRT", "case_type": "OA", "claim_min": 2000001, "claim_max": 5000000, "fee_type": "FIXED", "fee_value": 30000},
    {"court_type": "DRT", "case_type": "OA", "claim_min": 5000001, "claim_max": 10000000, "fee_type": "FIXED", "fee_value": 40000},
    {"court_type": "DRT", "case_type": "OA", "claim_min": 10000001, "claim_max": 50000000, "fee_type": "FIXED", "fee_value": 75000},
    {"court_type": "DRT", "case_type": "OA", "claim_min": 50000001, "claim_max": None, "fee_type": "FIXED", "fee_value": 150000},
    # DRT SA (Section 17 SARFAESI Appeal)
    {"court_type": "DRT", "case_type": "SA", "claim_min": 0, "claim_max": 1000000, "fee_type": "FIXED", "fee_value": 6000},
    {"court_type": "DRT", "case_type": "SA", "claim_min": 1000001, "claim_max": 5000000, "fee_type": "FIXED", "fee_value": 12000},
    {"court_type": "DRT", "case_type": "SA", "claim_min": 5000001, "claim_max": 10000000, "fee_type": "FIXED", "fee_value": 20000},
    {"court_type": "DRT", "case_type": "SA", "claim_min": 10000001, "claim_max": None, "fee_type": "FIXED", "fee_value": 30000},
    # DRAT Appeal Fee
    {"court_type": "DRAT", "case_type": "APPEAL", "claim_min": 0, "claim_max": 1000000, "fee_type": "FIXED", "fee_value": 20000},
    {"court_type": "DRAT", "case_type": "APPEAL", "claim_min": 1000001, "claim_max": 5000000, "fee_type": "FIXED", "fee_value": 30000},
    {"court_type": "DRAT", "case_type": "APPEAL", "claim_min": 5000001, "claim_max": 10000000, "fee_type": "FIXED", "fee_value": 50000},
    {"court_type": "DRAT", "case_type": "APPEAL", "claim_min": 10000001, "claim_max": None, "fee_type": "FIXED", "fee_value": 75000},
    # NCLT IBC Application Fee
    {"court_type": "NCLT", "case_type": "CP_IBC_7", "claim_min": 0, "claim_max": 10000000, "fee_type": "FIXED", "fee_value": 25000},
    {"court_type": "NCLT", "case_type": "CP_IBC_7", "claim_min": 10000001, "claim_max": 100000000, "fee_type": "FIXED", "fee_value": 50000},
    {"court_type": "NCLT", "case_type": "CP_IBC_7", "claim_min": 100000001, "claim_max": None, "fee_type": "FIXED", "fee_value": 100000},
    # NCLAT Appeal Fee
    {"court_type": "NCLAT", "case_type": "APPEAL", "claim_min": 0, "claim_max": 10000000, "fee_type": "FIXED", "fee_value": 50000},
    {"court_type": "NCLAT", "case_type": "APPEAL", "claim_min": 10000001, "claim_max": None, "fee_type": "FIXED", "fee_value": 100000},
]


# =============================================================================
# EXPENSE CATEGORIES DATA (matching existing schema)
# =============================================================================

EXPENSE_CATEGORIES = [
    {"code": "COURT_FEE", "name": "Court Filing Fee", "category_type": "COURT_FEE", "is_recoverable": True, "requires_approval": True, "approval_limit": 50000},
    {"code": "FILING_FEE", "name": "Document Filing Fee", "category_type": "FILING_FEE", "is_recoverable": True, "requires_approval": True, "approval_limit": 10000},
    {"code": "PROCESS_FEE", "name": "Process Fee", "category_type": "PROCESS_FEE", "is_recoverable": True, "requires_approval": True, "approval_limit": 5000},
    {"code": "EXECUTION_FEE", "name": "Execution Fee", "category_type": "EXECUTION_FEE", "is_recoverable": True, "requires_approval": True, "approval_limit": 50000},
    {"code": "ADV_RETAINER", "name": "Advocate Retainer Fee", "category_type": "ADVOCATE_RETAINER", "is_recoverable": True, "requires_approval": True, "approval_limit": 100000},
    {"code": "ADV_APPEARANCE", "name": "Advocate Appearance Fee", "category_type": "ADVOCATE_APPEARANCE", "is_recoverable": True, "requires_approval": True, "approval_limit": 25000},
    {"code": "VALUATION", "name": "Valuation Charges", "category_type": "VALUATION_CHARGES", "is_recoverable": True, "requires_approval": True, "approval_limit": 50000},
    {"code": "PUBLICATION", "name": "Newspaper Publication Charges", "category_type": "PUBLICATION_CHARGES", "is_recoverable": True, "requires_approval": True, "approval_limit": 25000},
    {"code": "STAMP_DUTY", "name": "Stamp Duty", "category_type": "STAMP_DUTY", "is_recoverable": True, "requires_approval": True, "approval_limit": 10000},
    {"code": "COURIER", "name": "Courier & Postage", "category_type": "COURIER_POSTAGE", "is_recoverable": True, "requires_approval": False, "approval_limit": 2000},
    {"code": "CERSAI", "name": "CERSAI Charges", "category_type": "CERSAI_CHARGES", "is_recoverable": True, "requires_approval": True, "approval_limit": 5000},
    {"code": "MISC", "name": "Miscellaneous Expenses", "category_type": "MISCELLANEOUS", "is_recoverable": True, "requires_approval": True, "approval_limit": 10000},
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("Legal Module Seed Data Script")
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
            org_id = str(org_row[0])
            print(f"✓ Using organization: {org_id}")

            # Seed Statutory Periods
            print("\n--- Seeding Statutory Periods ---")
            count = 0
            for p in STATUTORY_PERIODS:
                result = await session.execute(
                    text("SELECT id FROM mst_statutory_period WHERE organization_id = :org_id AND code = :code"),
                    {"org_id": org_id, "code": p["code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {p['code']}")
                    continue

                await session.execute(
                    text("""
                        INSERT INTO mst_statutory_period
                        (id, organization_id, code, name, act_name, section, period_days,
                         period_type, trigger_event, consequence, alert_days_before, is_active, created_at)
                        VALUES (:id, :org_id, :code, :name, :act_name, :section, :period_days,
                                :period_type, :trigger_event, :consequence, :alert_days_before, true, NOW())
                    """),
                    {"id": str(uuid4()), "org_id": org_id, **p}
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} statutory periods")

            # Seed Notice Templates
            print("\n--- Seeding Notice Templates ---")
            count = 0
            for t in NOTICE_TEMPLATES:
                result = await session.execute(
                    text("SELECT id FROM mst_notice_template WHERE organization_id = :org_id AND code = :code"),
                    {"org_id": org_id, "code": t["code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {t['code']}")
                    continue

                await session.execute(
                    text("""
                        INSERT INTO mst_notice_template
                        (id, organization_id, code, name, notice_type, template_body,
                         statutory_period_days, act_reference, section_reference, language,
                         is_active, version, created_at)
                        VALUES (:id, :org_id, :code, :name, :notice_type, :template_body,
                                :statutory_period_days, :act_reference, :section_reference, :language,
                                true, 1, NOW())
                    """),
                    {"id": str(uuid4()), "org_id": org_id, **t}
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} notice templates")

            # Seed Courts
            print("\n--- Seeding Courts ---")
            count = 0
            for c in COURTS:
                result = await session.execute(
                    text("SELECT id FROM mst_court WHERE organization_id = :org_id AND code = :code"),
                    {"org_id": org_id, "code": c["code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {c['code']}")
                    continue

                await session.execute(
                    text("""
                        INSERT INTO mst_court
                        (id, organization_id, code, name, court_type, jurisdiction,
                         city, state_code, country, filing_portal_url, is_active, version, created_at)
                        VALUES (:id, :org_id, :code, :name, :court_type, :jurisdiction,
                                :city, :state_code, 'India', :filing_portal_url, true, 1, NOW())
                    """),
                    {"id": str(uuid4()), "org_id": org_id, **c}
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} courts")

            # Seed Expense Categories
            print("\n--- Seeding Expense Categories ---")
            count = 0
            for e in EXPENSE_CATEGORIES:
                result = await session.execute(
                    text("SELECT id FROM mst_expense_category WHERE organization_id = :org_id AND code = :code"),
                    {"org_id": org_id, "code": e["code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {e['code']}")
                    continue

                await session.execute(
                    text("""
                        INSERT INTO mst_expense_category
                        (id, organization_id, code, name, category_type,
                         is_recoverable, requires_approval, approval_limit, is_active, created_at)
                        VALUES (:id, :org_id, :code, :name, :category_type,
                                :is_recoverable, :requires_approval, :approval_limit, true, NOW())
                    """),
                    {"id": str(uuid4()), "org_id": org_id, **e}
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} expense categories")

            # Seed Court Fee Slabs
            print("\n--- Seeding Court Fee Slabs ---")
            count = 0

            # Get court IDs by type for mapping
            court_map = {}
            result = await session.execute(
                text("SELECT id, code, court_type FROM mst_court WHERE organization_id = :org_id"),
                {"org_id": org_id}
            )
            for row in result.fetchall():
                court_type = row[2]
                if court_type not in court_map:
                    court_map[court_type] = str(row[0])  # Use first court of each type

            from datetime import date
            for slab in COURT_FEE_SLABS:
                court_id = court_map.get(slab["court_type"])
                if not court_id:
                    print(f"  - Skipped (no court): {slab['court_type']} {slab['case_type']}")
                    continue

                # Check if slab already exists
                result = await session.execute(
                    text("""
                        SELECT id FROM mst_court_fee_slab
                        WHERE court_id = :court_id AND case_type = :case_type
                        AND claim_min = :claim_min
                    """),
                    {"court_id": court_id, "case_type": slab["case_type"], "claim_min": slab["claim_min"]}
                )
                if result.fetchone():
                    continue

                await session.execute(
                    text("""
                        INSERT INTO mst_court_fee_slab
                        (id, court_id, case_type, claim_min, claim_max, fee_type, fee_value,
                         effective_from, is_active, created_at)
                        VALUES (:id, :court_id, :case_type, :claim_min, :claim_max, :fee_type, :fee_value,
                                :effective_from, true, NOW())
                    """),
                    {
                        "id": str(uuid4()),
                        "court_id": court_id,
                        "case_type": slab["case_type"],
                        "claim_min": slab["claim_min"],
                        "claim_max": slab["claim_max"],
                        "fee_type": slab["fee_type"],
                        "fee_value": slab["fee_value"],
                        "effective_from": date(2024, 1, 1)
                    }
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} court fee slabs")

            print("\n" + "=" * 60)
            print("✓ Legal Module seed data created successfully!")
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
