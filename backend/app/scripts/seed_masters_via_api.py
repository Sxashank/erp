"""
Seed master data via API endpoints.

This script creates sample master data by calling the REST API endpoints.
It's designed to be run after the system is up and running with authentication.

Usage:
    python -m app.scripts.seed_masters_via_api --base-url http://localhost:8000 --username admin --password adminpass123

Requirements:
    - httpx (pip install httpx)
    - The API server must be running
    - A user with admin permissions must exist
"""

import argparse
import asyncio
import sys
from typing import Optional
from decimal import Decimal

import httpx


class APIClient:
    """HTTP client for interacting with the ERP API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def login(self, username: str, password: str) -> bool:
        """Login and get access token."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                print(f"Logged in successfully as {username}")
                return True
            else:
                print(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    @property
    def headers(self) -> dict:
        """Get request headers with auth token."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request."""
        response = await self.client.get(
            f"{self.base_url}/api/v1{endpoint}",
            headers=self.headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: dict) -> dict:
        """Make POST request."""
        response = await self.client.post(
            f"{self.base_url}/api/v1{endpoint}",
            headers=self.headers,
            json=data,
        )
        if response.status_code >= 400:
            print(f"POST {endpoint} failed: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def seed_organization(client: APIClient) -> str:
    """Create a sample organization and return its ID."""
    print("\n--- Creating Organization ---")

    org_data = {
        "code": "SMFC",
        "name": "SMFC Finance Limited",
        "legal_name": "SMFC Finance Private Limited",
        "short_name": "SMFC",
        "description": "A leading NBFC providing financial services",
        "cin": "U65100MH2020PTC123456",
        "pan": "AABCS1234F",
        "tan": "MUMS12345E",
        "gstin": "27AABCS1234F1ZV",
        "rbi_registration": "N-13.00123",
        "reg_address_line1": "123 Finance Tower",
        "reg_address_line2": "Nariman Point",
        "reg_city": "Mumbai",
        "reg_district": "Mumbai",
        "reg_state_code": "27",
        "reg_pincode": "400021",
        "reg_country": "IN",
        "phone": "+91-22-12345678",
        "email": "info@smfc.com",
        "website": "https://www.smfc.com",
        "base_currency": "INR",
        "financial_year_start_month": 4,
    }

    try:
        # Check if organization already exists
        orgs = await client.get("/organizations")
        for org in orgs.get("items", []):
            if org["code"] == org_data["code"]:
                print(f"Organization '{org_data['code']}' already exists")
                return org["id"]

        result = await client.post("/organizations", org_data)
        org_id = result["id"]
        print(f"Created organization: {org_data['name']} (ID: {org_id})")
        return org_id
    except Exception as e:
        print(f"Error creating organization: {e}")
        raise


async def seed_bank_accounts(client: APIClient, org_id: str):
    """Create sample bank accounts for the organization."""
    print("\n--- Creating Bank Accounts ---")

    bank_accounts = [
        {
            "account_name": "Main Current Account",
            "account_number": "123456789012",
            "ifsc_code": "HDFC0000001",
            "bank_name": "HDFC Bank",
            "branch_name": "Fort Branch, Mumbai",
            "account_type": "CURRENT",
            "is_primary": True,
            "allow_payments": True,
            "allow_receipts": True,
        },
        {
            "account_name": "Cash Credit Account",
            "account_number": "987654321098",
            "ifsc_code": "SBIN0001234",
            "bank_name": "State Bank of India",
            "branch_name": "Nariman Point, Mumbai",
            "account_type": "CC",
            "sanctioned_limit": 50000000.00,  # 5 Cr
            "drawing_power": 45000000.00,  # 4.5 Cr
            "is_primary": False,
            "allow_payments": True,
            "allow_receipts": True,
        },
        {
            "account_name": "Collections Account",
            "account_number": "456789012345",
            "ifsc_code": "ICIC0000123",
            "bank_name": "ICICI Bank",
            "branch_name": "BKC, Mumbai",
            "account_type": "CURRENT",
            "is_primary": False,
            "allow_payments": False,
            "allow_receipts": True,
        },
    ]

    for account in bank_accounts:
        try:
            result = await client.post(
                f"/organizations/{org_id}/bank-accounts", account
            )
            print(f"Created bank account: {account['account_name']}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [400, 409]:
                print(f"Bank account '{account['account_name']}' may already exist")
            else:
                raise


async def seed_addresses(client: APIClient, org_id: str):
    """Create sample addresses for the organization."""
    print("\n--- Creating Addresses ---")

    addresses = [
        {
            "address_type": "REGISTERED",
            "address_line1": "123 Finance Tower",
            "address_line2": "Nariman Point",
            "city": "Mumbai",
            "district": "Mumbai",
            "state_code": "27",
            "pincode": "400021",
            "country": "IN",
            "is_primary": True,
        },
        {
            "address_type": "CORPORATE",
            "address_line1": "456 Business Hub",
            "address_line2": "BKC",
            "landmark": "Near Jio World Centre",
            "city": "Mumbai",
            "district": "Mumbai Suburban",
            "state_code": "27",
            "pincode": "400051",
            "country": "IN",
            "latitude": 19.0596,
            "longitude": 72.8656,
            "is_primary": False,
        },
        {
            "address_type": "BRANCH",
            "address_line1": "789 Commercial Complex",
            "address_line2": "MG Road",
            "city": "Pune",
            "district": "Pune",
            "state_code": "27",
            "pincode": "411001",
            "country": "IN",
            "is_primary": False,
        },
    ]

    for address in addresses:
        try:
            result = await client.post(f"/organizations/{org_id}/addresses", address)
            print(
                f"Created address: {address['address_type']} - {address['city']}"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [400, 409]:
                print(
                    f"Address '{address['address_type']}' may already exist"
                )
            else:
                raise


async def seed_departments(client: APIClient, org_id: str) -> dict:
    """Create sample departments and return their IDs."""
    print("\n--- Creating Departments ---")

    departments = [
        {
            "code": "CORP",
            "name": "Corporate Office",
            "short_name": "Corp",
            "description": "Head office corporate functions",
            "organization_id": org_id,
            "cost_center_code": "CC-CORP",
        },
        {
            "code": "FIN",
            "name": "Finance & Accounts",
            "short_name": "Finance",
            "description": "Finance, accounts, and treasury",
            "organization_id": org_id,
            "cost_center_code": "CC-FIN",
        },
        {
            "code": "CREDIT",
            "name": "Credit & Underwriting",
            "short_name": "Credit",
            "description": "Loan origination and credit assessment",
            "organization_id": org_id,
            "cost_center_code": "CC-CREDIT",
        },
        {
            "code": "OPS",
            "name": "Operations",
            "short_name": "Ops",
            "description": "Loan operations and disbursements",
            "organization_id": org_id,
            "cost_center_code": "CC-OPS",
        },
        {
            "code": "COLL",
            "name": "Collections",
            "short_name": "Collections",
            "description": "Loan collections and recovery",
            "organization_id": org_id,
            "cost_center_code": "CC-COLL",
        },
        {
            "code": "LEGAL",
            "name": "Legal",
            "short_name": "Legal",
            "description": "Legal and compliance",
            "organization_id": org_id,
            "cost_center_code": "CC-LEGAL",
        },
        {
            "code": "IT",
            "name": "Information Technology",
            "short_name": "IT",
            "description": "IT infrastructure and development",
            "organization_id": org_id,
            "cost_center_code": "CC-IT",
        },
        {
            "code": "HR",
            "name": "Human Resources",
            "short_name": "HR",
            "description": "Human resources and administration",
            "organization_id": org_id,
            "cost_center_code": "CC-HR",
        },
    ]

    dept_ids = {}
    for dept in departments:
        try:
            # Check if department already exists
            depts_response = await client.get(
                "/departments", {"organization_id": org_id}
            )
            existing = next(
                (d for d in depts_response.get("items", []) if d["code"] == dept["code"]),
                None,
            )
            if existing:
                dept_ids[dept["code"]] = existing["id"]
                print(f"Department '{dept['code']}' already exists")
                continue

            result = await client.post("/departments", dept)
            dept_ids[dept["code"]] = result["id"]
            print(f"Created department: {dept['name']}")
        except httpx.HTTPStatusError as e:
            print(f"Error creating department {dept['code']}: {e}")

    return dept_ids


async def seed_designations(client: APIClient, dept_ids: dict):
    """Create sample designations."""
    print("\n--- Creating Designations ---")

    designations = [
        # Corporate
        {
            "code": "MD",
            "name": "Managing Director",
            "level": 1,
            "approval_limit": 100000000.00,  # 10 Cr
        },
        {
            "code": "ED",
            "name": "Executive Director",
            "level": 2,
            "approval_limit": 50000000.00,  # 5 Cr
        },
        # Finance
        {
            "code": "CFO",
            "name": "Chief Financial Officer",
            "level": 2,
            "department_id": dept_ids.get("FIN"),
            "approval_limit": 50000000.00,
        },
        {
            "code": "FM",
            "name": "Finance Manager",
            "level": 4,
            "department_id": dept_ids.get("FIN"),
            "approval_limit": 5000000.00,
        },
        {
            "code": "SR_ACC",
            "name": "Senior Accountant",
            "level": 5,
            "department_id": dept_ids.get("FIN"),
            "approval_limit": 500000.00,
        },
        {
            "code": "ACC",
            "name": "Accountant",
            "level": 6,
            "department_id": dept_ids.get("FIN"),
        },
        # Credit
        {
            "code": "CCO",
            "name": "Chief Credit Officer",
            "level": 2,
            "department_id": dept_ids.get("CREDIT"),
            "approval_limit": 100000000.00,
        },
        {
            "code": "GM_CREDIT",
            "name": "General Manager - Credit",
            "level": 3,
            "department_id": dept_ids.get("CREDIT"),
            "approval_limit": 50000000.00,
        },
        {
            "code": "AGM_CREDIT",
            "name": "Assistant General Manager - Credit",
            "level": 4,
            "department_id": dept_ids.get("CREDIT"),
            "approval_limit": 10000000.00,
        },
        {
            "code": "CM",
            "name": "Credit Manager",
            "level": 5,
            "department_id": dept_ids.get("CREDIT"),
            "approval_limit": 2500000.00,
        },
        {
            "code": "CO",
            "name": "Credit Officer",
            "level": 6,
            "department_id": dept_ids.get("CREDIT"),
            "approval_limit": 500000.00,
        },
        {
            "code": "CA",
            "name": "Credit Analyst",
            "level": 6,
            "department_id": dept_ids.get("CREDIT"),
        },
        # Operations
        {
            "code": "COO",
            "name": "Chief Operations Officer",
            "level": 2,
            "department_id": dept_ids.get("OPS"),
            "approval_limit": 50000000.00,
        },
        {
            "code": "OM",
            "name": "Operations Manager",
            "level": 4,
            "department_id": dept_ids.get("OPS"),
            "approval_limit": 5000000.00,
        },
        {
            "code": "OPS_EXEC",
            "name": "Operations Executive",
            "level": 6,
            "department_id": dept_ids.get("OPS"),
        },
        # Collections
        {
            "code": "COLL_HEAD",
            "name": "Head - Collections",
            "level": 3,
            "department_id": dept_ids.get("COLL"),
            "approval_limit": 10000000.00,
        },
        {
            "code": "COLL_MGR",
            "name": "Collections Manager",
            "level": 5,
            "department_id": dept_ids.get("COLL"),
            "approval_limit": 2500000.00,
        },
        {
            "code": "COLL_EXEC",
            "name": "Collections Executive",
            "level": 6,
            "department_id": dept_ids.get("COLL"),
        },
        # Legal
        {
            "code": "LEGAL_HEAD",
            "name": "Head - Legal",
            "level": 3,
            "department_id": dept_ids.get("LEGAL"),
        },
        {
            "code": "LEGAL_MGR",
            "name": "Legal Manager",
            "level": 5,
            "department_id": dept_ids.get("LEGAL"),
        },
        # IT
        {
            "code": "CTO",
            "name": "Chief Technology Officer",
            "level": 2,
            "department_id": dept_ids.get("IT"),
        },
        {
            "code": "IT_MGR",
            "name": "IT Manager",
            "level": 4,
            "department_id": dept_ids.get("IT"),
        },
        # HR
        {
            "code": "HR_HEAD",
            "name": "Head - Human Resources",
            "level": 3,
            "department_id": dept_ids.get("HR"),
        },
        {
            "code": "HR_MGR",
            "name": "HR Manager",
            "level": 5,
            "department_id": dept_ids.get("HR"),
        },
    ]

    for desig in designations:
        try:
            # Check if designation already exists
            desigs_response = await client.get("/designations")
            existing = next(
                (d for d in desigs_response.get("items", []) if d["code"] == desig["code"]),
                None,
            )
            if existing:
                print(f"Designation '{desig['code']}' already exists")
                continue

            result = await client.post("/designations", desig)
            print(f"Created designation: {desig['name']}")
        except httpx.HTTPStatusError as e:
            print(f"Error creating designation {desig['code']}: {e}")


async def seed_units(client: APIClient, org_id: str):
    """Create sample units/branches."""
    print("\n--- Creating Units ---")

    units = [
        {
            "code": "HO",
            "name": "Head Office",
            "short_name": "HO",
            "description": "Corporate Head Office",
            "unit_type": "HEAD_OFFICE",
            "organization_id": org_id,
            "is_head_office": True,
            "is_separate_accounting": True,
            "gstin": "27AABCS1234F1ZV",
            "gst_state_code": "27",
            "address_line1": "123 Finance Tower",
            "address_line2": "Nariman Point",
            "city": "Mumbai",
            "state_code": "27",
            "pincode": "400021",
        },
        {
            "code": "MUM-01",
            "name": "Mumbai Branch",
            "short_name": "Mumbai",
            "description": "Mumbai Main Branch",
            "unit_type": "BRANCH",
            "organization_id": org_id,
            "is_head_office": False,
            "is_separate_accounting": False,
            "address_line1": "456 Commercial Complex",
            "address_line2": "Andheri East",
            "city": "Mumbai",
            "state_code": "27",
            "pincode": "400069",
        },
        {
            "code": "PUN-01",
            "name": "Pune Branch",
            "short_name": "Pune",
            "description": "Pune Main Branch",
            "unit_type": "BRANCH",
            "organization_id": org_id,
            "is_head_office": False,
            "is_separate_accounting": False,
            "address_line1": "789 Tech Park",
            "address_line2": "Hinjewadi",
            "city": "Pune",
            "state_code": "27",
            "pincode": "411057",
        },
        {
            "code": "DEL-01",
            "name": "Delhi Branch",
            "short_name": "Delhi",
            "description": "Delhi NCR Branch",
            "unit_type": "BRANCH",
            "organization_id": org_id,
            "is_head_office": False,
            "is_separate_accounting": True,
            "gstin": "07AABCS1234F1ZT",
            "gst_state_code": "07",
            "address_line1": "101 Business Centre",
            "address_line2": "Connaught Place",
            "city": "New Delhi",
            "state_code": "07",
            "pincode": "110001",
        },
    ]

    for unit in units:
        try:
            # Check if unit already exists
            units_response = await client.get("/units", {"organization_id": org_id})
            existing = next(
                (u for u in units_response.get("items", []) if u["code"] == unit["code"]),
                None,
            )
            if existing:
                print(f"Unit '{unit['code']}' already exists")
                continue

            result = await client.post("/units", unit)
            print(f"Created unit: {unit['name']}")
        except httpx.HTTPStatusError as e:
            print(f"Error creating unit {unit['code']}: {e}")


async def main():
    """Main entry point for seeding master data via API."""
    parser = argparse.ArgumentParser(
        description="Seed master data via API endpoints"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Username for API authentication (default: admin)",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Password for API authentication",
    )
    parser.add_argument(
        "--skip-org",
        action="store_true",
        help="Skip organization creation (use existing)",
    )

    args = parser.parse_args()

    client = APIClient(args.base_url)

    try:
        # Login
        if not await client.login(args.username, args.password):
            print("Failed to login. Please check credentials.")
            sys.exit(1)

        # Create organization (or get existing)
        if args.skip_org:
            orgs = await client.get("/organizations")
            if orgs.get("items"):
                org_id = orgs["items"][0]["id"]
                print(f"Using existing organization: {org_id}")
            else:
                print("No existing organization found. Run without --skip-org")
                sys.exit(1)
        else:
            org_id = await seed_organization(client)

        # Seed related data
        await seed_bank_accounts(client, org_id)
        await seed_addresses(client, org_id)
        await seed_units(client, org_id)
        dept_ids = await seed_departments(client, org_id)
        await seed_designations(client, dept_ids)

        print("\n" + "=" * 50)
        print("Master data seeding complete!")
        print("=" * 50)

    except Exception as e:
        print(f"\nError during seeding: {e}")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
