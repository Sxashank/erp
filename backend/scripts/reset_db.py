"""Reset database and create all tables."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, Base

# Import all models to register them with Base
from app.models import *  # noqa


async def reset_database():
    """Drop all tables and recreate them."""
    print("Dropping all tables...")
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)

        # Drop any enums that might exist
        await conn.execute(text("DROP TYPE IF EXISTS accountnature CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS voucherstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS voucherclass CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS vendortype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS gstregistrationtype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS paymentmodepreference CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS balancetype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS customertype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS billstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS paymentstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS supplytype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS invoicestatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS receiptstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS invoicesupplytype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS einvoicestatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS paymenttype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS partytype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS paymentmode CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS chequestatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS documenttype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS statementtransactiontype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS reconciliationstatus CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS bankreconciliationstatus CASCADE"))

    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_database())
