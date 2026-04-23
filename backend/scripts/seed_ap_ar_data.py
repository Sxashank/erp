#!/usr/bin/env python3
"""Seed AP/AR data - vendors, customers, purchase bills, sales invoices, payments."""

import asyncio
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import async_session_factory, engine, Base
from app.models.masters.organization import Organization
from app.models.masters.unit import Unit
from app.models.auth.user import User
from app.models.finance.account import Account
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.finance.voucher_type import VoucherType
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.gst.gst_rate import GSTRate
from app.models.tds.tds_section import TDSSection
from app.models.ap_ar.payment_terms import PaymentTerms
from app.models.ap_ar.vendor import Vendor, VendorType, GSTRegistrationType as VendorGSTType
from app.models.ap_ar.customer import Customer, CustomerType, GSTRegistrationType as CustomerGSTType
from app.models.ap_ar.purchase_bill import PurchaseBill, PurchaseBillLine, BillStatus, PaymentStatus, SupplyType
from app.models.ap_ar.sales_invoice import SalesInvoice, SalesInvoiceLine, InvoiceStatus, ReceiptStatus, EInvoiceStatus
from app.models.ap_ar.payment import (
    Payment, PaymentAllocation, PaymentType, PartyType, PaymentMode,
    PaymentStatus as PaymentStatusEnum, ChequeStatus, DocumentType
)
from app.core.constants import VoucherStatus as VoucherStatusEnum, BalanceType


# Sample Vendors
VENDORS = [
    {
        "code": "V001",
        "name": "ABC Technologies Pvt Ltd",
        "display_name": "ABC Technologies",
        "vendor_type": VendorType.SUPPLIER,
        "pan": "AAACA1234A",
        "gstin": "27AAACA1234A1Z5",
        "gst_registration_type": VendorGSTType.REGULAR,
        "contact_person": "Rajesh Kumar",
        "email": "rajesh@abctech.com",
        "phone": "+91 22 12345678",
        "mobile": "+91 9876543210",
        "address_line1": "123 Tech Park",
        "address_line2": "Andheri East",
        "city": "Mumbai",
        "state_code": "27",
        "pincode": "400069",
        "bank_name": "HDFC Bank",
        "bank_account_number": "12345678901234",
        "bank_ifsc_code": "HDFC0001234",
        "bank_branch": "Andheri East",
        "tds_applicable": True,
        "tds_section": "194C",
        "credit_days": 30,
    },
    {
        "code": "V002",
        "name": "XYZ Consulting Services",
        "display_name": "XYZ Consulting",
        "vendor_type": VendorType.SERVICE_PROVIDER,
        "pan": "AABCX5678B",
        "gstin": "27AABCX5678B1Z3",
        "gst_registration_type": VendorGSTType.REGULAR,
        "contact_person": "Priya Sharma",
        "email": "priya@xyzconsulting.com",
        "phone": "+91 22 98765432",
        "mobile": "+91 9123456789",
        "address_line1": "456 Business Center",
        "address_line2": "Bandra West",
        "city": "Mumbai",
        "state_code": "27",
        "pincode": "400050",
        "bank_name": "ICICI Bank",
        "bank_account_number": "23456789012345",
        "bank_ifsc_code": "ICIC0005678",
        "bank_branch": "Bandra West",
        "tds_applicable": True,
        "tds_section": "194J",
        "credit_days": 15,
    },
    {
        "code": "V003",
        "name": "Global IT Solutions",
        "display_name": "Global IT",
        "vendor_type": VendorType.SUPPLIER,
        "pan": "AABCG9012C",
        "gstin": "29AABCG9012C1Z1",
        "gst_registration_type": VendorGSTType.REGULAR,
        "contact_person": "Amit Patel",
        "email": "amit@globalit.com",
        "phone": "+91 80 11223344",
        "mobile": "+91 9988776655",
        "address_line1": "789 IT Park",
        "address_line2": "Electronic City",
        "city": "Bangalore",
        "state_code": "29",
        "pincode": "560100",
        "bank_name": "Axis Bank",
        "bank_account_number": "34567890123456",
        "bank_ifsc_code": "UTIB0009012",
        "bank_branch": "Electronic City",
        "tds_applicable": True,
        "tds_section": "194C",
        "credit_days": 45,
    },
    {
        "code": "V004",
        "name": "Office Supplies Co",
        "display_name": "Office Supplies",
        "vendor_type": VendorType.SUPPLIER,
        "pan": "AABCO3456D",
        "gstin": "27AABCO3456D1Z9",
        "gst_registration_type": VendorGSTType.REGULAR,
        "contact_person": "Sneha Reddy",
        "email": "sneha@officesupplies.com",
        "phone": "+91 22 55667788",
        "mobile": "+91 9876123456",
        "address_line1": "321 Commercial Complex",
        "address_line2": "Lower Parel",
        "city": "Mumbai",
        "state_code": "27",
        "pincode": "400013",
        "bank_name": "State Bank of India",
        "bank_account_number": "45678901234567",
        "bank_ifsc_code": "SBIN0003456",
        "bank_branch": "Lower Parel",
        "tds_applicable": False,
        "tds_section": None,
        "credit_days": 30,
    },
    {
        "code": "V005",
        "name": "Legal Associates LLP",
        "display_name": "Legal Associates",
        "vendor_type": VendorType.SERVICE_PROVIDER,
        "pan": "AABFL7890E",
        "gstin": "27AABFL7890E1Z7",
        "gst_registration_type": VendorGSTType.REGULAR,
        "contact_person": "Vikram Singh",
        "email": "vikram@legalassociates.com",
        "phone": "+91 22 33445566",
        "mobile": "+91 9765432109",
        "address_line1": "555 Law Chambers",
        "address_line2": "Fort",
        "city": "Mumbai",
        "state_code": "27",
        "pincode": "400001",
        "bank_name": "Kotak Mahindra Bank",
        "bank_account_number": "56789012345678",
        "bank_ifsc_code": "KKBK0007890",
        "bank_branch": "Fort",
        "tds_applicable": True,
        "tds_section": "194J",
        "credit_days": 15,
    },
]

