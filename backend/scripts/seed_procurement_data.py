"""
Direct database seed script for Procurement Module master data.
Inserts data directly into the database without requiring API authentication.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_procurement_data.py
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
# VENDOR CATEGORIES DATA
# =============================================================================

VENDOR_CATEGORIES = [
    {
        "category_code": "VND-IT",
        "category_name": "IT & Technology",
        "description": "Hardware, software, and IT services vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-OFF",
        "category_name": "Office Supplies",
        "description": "Stationery, furniture, and office equipment vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-PRINT",
        "category_name": "Printing & Packaging",
        "description": "Printing services and packaging material vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-MAINT",
        "category_name": "Maintenance & AMC",
        "description": "Annual maintenance and repair service vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-SEC",
        "category_name": "Security Services",
        "description": "Security personnel and surveillance vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-HOUSE",
        "category_name": "Housekeeping",
        "description": "Housekeeping and cleaning service vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-PROF",
        "category_name": "Professional Services",
        "description": "Legal, audit, and consulting service vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-TRAVEL",
        "category_name": "Travel & Transport",
        "description": "Travel agents, cab services, and courier vendors",
        "is_active": True,
    },
    {
        "category_code": "VND-UTIL",
        "category_name": "Utilities",
        "description": "Power, telecom, and utility service providers",
        "is_active": True,
    },
    {
        "category_code": "VND-MKTG",
        "category_name": "Marketing & Advertising",
        "description": "Advertising agencies and marketing vendors",
        "is_active": True,
    },
]


# =============================================================================
# VENDORS DATA
# =============================================================================

VENDORS = [
    # IT Vendors
    {
        "vendor_code": "VND-001",
        "vendor_name": "TechPro Solutions Pvt Ltd",
        "category_code": "VND-IT",
        "contact_person": "Rajesh Sharma",
        "email": "rajesh@techpro.com",
        "phone": "9876543210",
        "address": "Unit 501, Tech Park, Andheri East",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400093",
        "gstin": "27AABCT1234A1Z5",
        "pan": "AABCT1234A",
        "payment_terms_days": 30,
        "credit_limit": Decimal("1000000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    {
        "vendor_code": "VND-002",
        "vendor_name": "Digital Systems India",
        "category_code": "VND-IT",
        "contact_person": "Amit Kumar",
        "email": "amit@digitalsystems.in",
        "phone": "9876543211",
        "address": "Tower B, Cyber City",
        "city": "Gurugram",
        "state": "Haryana",
        "pincode": "122002",
        "gstin": "06AABCD5678B1Z3",
        "pan": "AABCD5678B",
        "payment_terms_days": 45,
        "credit_limit": Decimal("2000000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Office Supplies Vendors
    {
        "vendor_code": "VND-003",
        "vendor_name": "Supreme Stationery Mart",
        "category_code": "VND-OFF",
        "contact_person": "Vikram Patel",
        "email": "vikram@supremestation.com",
        "phone": "9876543212",
        "address": "Shop 12, Commercial Complex",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "gstin": "27AABCS9012C1Z1",
        "pan": "AABCS9012C",
        "payment_terms_days": 15,
        "credit_limit": Decimal("500000.00"),
        "vendor_rating": "B",
        "is_active": True,
    },
    {
        "vendor_code": "VND-004",
        "vendor_name": "Office World Enterprises",
        "category_code": "VND-OFF",
        "contact_person": "Priya Singh",
        "email": "priya@officeworld.in",
        "phone": "9876543213",
        "address": "Sector 18, Industrial Area",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "pincode": "201301",
        "gstin": "09AABCO3456D1Z9",
        "pan": "AABCO3456D",
        "payment_terms_days": 30,
        "credit_limit": Decimal("750000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Printing Vendors
    {
        "vendor_code": "VND-005",
        "vendor_name": "PrintMax Graphics",
        "category_code": "VND-PRINT",
        "contact_person": "Suresh Menon",
        "email": "suresh@printmax.com",
        "phone": "9876543214",
        "address": "Plot 25, MIDC Industrial Estate",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400076",
        "gstin": "27AABCP7890E1Z7",
        "pan": "AABCP7890E",
        "payment_terms_days": 21,
        "credit_limit": Decimal("300000.00"),
        "vendor_rating": "B",
        "is_active": True,
    },
    # Maintenance Vendors
    {
        "vendor_code": "VND-006",
        "vendor_name": "AllCare Services Pvt Ltd",
        "category_code": "VND-MAINT",
        "contact_person": "Kiran Reddy",
        "email": "kiran@allcare.in",
        "phone": "9876543215",
        "address": "Building 5, Bandra Complex",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400050",
        "gstin": "27AABCA1234F1Z5",
        "pan": "AABCA1234F",
        "payment_terms_days": 30,
        "credit_limit": Decimal("500000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Security Services
    {
        "vendor_code": "VND-007",
        "vendor_name": "SecureGuard Services",
        "category_code": "VND-SEC",
        "contact_person": "Major (Retd) Rajan",
        "email": "rajan@secureguard.in",
        "phone": "9876543216",
        "address": "Office 301, Business Center",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "gstin": "07AABCS5678G1Z3",
        "pan": "AABCS5678G",
        "payment_terms_days": 30,
        "credit_limit": Decimal("1000000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Housekeeping
    {
        "vendor_code": "VND-008",
        "vendor_name": "CleanPro Facility Management",
        "category_code": "VND-HOUSE",
        "contact_person": "Meena Sharma",
        "email": "meena@cleanpro.in",
        "phone": "9876543217",
        "address": "Floor 2, Vasant Vihar",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110057",
        "gstin": "07AABCC9012H1Z1",
        "pan": "AABCC9012H",
        "payment_terms_days": 30,
        "credit_limit": Decimal("800000.00"),
        "vendor_rating": "B",
        "is_active": True,
    },
    # Professional Services
    {
        "vendor_code": "VND-009",
        "vendor_name": "Kumar & Associates (Advocates)",
        "category_code": "VND-PROF",
        "contact_person": "Adv. Sunil Kumar",
        "email": "sunil@kumarassociates.com",
        "phone": "9876543218",
        "address": "Chamber 501, High Court",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400032",
        "gstin": "27AABFK3456I1Z9",
        "pan": "AABFK3456I",
        "payment_terms_days": 15,
        "credit_limit": Decimal("500000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    {
        "vendor_code": "VND-010",
        "vendor_name": "ABC Chartered Accountants",
        "category_code": "VND-PROF",
        "contact_person": "CA Anil Gupta",
        "email": "anil@abcca.in",
        "phone": "9876543219",
        "address": "Suite 1001, Financial Tower",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400021",
        "gstin": "27AABFA7890J1Z7",
        "pan": "AABFA7890J",
        "payment_terms_days": 30,
        "credit_limit": Decimal("1000000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Travel & Transport
    {
        "vendor_code": "VND-011",
        "vendor_name": "Swift Travels Pvt Ltd",
        "category_code": "VND-TRAVEL",
        "contact_person": "Rohit Jain",
        "email": "rohit@swifttravels.in",
        "phone": "9876543220",
        "address": "Ground Floor, Travel House",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400053",
        "gstin": "27AABCS1234K1Z5",
        "pan": "AABCS1234K",
        "payment_terms_days": 7,
        "credit_limit": Decimal("500000.00"),
        "vendor_rating": "B",
        "is_active": True,
    },
    {
        "vendor_code": "VND-012",
        "vendor_name": "BlueDart Express Ltd",
        "category_code": "VND-TRAVEL",
        "contact_person": "Customer Service",
        "email": "corporate@bluedart.com",
        "phone": "1860123456",
        "address": "Blue Dart Centre, Sahar Airport Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400099",
        "gstin": "27AABCB5678L1Z3",
        "pan": "AABCB5678L",
        "payment_terms_days": 15,
        "credit_limit": Decimal("200000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Marketing
    {
        "vendor_code": "VND-013",
        "vendor_name": "Creative Minds Advertising",
        "category_code": "VND-MKTG",
        "contact_person": "Neha Kapoor",
        "email": "neha@creativeminds.in",
        "phone": "9876543221",
        "address": "Studio 401, Film City Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400097",
        "gstin": "27AABCC9012M1Z1",
        "pan": "AABCC9012M",
        "payment_terms_days": 30,
        "credit_limit": Decimal("1500000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    # Utilities
    {
        "vendor_code": "VND-014",
        "vendor_name": "Tata Teleservices",
        "category_code": "VND-UTIL",
        "contact_person": "Enterprise Sales",
        "email": "enterprise@tatatele.com",
        "phone": "1800123456",
        "address": "Tata Communications Centre",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001",
        "gstin": "27AAACT3456N1Z9",
        "pan": "AAACT3456N",
        "payment_terms_days": 15,
        "credit_limit": Decimal("500000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
    {
        "vendor_code": "VND-015",
        "vendor_name": "Airtel Business",
        "category_code": "VND-UTIL",
        "contact_person": "Corporate Sales",
        "email": "business@airtel.com",
        "phone": "1800234567",
        "address": "Bharti Crescent, Nelson Mandela Road",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110070",
        "gstin": "07AAACB7890O1Z7",
        "pan": "AAACB7890O",
        "payment_terms_days": 15,
        "credit_limit": Decimal("500000.00"),
        "vendor_rating": "A",
        "is_active": True,
    },
]


# =============================================================================
# PURCHASE TERMS DATA
# =============================================================================

PURCHASE_TERMS = [
    {
        "term_code": "PAY-ADV",
        "term_name": "100% Advance",
        "description": "Full payment before delivery",
        "advance_percentage": Decimal("100.00"),
        "on_delivery_percentage": Decimal("0.00"),
        "credit_percentage": Decimal("0.00"),
        "credit_days": 0,
        "is_active": True,
    },
    {
        "term_code": "PAY-50-50",
        "term_name": "50% Advance, 50% on Delivery",
        "description": "Half advance, half on delivery",
        "advance_percentage": Decimal("50.00"),
        "on_delivery_percentage": Decimal("50.00"),
        "credit_percentage": Decimal("0.00"),
        "credit_days": 0,
        "is_active": True,
    },
    {
        "term_code": "PAY-COD",
        "term_name": "Cash on Delivery",
        "description": "Full payment on delivery",
        "advance_percentage": Decimal("0.00"),
        "on_delivery_percentage": Decimal("100.00"),
        "credit_percentage": Decimal("0.00"),
        "credit_days": 0,
        "is_active": True,
    },
    {
        "term_code": "PAY-NET15",
        "term_name": "Net 15 Days",
        "description": "Payment within 15 days of invoice",
        "advance_percentage": Decimal("0.00"),
        "on_delivery_percentage": Decimal("0.00"),
        "credit_percentage": Decimal("100.00"),
        "credit_days": 15,
        "is_active": True,
    },
    {
        "term_code": "PAY-NET30",
        "term_name": "Net 30 Days",
        "description": "Payment within 30 days of invoice",
        "advance_percentage": Decimal("0.00"),
        "on_delivery_percentage": Decimal("0.00"),
        "credit_percentage": Decimal("100.00"),
        "credit_days": 30,
        "is_active": True,
    },
    {
        "term_code": "PAY-NET45",
        "term_name": "Net 45 Days",
        "description": "Payment within 45 days of invoice",
        "advance_percentage": Decimal("0.00"),
        "on_delivery_percentage": Decimal("0.00"),
        "credit_percentage": Decimal("100.00"),
        "credit_days": 45,
        "is_active": True,
    },
    {
        "term_code": "PAY-NET60",
        "term_name": "Net 60 Days",
        "description": "Payment within 60 days of invoice",
        "advance_percentage": Decimal("0.00"),
        "on_delivery_percentage": Decimal("0.00"),
        "credit_percentage": Decimal("100.00"),
        "credit_days": 60,
        "is_active": True,
    },
    {
        "term_code": "PAY-30-70",
        "term_name": "30% Advance, 70% Net 30",
        "description": "30% advance, balance in 30 days",
        "advance_percentage": Decimal("30.00"),
        "on_delivery_percentage": Decimal("0.00"),
        "credit_percentage": Decimal("70.00"),
        "credit_days": 30,
        "is_active": True,
    },
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("Procurement Module Direct Seed Script")
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

            # Check if vendor table exists (from AP/AR module)
            result = await session.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'mst_vendor')")
            )
            vendor_table_exists = result.scalar()

            if vendor_table_exists:
                # Seed Vendors
                print("\n--- Seeding Vendors ---")
                count = 0
                for vendor_data in VENDORS:
                    # Check if exists
                    result = await session.execute(
                        text("SELECT id FROM mst_vendor WHERE organization_id = :org_id AND vendor_code = :code"),
                        {"org_id": org_id, "code": vendor_data["vendor_code"]}
                    )
                    if result.fetchone():
                        print(f"  - Skipped (exists): {vendor_data['vendor_code']}")
                        continue

                    # Insert vendor
                    await session.execute(
                        text("""
                            INSERT INTO mst_vendor (
                                organization_id, vendor_code, vendor_name, contact_person,
                                email, phone, address, city, state, pincode,
                                gstin, pan, payment_terms_days, credit_limit,
                                vendor_rating, is_active, created_by_id
                            ) VALUES (
                                :org_id, :vendor_code, :vendor_name, :contact_person,
                                :email, :phone, :address, :city, :state, :pincode,
                                :gstin, :pan, :payment_terms_days, :credit_limit,
                                :vendor_rating, :is_active, :user_id
                            )
                        """),
                        {
                            "org_id": org_id,
                            "vendor_code": vendor_data["vendor_code"],
                            "vendor_name": vendor_data["vendor_name"],
                            "contact_person": vendor_data["contact_person"],
                            "email": vendor_data["email"],
                            "phone": vendor_data["phone"],
                            "address": vendor_data["address"],
                            "city": vendor_data["city"],
                            "state": vendor_data["state"],
                            "pincode": vendor_data["pincode"],
                            "gstin": vendor_data["gstin"],
                            "pan": vendor_data["pan"],
                            "payment_terms_days": vendor_data["payment_terms_days"],
                            "credit_limit": vendor_data["credit_limit"],
                            "vendor_rating": vendor_data["vendor_rating"],
                            "is_active": vendor_data["is_active"],
                            "user_id": user_id,
                        }
                    )
                    count += 1
                await session.commit()
                print(f"  ✓ Created {count} vendors")
            else:
                print("\n--- Skipping Vendors (table not found) ---")

            print("\n" + "=" * 60)
            print("✓ Procurement Module seed data created successfully!")
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
