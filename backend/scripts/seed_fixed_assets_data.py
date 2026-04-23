"""
Seed script for Fixed Assets module test data.
Creates all necessary master data and fixed assets using APIs.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    python scripts/seed_fixed_assets_data.py

Prerequisites:
    - Database must be running
    - Run `python scripts/seed_data.py` first to create permissions and roles
    - Run `python scripts/create_superuser.py` to create admin user
    - API server must be running at http://localhost:8000
"""

import asyncio
import httpx
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"

# Store created IDs
created_ids = {
    "organization_id": None,
    "financial_year_id": None,
    "units": {},
    "departments": {},
    "account_groups": {},
    "accounts": {},
    "asset_categories": {},
    "assets": [],
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
        print(f"Logged in as {username}")
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

    async def put(self, endpoint: str, data: dict) -> dict:
        """Make PUT request."""
        response = await self.client.put(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self._headers(),
        )
        if response.status_code >= 400:
            print(f"PUT {endpoint} failed: {response.status_code} - {response.text}")
            return None
        return response.json()


async def create_organization(client: APIClient) -> str:
    """Create test organization."""
    print("\n--- Creating Organization ---")

    # Check if organization already exists
    existing = await client.get("/organizations", {"skip": 0, "limit": 1})
    if existing and existing.get("items"):
        org_id = existing["items"][0]["id"]
        print(f"Using existing organization: {org_id}")
        return org_id

    org_data = {
        "code": "NBFC001",
        "name": "TalentFino NBFC Ltd",
        "legal_name": "TalentFino Non-Banking Financial Company Limited",
        "pan": "AAACT1234A",
        "tan": "DELT12345A",
        "gstin": "07AAACT1234A1Z5",
        "cin": "U65100DL2020PLC123456",
        "incorporation_date": "2020-04-01",
        "registered_address": "123 Finance Tower, Connaught Place",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "country": "India",
        "phone": "011-12345678",
        "email": "contact@talentfino.com",
        "website": "https://talentfino.com",
        "logo_url": None,
        "base_currency": "INR",
        "fiscal_year_start_month": 4,
    }

    result = await client.post("/organizations", org_data)
    if result:
        print(f"Created organization: {result['name']} (ID: {result['id']})")
        return result["id"]
    return None


async def create_units(client: APIClient, org_id: str) -> dict:
    """Create test units (locations)."""
    print("\n--- Creating Units (Locations) ---")

    units = {}

    # Check existing units
    existing = await client.get("/units", {"organization_id": org_id, "skip": 0, "limit": 100})
    if existing and existing.get("items"):
        for unit in existing["items"]:
            units[unit["code"]] = unit["id"]
            print(f"Using existing unit: {unit['name']} (ID: {unit['id']})")
        if len(units) >= 3:
            return units

    unit_data_list = [
        {
            "organization_id": org_id,
            "code": "HO",
            "name": "Head Office",
            "unit_type": "HEAD_OFFICE",
            "address": "123 Finance Tower, Connaught Place",
            "city": "New Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "phone": "011-12345678",
            "email": "ho@talentfino.com",
            "is_active": True,
        },
        {
            "organization_id": org_id,
            "code": "MUM",
            "name": "Mumbai Branch",
            "unit_type": "BRANCH",
            "address": "456 BKC Complex, Bandra Kurla",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400051",
            "phone": "022-98765432",
            "email": "mumbai@talentfino.com",
            "is_active": True,
        },
        {
            "organization_id": org_id,
            "code": "BLR",
            "name": "Bangalore Branch",
            "unit_type": "BRANCH",
            "address": "789 Tech Park, Whitefield",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560066",
            "phone": "080-11223344",
            "email": "bangalore@talentfino.com",
            "is_active": True,
        },
    ]

    for unit_data in unit_data_list:
        if unit_data["code"] not in units:
            result = await client.post("/units", unit_data)
            if result:
                units[unit_data["code"]] = result["id"]
                print(f"Created unit: {result['name']} (ID: {result['id']})")

    return units


async def create_departments(client: APIClient, org_id: str) -> dict:
    """Create test departments."""
    print("\n--- Creating Departments ---")

    departments = {}

    # Check existing departments
    existing = await client.get("/departments", {"organization_id": org_id, "skip": 0, "limit": 100})
    if existing and existing.get("items"):
        for dept in existing["items"]:
            departments[dept["code"]] = dept["id"]
            print(f"Using existing department: {dept['name']} (ID: {dept['id']})")
        if len(departments) >= 4:
            return departments

    dept_data_list = [
        {
            "organization_id": org_id,
            "code": "FIN",
            "name": "Finance",
            "description": "Finance and Accounts Department",
            "is_active": True,
        },
        {
            "organization_id": org_id,
            "code": "IT",
            "name": "Information Technology",
            "description": "IT and Systems Department",
            "is_active": True,
        },
        {
            "organization_id": org_id,
            "code": "OPS",
            "name": "Operations",
            "description": "Operations Department",
            "is_active": True,
        },
        {
            "organization_id": org_id,
            "code": "HR",
            "name": "Human Resources",
            "description": "Human Resources Department",
            "is_active": True,
        },
    ]

    for dept_data in dept_data_list:
        if dept_data["code"] not in departments:
            result = await client.post("/departments", dept_data)
            if result:
                departments[dept_data["code"]] = result["id"]
                print(f"Created department: {result['name']} (ID: {result['id']})")

    return departments


async def create_financial_year(client: APIClient, org_id: str) -> str:
    """Create financial year with periods."""
    print("\n--- Creating Financial Year ---")

    # Check existing financial years
    existing = await client.get("/financial-years", {"organization_id": org_id, "skip": 0, "limit": 10})
    if existing and existing.get("items"):
        for fy in existing["items"]:
            if fy.get("is_current"):
                print(f"Using existing financial year: {fy['name']} (ID: {fy['id']})")
                return fy["id"]
        # Use first one if no current
        fy_id = existing["items"][0]["id"]
        print(f"Using existing financial year: {existing['items'][0]['name']} (ID: {fy_id})")
        return fy_id

    # Create new financial year
    today = date.today()
    if today.month >= 4:
        fy_start = date(today.year, 4, 1)
        fy_end = date(today.year + 1, 3, 31)
        fy_code = f"FY{today.year}-{str(today.year + 1)[2:]}"
        fy_name = f"Financial Year {today.year}-{str(today.year + 1)[2:]}"
    else:
        fy_start = date(today.year - 1, 4, 1)
        fy_end = date(today.year, 3, 31)
        fy_code = f"FY{today.year - 1}-{str(today.year)[2:]}"
        fy_name = f"Financial Year {today.year - 1}-{str(today.year)[2:]}"

    fy_data = {
        "organization_id": org_id,
        "code": fy_code,
        "name": fy_name,
        "start_date": fy_start.isoformat(),
        "end_date": fy_end.isoformat(),
        "is_current": True,
    }

    result = await client.post("/financial-years", fy_data)
    if result:
        print(f"Created financial year: {result['name']} (ID: {result['id']})")
        return result["id"]
    return None


async def create_account_groups(client: APIClient, org_id: str) -> dict:
    """Create chart of accounts - account groups."""
    print("\n--- Creating Account Groups ---")

    groups = {}

    # Check existing groups
    existing = await client.get("/account-groups", {"organization_id": org_id, "skip": 0, "limit": 100})
    if existing and existing.get("items"):
        for group in existing["items"]:
            groups[group["code"]] = group["id"]
        if len(groups) >= 10:
            print(f"Using {len(groups)} existing account groups")
            return groups

    # Parent groups first
    parent_groups = [
        {"code": "ASSETS", "name": "Assets", "group_type": "ASSET", "nature": "DEBIT"},
        {"code": "LIABILITIES", "name": "Liabilities", "group_type": "LIABILITY", "nature": "CREDIT"},
        {"code": "INCOME", "name": "Income", "group_type": "INCOME", "nature": "CREDIT"},
        {"code": "EXPENSES", "name": "Expenses", "group_type": "EXPENSE", "nature": "DEBIT"},
    ]

    for grp in parent_groups:
        if grp["code"] not in groups:
            data = {
                "organization_id": org_id,
                "code": grp["code"],
                "name": grp["name"],
                "group_type": grp["group_type"],
                "nature": grp["nature"],
                "parent_group_id": None,
            }
            result = await client.post("/account-groups", data)
            if result:
                groups[grp["code"]] = result["id"]
                print(f"Created account group: {result['name']}")

    # Child groups
    child_groups = [
        {"code": "FIXED_ASSETS", "name": "Fixed Assets", "parent": "ASSETS", "group_type": "ASSET", "nature": "DEBIT"},
        {"code": "ACCUM_DEP", "name": "Accumulated Depreciation", "parent": "ASSETS", "group_type": "ASSET", "nature": "CREDIT"},
        {"code": "CURRENT_ASSETS", "name": "Current Assets", "parent": "ASSETS", "group_type": "ASSET", "nature": "DEBIT"},
        {"code": "CURRENT_LIAB", "name": "Current Liabilities", "parent": "LIABILITIES", "group_type": "LIABILITY", "nature": "CREDIT"},
        {"code": "SUNDRY_CRED", "name": "Sundry Creditors", "parent": "CURRENT_LIAB", "group_type": "LIABILITY", "nature": "CREDIT"},
        {"code": "DIRECT_EXP", "name": "Direct Expenses", "parent": "EXPENSES", "group_type": "EXPENSE", "nature": "DEBIT"},
        {"code": "INDIRECT_EXP", "name": "Indirect Expenses", "parent": "EXPENSES", "group_type": "EXPENSE", "nature": "DEBIT"},
        {"code": "OTHER_INCOME", "name": "Other Income", "parent": "INCOME", "group_type": "INCOME", "nature": "CREDIT"},
    ]

    for grp in child_groups:
        if grp["code"] not in groups and grp["parent"] in groups:
            data = {
                "organization_id": org_id,
                "code": grp["code"],
                "name": grp["name"],
                "group_type": grp["group_type"],
                "nature": grp["nature"],
                "parent_group_id": groups[grp["parent"]],
            }
            result = await client.post("/account-groups", data)
            if result:
                groups[grp["code"]] = result["id"]
                print(f"Created account group: {result['name']}")

    return groups


async def create_gl_accounts(client: APIClient, org_id: str, groups: dict) -> dict:
    """Create GL accounts for fixed assets."""
    print("\n--- Creating GL Accounts ---")

    accounts = {}

    # Check existing accounts
    existing = await client.get("/accounts", {"organization_id": org_id, "skip": 0, "limit": 200})
    if existing and existing.get("items"):
        for acc in existing["items"]:
            accounts[acc["code"]] = acc["id"]
        if len(accounts) >= 10:
            print(f"Using {len(accounts)} existing GL accounts")
            return accounts

    account_data_list = [
        # Fixed Asset Accounts
        {"code": "1100", "name": "Plant & Machinery", "group": "FIXED_ASSETS", "account_type": "ASSET"},
        {"code": "1110", "name": "Furniture & Fixtures", "group": "FIXED_ASSETS", "account_type": "ASSET"},
        {"code": "1120", "name": "Computers & Equipment", "group": "FIXED_ASSETS", "account_type": "ASSET"},
        {"code": "1130", "name": "Vehicles", "group": "FIXED_ASSETS", "account_type": "ASSET"},
        {"code": "1140", "name": "Office Equipment", "group": "FIXED_ASSETS", "account_type": "ASSET"},
        {"code": "1150", "name": "Leasehold Improvements", "group": "FIXED_ASSETS", "account_type": "ASSET"},
        # Accumulated Depreciation Accounts
        {"code": "1200", "name": "Accum Dep - Plant & Machinery", "group": "ACCUM_DEP", "account_type": "ASSET"},
        {"code": "1210", "name": "Accum Dep - Furniture & Fixtures", "group": "ACCUM_DEP", "account_type": "ASSET"},
        {"code": "1220", "name": "Accum Dep - Computers & Equipment", "group": "ACCUM_DEP", "account_type": "ASSET"},
        {"code": "1230", "name": "Accum Dep - Vehicles", "group": "ACCUM_DEP", "account_type": "ASSET"},
        {"code": "1240", "name": "Accum Dep - Office Equipment", "group": "ACCUM_DEP", "account_type": "ASSET"},
        {"code": "1250", "name": "Accum Dep - Leasehold Improvements", "group": "ACCUM_DEP", "account_type": "ASSET"},
        # Current Assets
        {"code": "1300", "name": "Cash in Hand", "group": "CURRENT_ASSETS", "account_type": "CASH"},
        {"code": "1310", "name": "Bank Account - HDFC", "group": "CURRENT_ASSETS", "account_type": "BANK"},
        # Expense Accounts
        {"code": "5100", "name": "Depreciation Expense", "group": "INDIRECT_EXP", "account_type": "EXPENSE"},
        {"code": "5110", "name": "Impairment Loss", "group": "INDIRECT_EXP", "account_type": "EXPENSE"},
        {"code": "5120", "name": "Loss on Disposal of Assets", "group": "INDIRECT_EXP", "account_type": "EXPENSE"},
        # Income Accounts
        {"code": "4100", "name": "Gain on Disposal of Assets", "group": "OTHER_INCOME", "account_type": "INCOME"},
        # Liability Accounts
        {"code": "2100", "name": "Sundry Creditors - Others", "group": "SUNDRY_CRED", "account_type": "LIABILITY"},
        {"code": "2110", "name": "Revaluation Reserve", "group": "CURRENT_LIAB", "account_type": "LIABILITY"},
    ]

    for acc_data in account_data_list:
        if acc_data["code"] not in accounts and acc_data["group"] in groups:
            data = {
                "organization_id": org_id,
                "code": acc_data["code"],
                "name": acc_data["name"],
                "account_group_id": groups[acc_data["group"]],
                "account_type": acc_data["account_type"],
                "currency_code": "INR",
                "is_active": True,
            }
            result = await client.post("/accounts", data)
            if result:
                accounts[acc_data["code"]] = result["id"]
                print(f"Created GL account: {acc_data['code']} - {acc_data['name']}")

    return accounts


async def create_asset_categories(client: APIClient, org_id: str, accounts: dict) -> dict:
    """Create asset categories."""
    print("\n--- Creating Asset Categories ---")

    categories = {}

    # Check existing categories
    existing = await client.get("/fixed-assets/categories", {"organization_id": org_id, "skip": 0, "limit": 50})
    if existing and existing.get("items"):
        for cat in existing["items"]:
            categories[cat["category_code"]] = cat["id"]
        if len(categories) >= 5:
            print(f"Using {len(categories)} existing asset categories")
            return categories

    category_data_list = [
        {
            "category_code": "PLANT",
            "category_name": "Plant & Machinery",
            "description": "Manufacturing and processing equipment",
            "asset_type": "TANGIBLE",
            "depreciation_method": "WDV",
            "useful_life_years": 15,
            "residual_value_pct": 5.0,
            "depreciation_rate_slm": 6.33,
            "depreciation_rate_wdv": 15.0,
            "it_act_rate": 15.0,
            "it_act_block": "III",
            "capitalization_threshold": 5000.0,
            "asset_account": "1100",
            "accum_dep_account": "1200",
            "dep_expense_account": "5100",
        },
        {
            "category_code": "FURN",
            "category_name": "Furniture & Fixtures",
            "description": "Office furniture and fixtures",
            "asset_type": "TANGIBLE",
            "depreciation_method": "SLM",
            "useful_life_years": 10,
            "residual_value_pct": 5.0,
            "depreciation_rate_slm": 10.0,
            "depreciation_rate_wdv": 25.0,
            "it_act_rate": 10.0,
            "it_act_block": "II",
            "capitalization_threshold": 5000.0,
            "asset_account": "1110",
            "accum_dep_account": "1210",
            "dep_expense_account": "5100",
        },
        {
            "category_code": "COMP",
            "category_name": "Computers & Equipment",
            "description": "Computers, servers, and IT equipment",
            "asset_type": "TANGIBLE",
            "depreciation_method": "WDV",
            "useful_life_years": 3,
            "residual_value_pct": 5.0,
            "depreciation_rate_slm": 33.33,
            "depreciation_rate_wdv": 40.0,
            "it_act_rate": 40.0,
            "it_act_block": "IIIA",
            "capitalization_threshold": 5000.0,
            "asset_account": "1120",
            "accum_dep_account": "1220",
            "dep_expense_account": "5100",
        },
        {
            "category_code": "VEH",
            "category_name": "Vehicles",
            "description": "Company vehicles",
            "asset_type": "TANGIBLE",
            "depreciation_method": "WDV",
            "useful_life_years": 8,
            "residual_value_pct": 10.0,
            "depreciation_rate_slm": 12.5,
            "depreciation_rate_wdv": 25.0,
            "it_act_rate": 15.0,
            "it_act_block": "III",
            "capitalization_threshold": 50000.0,
            "asset_account": "1130",
            "accum_dep_account": "1230",
            "dep_expense_account": "5100",
        },
        {
            "category_code": "OFFICE",
            "category_name": "Office Equipment",
            "description": "Office equipment and appliances",
            "asset_type": "TANGIBLE",
            "depreciation_method": "SLM",
            "useful_life_years": 5,
            "residual_value_pct": 5.0,
            "depreciation_rate_slm": 20.0,
            "depreciation_rate_wdv": 40.0,
            "it_act_rate": 15.0,
            "it_act_block": "III",
            "capitalization_threshold": 5000.0,
            "asset_account": "1140",
            "accum_dep_account": "1240",
            "dep_expense_account": "5100",
        },
        {
            "category_code": "LEASE",
            "category_name": "Leasehold Improvements",
            "description": "Improvements to leased premises",
            "asset_type": "TANGIBLE",
            "depreciation_method": "SLM",
            "useful_life_years": 10,
            "residual_value_pct": 0.0,
            "depreciation_rate_slm": 10.0,
            "depreciation_rate_wdv": 25.0,
            "it_act_rate": 10.0,
            "it_act_block": "II",
            "capitalization_threshold": 10000.0,
            "asset_account": "1150",
            "accum_dep_account": "1250",
            "dep_expense_account": "5100",
        },
    ]

    for cat_data in category_data_list:
        if cat_data["category_code"] not in categories:
            data = {
                "organization_id": org_id,
                "category_code": cat_data["category_code"],
                "category_name": cat_data["category_name"],
                "description": cat_data["description"],
                "asset_type": cat_data["asset_type"],
                "depreciation_method": cat_data["depreciation_method"],
                "useful_life_years": cat_data["useful_life_years"],
                "residual_value_pct": cat_data["residual_value_pct"],
                "depreciation_rate_slm": cat_data["depreciation_rate_slm"],
                "depreciation_rate_wdv": cat_data["depreciation_rate_wdv"],
                "it_act_rate": cat_data["it_act_rate"],
                "it_act_block": cat_data["it_act_block"],
                "capitalization_threshold": cat_data["capitalization_threshold"],
                "gl_asset_account_id": accounts.get(cat_data["asset_account"]),
                "gl_accum_dep_account_id": accounts.get(cat_data["accum_dep_account"]),
                "gl_dep_expense_account_id": accounts.get(cat_data["dep_expense_account"]),
                "gl_disposal_gain_account_id": accounts.get("4100"),
                "gl_disposal_loss_account_id": accounts.get("5120"),
                "gl_revaluation_reserve_account_id": accounts.get("2110"),
                "gl_impairment_account_id": accounts.get("5110"),
                "requires_insurance": cat_data["category_code"] in ["VEH", "PLANT"],
                "requires_amc": cat_data["category_code"] in ["COMP", "OFFICE"],
            }
            result = await client.post("/fixed-assets/categories", data)
            if result:
                categories[cat_data["category_code"]] = result["id"]
                print(f"Created asset category: {cat_data['category_name']}")

    return categories


async def create_fixed_assets(client: APIClient, org_id: str, categories: dict, units: dict, departments: dict) -> list:
    """Create fixed assets."""
    print("\n--- Creating Fixed Assets ---")

    assets = []
    today = date.today()

    # Check existing assets
    existing = await client.get("/fixed-assets/assets", {"organization_id": org_id, "skip": 0, "limit": 100})
    if existing and existing.get("items"):
        print(f"Found {len(existing['items'])} existing assets")
        return existing["items"]

    # Get first unit and department IDs
    ho_unit_id = units.get("HO") or list(units.values())[0] if units else None
    mum_unit_id = units.get("MUM") or ho_unit_id
    blr_unit_id = units.get("BLR") or ho_unit_id

    fin_dept_id = departments.get("FIN") or list(departments.values())[0] if departments else None
    it_dept_id = departments.get("IT") or fin_dept_id
    ops_dept_id = departments.get("OPS") or fin_dept_id

    asset_data_list = [
        # Computers
        {
            "asset_name": "Dell PowerEdge Server R750",
            "description": "Primary application server for core banking",
            "category": "COMP",
            "location": ho_unit_id,
            "department": it_dept_id,
            "acquisition_cost": 850000.0,
            "acquisition_date": (today - timedelta(days=180)).isoformat(),
            "make": "Dell",
            "model": "PowerEdge R750",
            "serial_number": "DELL-R750-001",
        },
        {
            "asset_name": "HP ProLiant DL380 Server",
            "description": "Database server",
            "category": "COMP",
            "location": ho_unit_id,
            "department": it_dept_id,
            "acquisition_cost": 720000.0,
            "acquisition_date": (today - timedelta(days=120)).isoformat(),
            "make": "HP",
            "model": "ProLiant DL380 Gen10",
            "serial_number": "HP-DL380-001",
        },
        {
            "asset_name": "MacBook Pro 16-inch",
            "description": "Development laptop",
            "category": "COMP",
            "location": mum_unit_id,
            "department": it_dept_id,
            "acquisition_cost": 249900.0,
            "acquisition_date": (today - timedelta(days=90)).isoformat(),
            "make": "Apple",
            "model": "MacBook Pro 16-inch M3 Max",
            "serial_number": "MBP-M3-001",
        },
        # Furniture
        {
            "asset_name": "Executive Office Desks (Set of 10)",
            "description": "Executive office furniture for management floor",
            "category": "FURN",
            "location": ho_unit_id,
            "department": ops_dept_id,
            "acquisition_cost": 450000.0,
            "acquisition_date": (today - timedelta(days=365)).isoformat(),
            "make": "Godrej",
            "model": "Executive Series",
            "serial_number": "GODR-EXEC-001",
        },
        {
            "asset_name": "Conference Room Furniture Set",
            "description": "Board room table and chairs",
            "category": "FURN",
            "location": ho_unit_id,
            "department": ops_dept_id,
            "acquisition_cost": 380000.0,
            "acquisition_date": (today - timedelta(days=300)).isoformat(),
            "make": "Featherlite",
            "model": "Premium Conference",
            "serial_number": "FTH-CONF-001",
        },
        # Vehicles
        {
            "asset_name": "Toyota Fortuner",
            "description": "Executive vehicle for MD",
            "category": "VEH",
            "location": ho_unit_id,
            "department": ops_dept_id,
            "acquisition_cost": 4500000.0,
            "acquisition_date": (today - timedelta(days=400)).isoformat(),
            "make": "Toyota",
            "model": "Fortuner 4x4",
            "serial_number": "TYT-FORT-001",
        },
        {
            "asset_name": "Maruti Swift Dzire",
            "description": "Staff vehicle for Mumbai office",
            "category": "VEH",
            "location": mum_unit_id,
            "department": ops_dept_id,
            "acquisition_cost": 850000.0,
            "acquisition_date": (today - timedelta(days=200)).isoformat(),
            "make": "Maruti Suzuki",
            "model": "Swift Dzire ZXI+",
            "serial_number": "MSZ-DZR-001",
        },
        # Office Equipment
        {
            "asset_name": "Xerox WorkCentre 7855",
            "description": "Multi-function printer/copier",
            "category": "OFFICE",
            "location": ho_unit_id,
            "department": ops_dept_id,
            "acquisition_cost": 450000.0,
            "acquisition_date": (today - timedelta(days=250)).isoformat(),
            "make": "Xerox",
            "model": "WorkCentre 7855",
            "serial_number": "XRX-WC7855-001",
        },
        {
            "asset_name": "Cisco Catalyst 9300 Switch",
            "description": "Core network switch",
            "category": "OFFICE",
            "location": ho_unit_id,
            "department": it_dept_id,
            "acquisition_cost": 280000.0,
            "acquisition_date": (today - timedelta(days=180)).isoformat(),
            "make": "Cisco",
            "model": "Catalyst 9300-48P",
            "serial_number": "CISCO-C9300-001",
        },
        # Plant & Machinery
        {
            "asset_name": "UPS System 100KVA",
            "description": "Uninterrupted power supply for data center",
            "category": "PLANT",
            "location": ho_unit_id,
            "department": it_dept_id,
            "acquisition_cost": 1200000.0,
            "acquisition_date": (today - timedelta(days=500)).isoformat(),
            "make": "APC",
            "model": "Symmetra PX 100KVA",
            "serial_number": "APC-PX100-001",
        },
        {
            "asset_name": "Precision AC System",
            "description": "Data center cooling system",
            "category": "PLANT",
            "location": ho_unit_id,
            "department": it_dept_id,
            "acquisition_cost": 850000.0,
            "acquisition_date": (today - timedelta(days=450)).isoformat(),
            "make": "Daikin",
            "model": "Precision AC 20TR",
            "serial_number": "DAK-PAC-001",
        },
        # Leasehold Improvements
        {
            "asset_name": "Office Renovation - HO",
            "description": "Interior renovation of head office",
            "category": "LEASE",
            "location": ho_unit_id,
            "department": ops_dept_id,
            "acquisition_cost": 2500000.0,
            "acquisition_date": (today - timedelta(days=600)).isoformat(),
            "make": "N/A",
            "model": "N/A",
            "serial_number": "RENO-HO-001",
        },
    ]

    for asset_data in asset_data_list:
        category_id = categories.get(asset_data["category"])
        if not category_id:
            print(f"Skipping {asset_data['asset_name']} - category not found")
            continue

        data = {
            "organization_id": org_id,
            "category_id": category_id,
            "asset_name": asset_data["asset_name"],
            "description": asset_data["description"],
            "location_id": asset_data["location"],
            "department_id": asset_data["department"],
            "acquisition_date": asset_data["acquisition_date"],
            "acquisition_cost": asset_data["acquisition_cost"],
            "installation_cost": 0.0,
            "other_costs": 0.0,
            "make": asset_data["make"],
            "model": asset_data["model"],
            "serial_number": asset_data["serial_number"],
        }

        result = await client.post("/fixed-assets/assets", data)
        if result:
            assets.append(result)
            print(f"Created asset: {asset_data['asset_name']} (Code: {result.get('asset_code', 'N/A')})")

    return assets


async def capitalize_assets(client: APIClient, assets: list) -> None:
    """Capitalize draft assets."""
    print("\n--- Capitalizing Assets ---")

    today = date.today()

    for asset in assets:
        if asset.get("status") == "DRAFT":
            asset_id = asset["id"]
            acq_date = asset.get("acquisition_date", today.isoformat())

            data = {
                "capitalization_date": acq_date,
                "put_to_use_date": acq_date,
                "depreciation_start_date": acq_date,
            }

            result = await client.post(f"/fixed-assets/assets/{asset_id}/capitalize", data)
            if result:
                print(f"Capitalized: {asset['asset_name']} -> ACTIVE")


async def run_depreciation(client: APIClient, org_id: str) -> None:
    """Run depreciation for current period."""
    print("\n--- Running Depreciation ---")

    today = date.today()

    # Get first day of current month
    period_from = date(today.year, today.month, 1)

    # Get last day of current month
    if today.month == 12:
        period_to = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        period_to = date(today.year, today.month + 1, 1) - timedelta(days=1)

    dep_period = today.strftime("%Y-%m")

    data = {
        "organization_id": org_id,
        "depreciation_period": dep_period,
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "remarks": "Monthly depreciation run",
    }

    result = await client.post("/fixed-assets/depreciation/run", data)
    if result:
        print(f"Depreciation run completed: {result.get('total_assets', 0)} assets processed")
        print(f"Total depreciation: {result.get('total_depreciation', 0)}")

        # Post the depreciation run
        run_id = result.get("id")
        if run_id and result.get("status") == "COMPLETED":
            post_result = await client.post(f"/fixed-assets/depreciation/runs/{run_id}/post", {})
            if post_result:
                print(f"Depreciation run posted to GL")


async def main():
    """Main function to seed all test data."""
    print("=" * 60)
    print("Fixed Assets Module - Test Data Seeding")
    print("=" * 60)

    client = APIClient(BASE_URL)

    try:
        # Step 1: Login
        await client.login(ADMIN_USERNAME, ADMIN_PASSWORD)

        # Step 2: Create Organization
        org_id = await create_organization(client)
        if not org_id:
            print("Failed to create organization. Exiting.")
            return
        created_ids["organization_id"] = org_id

        # Step 3: Create Units (Locations)
        units = await create_units(client, org_id)
        created_ids["units"] = units

        # Step 4: Create Departments
        departments = await create_departments(client, org_id)
        created_ids["departments"] = departments

        # Step 5: Create Financial Year
        fy_id = await create_financial_year(client, org_id)
        if not fy_id:
            print("Failed to create financial year. Exiting.")
            return
        created_ids["financial_year_id"] = fy_id

        # Step 6: Create Account Groups
        groups = await create_account_groups(client, org_id)
        created_ids["account_groups"] = groups

        # Step 7: Create GL Accounts
        accounts = await create_gl_accounts(client, org_id, groups)
        created_ids["accounts"] = accounts

        # Step 8: Create Asset Categories
        categories = await create_asset_categories(client, org_id, accounts)
        created_ids["asset_categories"] = categories

        # Step 9: Create Fixed Assets
        assets = await create_fixed_assets(client, org_id, categories, units, departments)
        created_ids["assets"] = assets

        # Step 10: Capitalize Assets
        await capitalize_assets(client, assets)

        # Step 11: Run Depreciation
        await run_depreciation(client, org_id)

        print("\n" + "=" * 60)
        print("Test Data Seeding Complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Organization: {org_id}")
        print(f"  Units: {len(units)}")
        print(f"  Departments: {len(departments)}")
        print(f"  Financial Year: {fy_id}")
        print(f"  Account Groups: {len(groups)}")
        print(f"  GL Accounts: {len(accounts)}")
        print(f"  Asset Categories: {len(categories)}")
        print(f"  Fixed Assets: {len(assets)}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