# Sample Customers
CUSTOMERS = [
    {
        "code": "C001",
        "name": "Sunrise Industries Pvt Ltd",
        "display_name": "Sunrise Industries",
        "customer_type": CustomerType.COMPANY,
        "pan": "AABCS1111A",
        "gstin": "27AABCS1111A1Z1",
        "gst_registration_type": CustomerGSTType.REGULAR,
        "contact_person": "Ananya Gupta",
        "email": "ananya@sunrise.com",
        "phone": "+91 22 44556677",
        "mobile": "+91 9876501234",
        "billing_address_line1": "111 Industrial Estate",
        "billing_address_line2": "Thane",
        "billing_city": "Mumbai",
        "billing_state_code": "27",
        "billing_pincode": "400601",
        "credit_days": 30,
        "credit_limit": Decimal("1000000"),
    },
    {
        "code": "C002",
        "name": "BlueSky Enterprises",
        "display_name": "BlueSky",
        "customer_type": CustomerType.COMPANY,
        "pan": "AABCB2222B",
        "gstin": "27AABCB2222B1Z2",
        "gst_registration_type": CustomerGSTType.REGULAR,
        "contact_person": "Rahul Verma",
        "email": "rahul@bluesky.com",
        "phone": "+91 22 66778899",
        "mobile": "+91 9123450987",
        "billing_address_line1": "222 Trade Center",
        "billing_address_line2": "Navi Mumbai",
        "billing_city": "Navi Mumbai",
        "billing_state_code": "27",
        "billing_pincode": "400701",
        "credit_days": 45,
        "credit_limit": Decimal("500000"),
    },
    {
        "code": "C003",
        "name": "Green Valley Foods",
        "display_name": "Green Valley",
        "customer_type": CustomerType.COMPANY,
        "pan": "AABCG3333C",
        "gstin": "29AABCG3333C1Z3",
        "gst_registration_type": CustomerGSTType.REGULAR,
        "contact_person": "Meera Nair",
        "email": "meera@greenvalley.com",
        "phone": "+91 80 22334455",
        "mobile": "+91 9988001122",
        "billing_address_line1": "333 Food Park",
        "billing_address_line2": "Whitefield",
        "billing_city": "Bangalore",
        "billing_state_code": "29",
        "billing_pincode": "560066",
        "credit_days": 30,
        "credit_limit": Decimal("750000"),
    },
    {
        "code": "C004",
        "name": "Mr. Suresh Kumar",
        "display_name": "Suresh Kumar",
        "customer_type": CustomerType.INDIVIDUAL,
        "pan": "ABCPK4444D",
        "gstin": None,
        "gst_registration_type": CustomerGSTType.UNREGISTERED,
        "contact_person": "Suresh Kumar",
        "email": "suresh.kumar@gmail.com",
        "phone": None,
        "mobile": "+91 9876009876",
        "billing_address_line1": "444 Residential Complex",
        "billing_address_line2": "Powai",
        "billing_city": "Mumbai",
        "billing_state_code": "27",
        "billing_pincode": "400076",
        "credit_days": 15,
        "credit_limit": Decimal("100000"),
    },
    {
        "code": "C005",
        "name": "Metro Retail Chain",
        "display_name": "Metro Retail",
        "customer_type": CustomerType.COMPANY,
        "pan": "AABCM5555E",
        "gstin": "27AABCM5555E1Z5",
        "gst_registration_type": CustomerGSTType.REGULAR,
        "contact_person": "Deepak Joshi",
        "email": "deepak@metroretail.com",
        "phone": "+91 22 99887766",
        "mobile": "+91 9765098765",
        "billing_address_line1": "555 Mall Road",
        "billing_address_line2": "Malad West",
        "billing_city": "Mumbai",
        "billing_state_code": "27",
        "billing_pincode": "400064",
        "credit_days": 60,
        "credit_limit": Decimal("2000000"),
    },
]


