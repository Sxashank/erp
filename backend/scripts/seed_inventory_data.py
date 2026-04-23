"""
Direct database seed script for Inventory Module master data.
Inserts data directly into the database without requiring API authentication.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_inventory_data.py
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


# =============================================================================
# ITEM CATEGORIES DATA
# =============================================================================

ITEM_CATEGORIES = [
    # Office Supplies
    {
        "category_code": "OFF-STAT",
        "category_name": "Stationery",
        "description": "Office stationery items like pens, paper, files",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "OFF-COMP",
        "category_name": "Computer Accessories",
        "description": "Computer peripherals and accessories",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "OFF-FURN",
        "category_name": "Office Furniture",
        "description": "Desks, chairs, cabinets",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "OFF-ELEC",
        "category_name": "Electronics",
        "description": "Electronic equipment and devices",
        "parent_code": None,
        "is_active": True,
    },
    # Consumables
    {
        "category_code": "CON-PRINT",
        "category_name": "Printing Consumables",
        "description": "Toner, ink cartridges, printing paper",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "CON-CLEAN",
        "category_name": "Cleaning Supplies",
        "description": "Cleaning materials and supplies",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "CON-CAFE",
        "category_name": "Cafeteria Supplies",
        "description": "Tea, coffee, disposables",
        "parent_code": None,
        "is_active": True,
    },
    # IT Assets
    {
        "category_code": "IT-HARD",
        "category_name": "IT Hardware",
        "description": "Computers, laptops, servers",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "IT-NET",
        "category_name": "Networking Equipment",
        "description": "Routers, switches, cables",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "IT-SEC",
        "category_name": "Security Equipment",
        "description": "CCTV, access control systems",
        "parent_code": None,
        "is_active": True,
    },
    # Marketing
    {
        "category_code": "MKT-PROMO",
        "category_name": "Promotional Materials",
        "description": "Brochures, banners, standees",
        "parent_code": None,
        "is_active": True,
    },
    {
        "category_code": "MKT-GIFT",
        "category_name": "Corporate Gifts",
        "description": "Gifts for clients and employees",
        "parent_code": None,
        "is_active": True,
    },
]


# =============================================================================
# WAREHOUSES DATA
# =============================================================================

WAREHOUSES = [
    {
        "warehouse_code": "WH-HO-MUM",
        "warehouse_name": "Head Office Warehouse - Mumbai",
        "address": "Plot 5, BKC Complex, Bandra Kurla Complex",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400051",
        "contact_person": "Rajesh Kumar",
        "contact_phone": "9876543210",
        "is_active": True,
    },
    {
        "warehouse_code": "WH-BR-DEL",
        "warehouse_name": "Delhi Branch Store",
        "address": "Tower A, Connaught Place",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "contact_person": "Amit Singh",
        "contact_phone": "9876543211",
        "is_active": True,
    },
    {
        "warehouse_code": "WH-BR-CHN",
        "warehouse_name": "Chennai Branch Store",
        "address": "3rd Floor, Anna Salai Complex",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600002",
        "contact_person": "Suresh Rajan",
        "contact_phone": "9876543212",
        "is_active": True,
    },
    {
        "warehouse_code": "WH-BR-BLR",
        "warehouse_name": "Bangalore Branch Store",
        "address": "Tech Park, Electronic City",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560100",
        "contact_person": "Deepak Sharma",
        "contact_phone": "9876543213",
        "is_active": True,
    },
    {
        "warehouse_code": "WH-BR-HYD",
        "warehouse_name": "Hyderabad Branch Store",
        "address": "HITEC City, Madhapur",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500081",
        "contact_person": "Ravi Teja",
        "contact_phone": "9876543214",
        "is_active": True,
    },
    {
        "warehouse_code": "WH-BR-KOL",
        "warehouse_name": "Kolkata Branch Store",
        "address": "Salt Lake Sector V",
        "city": "Kolkata",
        "state": "West Bengal",
        "pincode": "700091",
        "contact_person": "Soumya Das",
        "contact_phone": "9876543215",
        "is_active": True,
    },
]


# =============================================================================
# ITEMS MASTER DATA
# =============================================================================

ITEMS = [
    # Stationery Items
    {
        "item_code": "STAT-001",
        "item_name": "A4 Copier Paper (500 sheets)",
        "category_code": "OFF-STAT",
        "unit_of_measure": "Ream",
        "reorder_level": 100,
        "reorder_quantity": 500,
        "standard_cost": Decimal("250.00"),
        "is_active": True,
    },
    {
        "item_code": "STAT-002",
        "item_name": "Ball Point Pen (Blue)",
        "category_code": "OFF-STAT",
        "unit_of_measure": "Box",
        "reorder_level": 50,
        "reorder_quantity": 200,
        "standard_cost": Decimal("150.00"),
        "is_active": True,
    },
    {
        "item_code": "STAT-003",
        "item_name": "File Folder (Box of 10)",
        "category_code": "OFF-STAT",
        "unit_of_measure": "Box",
        "reorder_level": 20,
        "reorder_quantity": 100,
        "standard_cost": Decimal("350.00"),
        "is_active": True,
    },
    {
        "item_code": "STAT-004",
        "item_name": "Stapler Heavy Duty",
        "category_code": "OFF-STAT",
        "unit_of_measure": "Piece",
        "reorder_level": 10,
        "reorder_quantity": 50,
        "standard_cost": Decimal("450.00"),
        "is_active": True,
    },
    {
        "item_code": "STAT-005",
        "item_name": "Stapler Pins (5000)",
        "category_code": "OFF-STAT",
        "unit_of_measure": "Box",
        "reorder_level": 30,
        "reorder_quantity": 100,
        "standard_cost": Decimal("75.00"),
        "is_active": True,
    },
    # Computer Accessories
    {
        "item_code": "COMP-001",
        "item_name": "USB Mouse Wireless",
        "category_code": "OFF-COMP",
        "unit_of_measure": "Piece",
        "reorder_level": 10,
        "reorder_quantity": 50,
        "standard_cost": Decimal("650.00"),
        "is_active": True,
    },
    {
        "item_code": "COMP-002",
        "item_name": "USB Keyboard",
        "category_code": "OFF-COMP",
        "unit_of_measure": "Piece",
        "reorder_level": 10,
        "reorder_quantity": 50,
        "standard_cost": Decimal("750.00"),
        "is_active": True,
    },
    {
        "item_code": "COMP-003",
        "item_name": "USB Hub 4-Port",
        "category_code": "OFF-COMP",
        "unit_of_measure": "Piece",
        "reorder_level": 5,
        "reorder_quantity": 20,
        "standard_cost": Decimal("550.00"),
        "is_active": True,
    },
    {
        "item_code": "COMP-004",
        "item_name": "HDMI Cable 2m",
        "category_code": "OFF-COMP",
        "unit_of_measure": "Piece",
        "reorder_level": 10,
        "reorder_quantity": 30,
        "standard_cost": Decimal("350.00"),
        "is_active": True,
    },
    # Printing Consumables
    {
        "item_code": "PRINT-001",
        "item_name": "HP Toner Cartridge 78A",
        "category_code": "CON-PRINT",
        "unit_of_measure": "Piece",
        "reorder_level": 5,
        "reorder_quantity": 20,
        "standard_cost": Decimal("3500.00"),
        "is_active": True,
    },
    {
        "item_code": "PRINT-002",
        "item_name": "Canon Ink Cartridge Black",
        "category_code": "CON-PRINT",
        "unit_of_measure": "Piece",
        "reorder_level": 5,
        "reorder_quantity": 20,
        "standard_cost": Decimal("1200.00"),
        "is_active": True,
    },
    {
        "item_code": "PRINT-003",
        "item_name": "Canon Ink Cartridge Color Set",
        "category_code": "CON-PRINT",
        "unit_of_measure": "Set",
        "reorder_level": 3,
        "reorder_quantity": 10,
        "standard_cost": Decimal("2500.00"),
        "is_active": True,
    },
    # Cleaning Supplies
    {
        "item_code": "CLEAN-001",
        "item_name": "Floor Cleaner 5L",
        "category_code": "CON-CLEAN",
        "unit_of_measure": "Can",
        "reorder_level": 10,
        "reorder_quantity": 50,
        "standard_cost": Decimal("350.00"),
        "is_active": True,
    },
    {
        "item_code": "CLEAN-002",
        "item_name": "Glass Cleaner 500ml",
        "category_code": "CON-CLEAN",
        "unit_of_measure": "Bottle",
        "reorder_level": 20,
        "reorder_quantity": 100,
        "standard_cost": Decimal("150.00"),
        "is_active": True,
    },
    {
        "item_code": "CLEAN-003",
        "item_name": "Hand Sanitizer 500ml",
        "category_code": "CON-CLEAN",
        "unit_of_measure": "Bottle",
        "reorder_level": 50,
        "reorder_quantity": 200,
        "standard_cost": Decimal("250.00"),
        "is_active": True,
    },
    # Cafeteria Supplies
    {
        "item_code": "CAFE-001",
        "item_name": "Premium Tea 1kg",
        "category_code": "CON-CAFE",
        "unit_of_measure": "Packet",
        "reorder_level": 10,
        "reorder_quantity": 50,
        "standard_cost": Decimal("450.00"),
        "is_active": True,
    },
    {
        "item_code": "CAFE-002",
        "item_name": "Instant Coffee 500g",
        "category_code": "CON-CAFE",
        "unit_of_measure": "Jar",
        "reorder_level": 10,
        "reorder_quantity": 50,
        "standard_cost": Decimal("650.00"),
        "is_active": True,
    },
    {
        "item_code": "CAFE-003",
        "item_name": "Sugar 5kg",
        "category_code": "CON-CAFE",
        "unit_of_measure": "Bag",
        "reorder_level": 5,
        "reorder_quantity": 20,
        "standard_cost": Decimal("225.00"),
        "is_active": True,
    },
    {
        "item_code": "CAFE-004",
        "item_name": "Paper Cups (100 pack)",
        "category_code": "CON-CAFE",
        "unit_of_measure": "Pack",
        "reorder_level": 20,
        "reorder_quantity": 100,
        "standard_cost": Decimal("120.00"),
        "is_active": True,
    },
    # IT Hardware
    {
        "item_code": "IT-001",
        "item_name": "Dell Desktop Computer i5",
        "category_code": "IT-HARD",
        "unit_of_measure": "Unit",
        "reorder_level": 2,
        "reorder_quantity": 10,
        "standard_cost": Decimal("55000.00"),
        "is_active": True,
    },
    {
        "item_code": "IT-002",
        "item_name": "HP Laptop 14-inch i5",
        "category_code": "IT-HARD",
        "unit_of_measure": "Unit",
        "reorder_level": 2,
        "reorder_quantity": 10,
        "standard_cost": Decimal("65000.00"),
        "is_active": True,
    },
    {
        "item_code": "IT-003",
        "item_name": "24-inch LED Monitor",
        "category_code": "IT-HARD",
        "unit_of_measure": "Unit",
        "reorder_level": 3,
        "reorder_quantity": 15,
        "standard_cost": Decimal("12000.00"),
        "is_active": True,
    },
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("Inventory Module Direct Seed Script")
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

            # Seed Item Categories
            print("\n--- Seeding Item Categories ---")
            category_ids = {}
            count = 0
            for cat_data in ITEM_CATEGORIES:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_item_category WHERE organization_id = :org_id AND category_code = :code"),
                    {"org_id": org_id, "code": cat_data["category_code"]}
                )
                existing = result.fetchone()
                if existing:
                    category_ids[cat_data["category_code"]] = existing[0]
                    print(f"  - Skipped (exists): {cat_data['category_code']}")
                    continue

                # Insert category
                result = await session.execute(
                    text("""
                        INSERT INTO mst_item_category (
                            organization_id, category_code, category_name, description,
                            parent_id, is_active, created_by_id
                        ) VALUES (
                            :org_id, :category_code, :category_name, :description,
                            NULL, :is_active, :user_id
                        ) RETURNING id
                    """),
                    {
                        "org_id": org_id,
                        "category_code": cat_data["category_code"],
                        "category_name": cat_data["category_name"],
                        "description": cat_data["description"],
                        "is_active": cat_data["is_active"],
                        "user_id": user_id,
                    }
                )
                new_id = result.fetchone()[0]
                category_ids[cat_data["category_code"]] = new_id
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} item categories")

            # Seed Warehouses
            print("\n--- Seeding Warehouses ---")
            warehouse_ids = {}
            count = 0
            for wh_data in WAREHOUSES:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_warehouse WHERE organization_id = :org_id AND warehouse_code = :code"),
                    {"org_id": org_id, "code": wh_data["warehouse_code"]}
                )
                existing = result.fetchone()
                if existing:
                    warehouse_ids[wh_data["warehouse_code"]] = existing[0]
                    print(f"  - Skipped (exists): {wh_data['warehouse_code']}")
                    continue

                # Insert warehouse
                result = await session.execute(
                    text("""
                        INSERT INTO mst_warehouse (
                            organization_id, warehouse_code, warehouse_name, address,
                            city, state, pincode, contact_person, contact_phone,
                            is_active, created_by_id
                        ) VALUES (
                            :org_id, :warehouse_code, :warehouse_name, :address,
                            :city, :state, :pincode, :contact_person, :contact_phone,
                            :is_active, :user_id
                        ) RETURNING id
                    """),
                    {
                        "org_id": org_id,
                        "warehouse_code": wh_data["warehouse_code"],
                        "warehouse_name": wh_data["warehouse_name"],
                        "address": wh_data["address"],
                        "city": wh_data["city"],
                        "state": wh_data["state"],
                        "pincode": wh_data["pincode"],
                        "contact_person": wh_data["contact_person"],
                        "contact_phone": wh_data["contact_phone"],
                        "is_active": wh_data["is_active"],
                        "user_id": user_id,
                    }
                )
                new_id = result.fetchone()[0]
                warehouse_ids[wh_data["warehouse_code"]] = new_id
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} warehouses")

            # Seed Items
            print("\n--- Seeding Items ---")
            count = 0
            for item_data in ITEMS:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_item_master WHERE organization_id = :org_id AND item_code = :code"),
                    {"org_id": org_id, "code": item_data["item_code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {item_data['item_code']}")
                    continue

                # Get category ID
                category_id = category_ids.get(item_data["category_code"])
                if not category_id:
                    print(f"  - Skipped (no category): {item_data['item_code']}")
                    continue

                # Insert item
                await session.execute(
                    text("""
                        INSERT INTO mst_item_master (
                            organization_id, item_code, item_name, category_id,
                            unit_of_measure, reorder_level, reorder_quantity,
                            standard_cost, is_active, created_by_id
                        ) VALUES (
                            :org_id, :item_code, :item_name, :category_id,
                            :unit_of_measure, :reorder_level, :reorder_quantity,
                            :standard_cost, :is_active, :user_id
                        )
                    """),
                    {
                        "org_id": org_id,
                        "item_code": item_data["item_code"],
                        "item_name": item_data["item_name"],
                        "category_id": category_id,
                        "unit_of_measure": item_data["unit_of_measure"],
                        "reorder_level": item_data["reorder_level"],
                        "reorder_quantity": item_data["reorder_quantity"],
                        "standard_cost": item_data["standard_cost"],
                        "is_active": item_data["is_active"],
                        "user_id": user_id,
                    }
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} items")

            # Initialize stock balances for head office warehouse
            print("\n--- Initializing Stock Balances ---")
            ho_warehouse_id = warehouse_ids.get("WH-HO-MUM")
            if ho_warehouse_id:
                result = await session.execute(
                    text("SELECT id, item_code FROM mst_item_master WHERE organization_id = :org_id"),
                    {"org_id": org_id}
                )
                items = result.fetchall()
                count = 0
                for item_id, item_code in items:
                    # Check if stock balance exists
                    result = await session.execute(
                        text("""
                            SELECT id FROM txn_stock_balance
                            WHERE item_id = :item_id AND warehouse_id = :warehouse_id
                        """),
                        {"item_id": item_id, "warehouse_id": ho_warehouse_id}
                    )
                    if result.fetchone():
                        continue

                    # Create initial stock balance with random quantity
                    import random
                    initial_qty = random.randint(50, 500)
                    await session.execute(
                        text("""
                            INSERT INTO txn_stock_balance (
                                organization_id, item_id, warehouse_id, quantity,
                                reserved_quantity, available_quantity, created_by_id
                            ) VALUES (
                                :org_id, :item_id, :warehouse_id, :quantity,
                                0, :quantity, :user_id
                            )
                        """),
                        {
                            "org_id": org_id,
                            "item_id": item_id,
                            "warehouse_id": ho_warehouse_id,
                            "quantity": initial_qty,
                            "user_id": user_id,
                        }
                    )
                    count += 1
                await session.commit()
                print(f"  ✓ Created {count} stock balances")

            print("\n" + "=" * 60)
            print("✓ Inventory Module seed data created successfully!")
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