async def seed_vendors(session, org, payment_terms_map, tds_section_map, account_map):
    """Seed sample vendors."""
    print("\nSeeding vendors...")

    # Check if vendors already exist
    result = await session.execute(
        select(Vendor).where(Vendor.organization_id == org.id)
    )
    existing_vendors = result.scalars().all()
    if existing_vendors:
        print("  - Vendors already exist")
        return {v.code: v for v in existing_vendors}

    vendor_map = {}
    for v_data in VENDORS:
        # Get TDS section if applicable
        tds_section_id = None
        if v_data.get("tds_section") and v_data["tds_section"] in tds_section_map:
            tds_section_id = tds_section_map[v_data["tds_section"]].id

        # Get default payment terms
        payment_terms_id = None
        if "NET30" in payment_terms_map:
            payment_terms_id = payment_terms_map["NET30"].id

        # Get control account (Trade Payables)
        control_account_id = None
        if "2201" in account_map:
            control_account_id = account_map["2201"].id

        vendor = Vendor(
            code=v_data["code"],
            name=v_data["name"],
            display_name=v_data["display_name"],
            vendor_type=v_data["vendor_type"],
            pan=v_data["pan"],
            gstin=v_data.get("gstin"),
            gst_registration_type=v_data["gst_registration_type"],
            contact_person=v_data["contact_person"],
            email=v_data["email"],
            phone=v_data.get("phone"),
            mobile=v_data.get("mobile"),
            address_line1=v_data["address_line1"],
            address_line2=v_data.get("address_line2"),
            city=v_data["city"],
            state_code=v_data["state_code"],
            pincode=v_data["pincode"],
            country="IN",
            bank_name=v_data.get("bank_name"),
            bank_account_number=v_data.get("bank_account_number"),
            bank_ifsc_code=v_data.get("bank_ifsc_code"),
            bank_branch=v_data.get("bank_branch"),
            tds_applicable=v_data.get("tds_applicable", False),
            tds_section_id=tds_section_id,
            payment_terms_id=payment_terms_id,
            credit_days=v_data.get("credit_days", 30),
            control_account_id=control_account_id,
            organization_id=org.id,
            opening_balance=Decimal("0"),
            current_balance=Decimal("0"),
        )
        session.add(vendor)
        await session.flush()
        vendor_map[v_data["code"]] = vendor
        print(f"  + Created vendor '{v_data['code']}' - {v_data['name']}")

    await session.commit()
    print(f"Total vendors: {len(vendor_map)}")
    return vendor_map


async def seed_customers(session, org, payment_terms_map, account_map):
    """Seed sample customers."""
    print("\nSeeding customers...")

    # Check if customers already exist
    result = await session.execute(
        select(Customer).where(Customer.organization_id == org.id)
    )
    existing_customers = result.scalars().all()
    if existing_customers:
        print("  - Customers already exist")
        return {c.code: c for c in existing_customers}

    customer_map = {}
    for c_data in CUSTOMERS:
        # Get default payment terms
        payment_terms_id = None
        if "NET30" in payment_terms_map:
            payment_terms_id = payment_terms_map["NET30"].id

        # Get control account (Trade Receivables)
        control_account_id = None
        if "1301" in account_map:
            control_account_id = account_map["1301"].id

        customer = Customer(
            code=c_data["code"],
            name=c_data["name"],
            display_name=c_data["display_name"],
            customer_type=c_data["customer_type"],
            pan=c_data.get("pan"),
            gstin=c_data.get("gstin"),
            gst_registration_type=c_data["gst_registration_type"],
            contact_person=c_data["contact_person"],
            email=c_data["email"],
            phone=c_data.get("phone"),
            mobile=c_data.get("mobile"),
            billing_address_line1=c_data["billing_address_line1"],
            billing_address_line2=c_data.get("billing_address_line2"),
            billing_city=c_data["billing_city"],
            billing_state_code=c_data["billing_state_code"],
            billing_pincode=c_data["billing_pincode"],
            billing_country="IN",
            shipping_address_line1=c_data["billing_address_line1"],
            shipping_address_line2=c_data.get("billing_address_line2"),
            shipping_city=c_data["billing_city"],
            shipping_state_code=c_data["billing_state_code"],
            shipping_pincode=c_data["billing_pincode"],
            shipping_country="IN",
            payment_terms_id=payment_terms_id,
            credit_days=c_data.get("credit_days", 30),
            credit_limit=c_data.get("credit_limit", Decimal("0")),
            credit_limit_enabled=True,
            control_account_id=control_account_id,
            organization_id=org.id,
            opening_balance=Decimal("0"),
            current_balance=Decimal("0"),
        )
        session.add(customer)
        await session.flush()
        customer_map[c_data["code"]] = customer
        print(f"  + Created customer '{c_data['code']}' - {c_data['name']}")

    await session.commit()
    print(f"Total customers: {len(customer_map)}")
    return customer_map


async def seed_purchase_bills(session, org, vendor_map, gst_rate_map, account_map, admin_user):
    """Seed sample purchase bills."""
    print("\nSeeding purchase bills...")

    # Check if purchase bills already exist
    result = await session.execute(
        select(PurchaseBill).where(PurchaseBill.organization_id == org.id).limit(1)
    )
    if result.scalar_one_or_none():
        print("  - Purchase bills already exist")
        return

    # Get expense account
    expense_account = account_map.get("5201")  # IT Expenses
    gst_rate_18 = None
    for code, rate in gst_rate_map.items():
        if rate.rate == Decimal("18"):
            gst_rate_18 = rate
            break

    bills_data = [
        {
            "vendor": "V001",
            "invoice_number": "INV-2024-001",
            "invoice_date": date(2024, 12, 1),
            "bill_date": date(2024, 12, 2),
            "status": BillStatus.APPROVED,
            "lines": [
                {"description": "IT Hardware - Laptops (5 units)", "qty": 5, "price": Decimal("45000"), "hsn": "8471"},
                {"description": "IT Hardware - Monitors (5 units)", "qty": 5, "price": Decimal("12000"), "hsn": "8528"},
            ]
        },
        {
            "vendor": "V002",
            "invoice_number": "XYZ-2024-156",
            "invoice_date": date(2024, 12, 5),
            "bill_date": date(2024, 12, 6),
            "status": BillStatus.APPROVED,
            "lines": [
                {"description": "Consulting Services - Dec 2024", "qty": 1, "price": Decimal("150000"), "hsn": "998311"},
            ]
        },
        {
            "vendor": "V003",
            "invoice_number": "GIT-2024-789",
            "invoice_date": date(2024, 12, 10),
            "bill_date": date(2024, 12, 11),
            "status": BillStatus.DRAFT,
            "lines": [
                {"description": "Software Licenses - Annual", "qty": 10, "price": Decimal("25000"), "hsn": "998314"},
            ]
        },
        {
            "vendor": "V004",
            "invoice_number": "OS-2024-445",
            "invoice_date": date(2024, 12, 15),
            "bill_date": date(2024, 12, 15),
            "status": BillStatus.SUBMITTED,
            "lines": [
                {"description": "Office Stationery", "qty": 1, "price": Decimal("15000"), "hsn": "4820"},
                {"description": "Printer Cartridges", "qty": 10, "price": Decimal("2500"), "hsn": "8443"},
            ]
        },
        {
            "vendor": "V005",
            "invoice_number": "LA-2024-089",
            "invoice_date": date(2024, 12, 18),
            "bill_date": date(2024, 12, 19),
            "status": BillStatus.PAID,
            "lines": [
                {"description": "Legal Retainer - Dec 2024", "qty": 1, "price": Decimal("75000"), "hsn": "998212"},
            ]
        },
    ]

    bill_counter = 0
    for bill_data in bills_data:
        vendor = vendor_map.get(bill_data["vendor"])
        if not vendor:
            continue

        bill_counter += 1
        bill_number = f"PB-2024-{bill_counter:04d}"

        # Calculate amounts
        subtotal = Decimal("0")
        for line in bill_data["lines"]:
            subtotal += line["qty"] * line["price"]

        # Calculate GST (assuming intra-state for Mumbai vendors)
        is_intra_state = vendor.state_code == "27"
        cgst_amount = sgst_amount = igst_amount = Decimal("0")

        if is_intra_state:
            cgst_amount = subtotal * Decimal("0.09")
            sgst_amount = subtotal * Decimal("0.09")
        else:
            igst_amount = subtotal * Decimal("0.18")

        total_amount = subtotal + cgst_amount + sgst_amount + igst_amount

        bill = PurchaseBill(
            bill_number=bill_number,
            vendor_invoice_number=bill_data["invoice_number"],
            vendor_invoice_date=bill_data["invoice_date"],
            bill_date=bill_data["bill_date"],
            due_date=bill_data["bill_date"] + timedelta(days=vendor.credit_days),
            vendor_id=vendor.id,
            organization_id=org.id,
            subtotal=subtotal,
            taxable_amount=subtotal,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount,
            total_amount=total_amount,
            balance_amount=total_amount if bill_data["status"] != BillStatus.PAID else Decimal("0"),
            supply_type=SupplyType.INTRA_STATE if is_intra_state else SupplyType.INTER_STATE,
            vendor_gstin=vendor.gstin,
            place_of_supply=vendor.state_code,
            status=bill_data["status"],
            payment_status=PaymentStatus.PAID if bill_data["status"] == BillStatus.PAID else PaymentStatus.UNPAID,
            created_by=admin_user.id,
        )
        session.add(bill)
        await session.flush()

        # Create bill lines
        for idx, line_data in enumerate(bill_data["lines"]):
            line_subtotal = line_data["qty"] * line_data["price"]
            line_cgst = line_subtotal * Decimal("0.09") if is_intra_state else Decimal("0")
            line_sgst = line_subtotal * Decimal("0.09") if is_intra_state else Decimal("0")
            line_igst = line_subtotal * Decimal("0.18") if not is_intra_state else Decimal("0")

            line = PurchaseBillLine(
                bill_id=bill.id,
                line_number=idx + 1,
                description=line_data["description"],
                hsn_sac_code=line_data["hsn"],
                quantity=Decimal(str(line_data["qty"])),
                unit_price=line_data["price"],
                taxable_amount=line_subtotal,
                gst_rate_id=gst_rate_18.id if gst_rate_18 else None,
                cgst_rate=Decimal("9") if is_intra_state else Decimal("0"),
                cgst_amount=line_cgst,
                sgst_rate=Decimal("9") if is_intra_state else Decimal("0"),
                sgst_amount=line_sgst,
                igst_rate=Decimal("18") if not is_intra_state else Decimal("0"),
                igst_amount=line_igst,
                total_amount=line_subtotal + line_cgst + line_sgst + line_igst,
                expense_account_id=expense_account.id if expense_account else None,
                created_by=admin_user.id,
            )
            session.add(line)

        print(f"  + Created purchase bill '{bill_number}' - {vendor.name} - Rs.{total_amount:,.2f}")

    await session.commit()
    print(f"Total purchase bills: {bill_counter}")


async def seed_sales_invoices(session, org, customer_map, gst_rate_map, account_map, admin_user):
    """Seed sample sales invoices."""
    print("\nSeeding sales invoices...")

    # Check if sales invoices already exist
    result = await session.execute(
        select(SalesInvoice).where(SalesInvoice.organization_id == org.id).limit(1)
    )
    if result.scalar_one_or_none():
        print("  - Sales invoices already exist")
        return

    # Get revenue account
    revenue_account = account_map.get("4101")  # Interest Income
    gst_rate_18 = None
    for code, rate in gst_rate_map.items():
        if rate.rate == Decimal("18"):
            gst_rate_18 = rate
            break

    invoices_data = [
        {
            "customer": "C001",
            "invoice_date": date(2024, 12, 1),
            "status": InvoiceStatus.APPROVED,
            "lines": [
                {"description": "Financial Advisory Services - Nov 2024", "qty": 1, "price": Decimal("250000"), "sac": "998311"},
            ]
        },
        {
            "customer": "C002",
            "invoice_date": date(2024, 12, 5),
            "status": InvoiceStatus.APPROVED,
            "lines": [
                {"description": "Loan Processing Fee", "qty": 1, "price": Decimal("50000"), "sac": "997159"},
                {"description": "Documentation Charges", "qty": 1, "price": Decimal("10000"), "sac": "997159"},
            ]
        },
        {
            "customer": "C003",
            "invoice_date": date(2024, 12, 10),
            "status": InvoiceStatus.DRAFT,
            "lines": [
                {"description": "Working Capital Interest - Dec 2024", "qty": 1, "price": Decimal("175000"), "sac": "997113"},
            ]
        },
        {
            "customer": "C004",
            "invoice_date": date(2024, 12, 15),
            "status": InvoiceStatus.SUBMITTED,
            "lines": [
                {"description": "Personal Loan EMI - Dec 2024", "qty": 1, "price": Decimal("25000"), "sac": "997113"},
            ]
        },
        {
            "customer": "C005",
            "invoice_date": date(2024, 12, 18),
            "status": InvoiceStatus.RECEIVED,
            "lines": [
                {"description": "Credit Facility Fee", "qty": 1, "price": Decimal("100000"), "sac": "997159"},
                {"description": "Collateral Management Fee", "qty": 1, "price": Decimal("25000"), "sac": "997159"},
            ]
        },
    ]

    invoice_counter = 0
    for inv_data in invoices_data:
        customer = customer_map.get(inv_data["customer"])
        if not customer:
            continue

        invoice_counter += 1
        invoice_number = f"SI-2024-{invoice_counter:04d}"

        # Calculate amounts
        subtotal = Decimal("0")
        for line in inv_data["lines"]:
            subtotal += line["qty"] * line["price"]

        # Calculate GST
        is_intra_state = customer.billing_state_code == "27"
        cgst_amount = sgst_amount = igst_amount = Decimal("0")

        if is_intra_state:
            cgst_amount = subtotal * Decimal("0.09")
            sgst_amount = subtotal * Decimal("0.09")
        else:
            igst_amount = subtotal * Decimal("0.18")

        total_amount = subtotal + cgst_amount + sgst_amount + igst_amount

        invoice = SalesInvoice(
            invoice_number=invoice_number,
            invoice_date=inv_data["invoice_date"],
            due_date=inv_data["invoice_date"] + timedelta(days=customer.credit_days),
            customer_id=customer.id,
            organization_id=org.id,
            subtotal=subtotal,
            taxable_amount=subtotal,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount,
            total_amount=total_amount,
            balance_amount=total_amount if inv_data["status"] != InvoiceStatus.RECEIVED else Decimal("0"),
            supply_type=SupplyType.INTRA_STATE if is_intra_state else SupplyType.INTER_STATE,
            customer_gstin=customer.gstin,
            place_of_supply=customer.billing_state_code,
            status=inv_data["status"],
            receipt_status=ReceiptStatus.RECEIVED if inv_data["status"] == InvoiceStatus.RECEIVED else ReceiptStatus.UNRECEIVED,
            e_invoice_status=EInvoiceStatus.NOT_APPLICABLE,
            created_by=admin_user.id,
        )
        session.add(invoice)
        await session.flush()

        # Create invoice lines
        for idx, line_data in enumerate(inv_data["lines"]):
            line_subtotal = line_data["qty"] * line_data["price"]
            line_cgst = line_subtotal * Decimal("0.09") if is_intra_state else Decimal("0")
            line_sgst = line_subtotal * Decimal("0.09") if is_intra_state else Decimal("0")
            line_igst = line_subtotal * Decimal("0.18") if not is_intra_state else Decimal("0")

            line = SalesInvoiceLine(
                invoice_id=invoice.id,
                line_number=idx + 1,
                description=line_data["description"],
                hsn_sac_code=line_data["sac"],
                quantity=Decimal(str(line_data["qty"])),
                unit_price=line_data["price"],
                taxable_amount=line_subtotal,
                gst_rate_id=gst_rate_18.id if gst_rate_18 else None,
                cgst_rate=Decimal("9") if is_intra_state else Decimal("0"),
                cgst_amount=line_cgst,
                sgst_rate=Decimal("9") if is_intra_state else Decimal("0"),
                sgst_amount=line_sgst,
                igst_rate=Decimal("18") if not is_intra_state else Decimal("0"),
                igst_amount=line_igst,
                total_amount=line_subtotal + line_cgst + line_sgst + line_igst,
                revenue_account_id=revenue_account.id if revenue_account else None,
                created_by=admin_user.id,
            )
            session.add(line)

        print(f"  + Created sales invoice '{invoice_number}' - {customer.name} - Rs.{total_amount:,.2f}")

    await session.commit()
    print(f"Total sales invoices: {invoice_counter}")


async def seed_payments(session, org, vendor_map, customer_map, account_map, admin_user):
    """Seed sample payments and receipts."""
    print("\nSeeding payments and receipts...")

    # Check if payments already exist
    result = await session.execute(
        select(Payment).where(Payment.organization_id == org.id).limit(1)
    )
    if result.scalar_one_or_none():
        print("  - Payments already exist")
        return

    # Get bank account
    bank_account = account_map.get("1101")  # Bank Account

    payments_data = [
        # Vendor Payments
        {
            "type": PaymentType.VENDOR_PAYMENT,
            "party_type": PartyType.VENDOR,
            "party_code": "V005",
            "date": date(2024, 12, 20),
            "amount": Decimal("88500"),  # 75000 + 18% GST
            "mode": PaymentMode.NEFT,
            "reference": "UTR123456789",
            "status": PaymentStatusEnum.POSTED,
        },
        {
            "type": PaymentType.VENDOR_PAYMENT,
            "party_type": PartyType.VENDOR,
            "party_code": "V001",
            "date": date(2024, 12, 22),
            "amount": Decimal("150000"),
            "mode": PaymentMode.CHEQUE,
            "cheque_number": "000123",
            "cheque_date": date(2024, 12, 22),
            "status": PaymentStatusEnum.APPROVED,
        },
        # Customer Receipts
        {
            "type": PaymentType.CUSTOMER_RECEIPT,
            "party_type": PartyType.CUSTOMER,
            "party_code": "C005",
            "date": date(2024, 12, 19),
            "amount": Decimal("147500"),  # 125000 + 18% GST
            "mode": PaymentMode.NEFT,
            "reference": "UTR987654321",
            "status": PaymentStatusEnum.POSTED,
        },
        {
            "type": PaymentType.CUSTOMER_RECEIPT,
            "party_type": PartyType.CUSTOMER,
            "party_code": "C001",
            "date": date(2024, 12, 21),
            "amount": Decimal("100000"),
            "mode": PaymentMode.RTGS,
            "reference": "RTGS2024122100001",
            "status": PaymentStatusEnum.POSTED,
        },
        {
            "type": PaymentType.ADVANCE_RECEIPT,
            "party_type": PartyType.CUSTOMER,
            "party_code": "C002",
            "date": date(2024, 12, 23),
            "amount": Decimal("50000"),
            "mode": PaymentMode.UPI,
            "reference": "UPI/123456/DEC24",
            "status": PaymentStatusEnum.APPROVED,
        },
    ]

    payment_counter = 0
    for p_data in payments_data:
        payment_counter += 1
        payment_number = f"PAY-2024-{payment_counter:04d}"

        # Get party
        if p_data["party_type"] == PartyType.VENDOR:
            party = vendor_map.get(p_data["party_code"])
            party_name = party.name if party else None
            vendor_id = party.id if party else None
            customer_id = None
        else:
            party = customer_map.get(p_data["party_code"])
            party_name = party.name if party else None
            customer_id = party.id if party else None
            vendor_id = None

        if not party:
            continue

        payment = Payment(
            payment_number=payment_number,
            payment_date=p_data["date"],
            payment_type=p_data["type"],
            party_type=p_data["party_type"],
            vendor_id=vendor_id,
            customer_id=customer_id,
            organization_id=org.id,
            payment_mode=p_data["mode"],
            bank_account_id=bank_account.id if bank_account else None,
            amount=p_data["amount"],
            net_amount=p_data["amount"],
            reference_number=p_data.get("reference"),
            cheque_number=p_data.get("cheque_number"),
            cheque_date=p_data.get("cheque_date"),
            cheque_status=ChequeStatus.ISSUED if p_data.get("cheque_number") else None,
            status=p_data["status"],
            is_posted=p_data["status"] == PaymentStatusEnum.POSTED,
            created_by=admin_user.id,
        )
        session.add(payment)
        await session.flush()

        print(f"  + Created payment '{payment_number}' - {p_data['type'].value} - {party_name} - Rs.{p_data['amount']:,.2f}")

    await session.commit()
    print(f"Total payments: {payment_counter}")


async def main():
    """Run AP/AR seed data."""
    print("=" * 60)
    print("SMFC ERP - Seed AP/AR Data")
    print("=" * 60)

    async with async_session_factory() as session:
        # Get organization
        result = await session.execute(
            select(Organization).where(Organization.code == "SMFC")
        )
        org = result.scalar_one_or_none()
        if not org:
            print("ERROR: Organization not found. Run seed_data.py first.")
            return

        # Get admin user
        result = await session.execute(
            select(User).where(User.username == "krishna")
        )
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            print("ERROR: Admin user not found. Run seed_data.py first.")
            return

        # Get payment terms
        result = await session.execute(
            select(PaymentTerms).where(PaymentTerms.organization_id == org.id)
        )
        payment_terms_map = {pt.code: pt for pt in result.scalars().all()}

        # Get TDS sections
        result = await session.execute(select(TDSSection))
        tds_section_map = {ts.section_code: ts for ts in result.scalars().all()}

        # Get accounts
        result = await session.execute(
            select(Account).where(Account.organization_id == org.id)
        )
        account_map = {acc.code: acc for acc in result.scalars().all()}

        # Get GST rates
        result = await session.execute(select(GSTRate))
        gst_rate_map = {str(gr.id): gr for gr in result.scalars().all()}

        # Seed vendors
        vendor_map = await seed_vendors(session, org, payment_terms_map, tds_section_map, account_map)

        # Seed customers
        customer_map = await seed_customers(session, org, payment_terms_map, account_map)

        # Seed purchase bills
        await seed_purchase_bills(session, org, vendor_map, gst_rate_map, account_map, admin_user)

        # Seed sales invoices
        await seed_sales_invoices(session, org, customer_map, gst_rate_map, account_map, admin_user)

        # Seed payments
        await seed_payments(session, org, vendor_map, customer_map, account_map, admin_user)

    print("\n" + "=" * 60)
    print("AP/AR seed data completed successfully!")
    print("=" * 60)
    print("\nData Seeded:")
    print("  - Vendors: 5 sample vendors")
    print("  - Customers: 5 sample customers")
    print("  - Purchase Bills: 5 bills with various statuses")
    print("  - Sales Invoices: 5 invoices with various statuses")
    print("  - Payments: 5 payments/receipts")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
