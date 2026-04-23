"""CERSAI API Client.

Implements CERSAI API for:
- Security Interest Registration (Form I)
- Security Interest Modification (Form II)
- Security Interest Satisfaction (Form III)
- Asset Search
"""

import hashlib
import hmac
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """CERSAI transaction types."""
    REGISTRATION = "SI_REGISTRATION"  # Form I
    MODIFICATION = "SI_MODIFICATION"  # Form II
    SATISFACTION = "SI_SATISFACTION"  # Form III
    ASSET_SEARCH = "ASSET_SEARCH"


class AssetType(str, Enum):
    """CERSAI asset types."""
    # Immovable Property
    IMMOVABLE_RESIDENTIAL = "IMM_RES"
    IMMOVABLE_COMMERCIAL = "IMM_COM"
    IMMOVABLE_INDUSTRIAL = "IMM_IND"
    IMMOVABLE_AGRICULTURAL = "IMM_AGR"
    IMMOVABLE_PLOT = "IMM_PLT"

    # Movable Assets
    MOVABLE_VEHICLE = "MOV_VEH"
    MOVABLE_MACHINERY = "MOV_MAC"
    MOVABLE_STOCK = "MOV_STK"
    MOVABLE_RECEIVABLES = "MOV_RCV"
    MOVABLE_INTANGIBLE = "MOV_INT"


class RegistrationStatus(str, Enum):
    """Registration status."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PROCESSING = "PROCESSING"
    REGISTERED = "REGISTERED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    SATISFIED = "SATISFIED"


@dataclass
class Borrower:
    """Borrower details for CERSAI."""
    name: str
    pan: Optional[str] = None
    aadhaar: Optional[str] = None
    cin: Optional[str] = None  # For companies
    address: Optional[str] = None
    state_code: Optional[str] = None
    pin_code: Optional[str] = None
    entity_type: str = "INDIVIDUAL"  # INDIVIDUAL, COMPANY, LLP, PARTNERSHIP


@dataclass
class Asset:
    """Asset details for CERSAI registration."""
    asset_type: AssetType
    description: str
    # For immovable property
    property_address: Optional[str] = None
    survey_number: Optional[str] = None
    khata_number: Optional[str] = None
    plot_area: Optional[Decimal] = None
    plot_area_unit: str = "SQFT"
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    pin_code: Optional[str] = None
    # For movable assets
    registration_number: Optional[str] = None  # Vehicle
    serial_number: Optional[str] = None  # Machinery
    # Valuation
    market_value: Optional[Decimal] = None
    valuation_date: Optional[date] = None


@dataclass
class RegistrationRequest:
    """Security interest registration request."""
    # Loan details
    loan_account_number: str
    sanction_date: date
    disbursement_date: Optional[date] = None
    sanction_amount: Decimal = Decimal("0")
    outstanding_amount: Decimal = Decimal("0")
    interest_rate: Optional[Decimal] = None
    tenure_months: Optional[int] = None

    # Borrower(s)
    borrowers: List[Borrower] = field(default_factory=list)

    # Assets
    assets: List[Asset] = field(default_factory=list)

    # Security details
    security_interest_type: str = "HYPOTHECATION"  # MORTGAGE, PLEDGE, HYPOTHECATION
    date_of_creation: Optional[date] = None

    # Metadata
    organization_id: Optional[UUID] = None
    loan_account_id: Optional[UUID] = None

    # CERSAI specific
    priority: int = 1  # Priority of charge
    cersai_reference: Optional[str] = None  # For modification/satisfaction


@dataclass
class RegistrationResponse:
    """CERSAI registration response."""
    success: bool
    transaction_type: TransactionType = TransactionType.REGISTRATION
    cersai_reference: Optional[str] = None
    registration_number: Optional[str] = None
    status: RegistrationStatus = RegistrationStatus.DRAFT
    registration_date: Optional[date] = None
    payment_reference: Optional[str] = None
    fee_amount: Optional[Decimal] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchRequest:
    """Asset search request."""
    # Search by borrower
    borrower_pan: Optional[str] = None
    borrower_aadhaar: Optional[str] = None
    borrower_cin: Optional[str] = None
    borrower_name: Optional[str] = None

    # Search by asset
    asset_type: Optional[AssetType] = None
    property_address: Optional[str] = None
    survey_number: Optional[str] = None
    vehicle_registration: Optional[str] = None

    # Search by registration
    cersai_reference: Optional[str] = None


@dataclass
class SearchResponse:
    """CERSAI search response."""
    success: bool
    records: List[Dict[str, Any]] = field(default_factory=list)
    total_records: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class CersaiError(Exception):
    """CERSAI API error."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class CersaiClient:
    """
    CERSAI API Client.

    Implements the CERSAI web service API for:
    - Form I: Registration of security interest
    - Form II: Modification of security interest
    - Form III: Satisfaction of security interest
    - Asset search
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize CERSAI client."""
        self.config = config
        self._validate_config()
        self.base_url = config.get(
            "base_url", "https://cersai.org.in/api/v1"
        )

    def _validate_config(self) -> None:
        """Validate configuration."""
        required = ["entity_id", "api_key", "api_secret"]
        for key in required:
            if key not in self.config:
                raise CersaiError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                )

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        timestamp = datetime.utcnow().isoformat()
        signature = self._generate_signature(timestamp)

        return {
            "Content-Type": "application/json",
            "X-Entity-ID": self.config["entity_id"],
            "X-API-Key": self.config["api_key"],
            "X-Timestamp": timestamp,
            "X-Signature": signature,
        }

    def _generate_signature(self, timestamp: str) -> str:
        """Generate request signature."""
        message = f"{self.config['entity_id']}|{timestamp}"
        return hmac.new(
            self.config["api_secret"].encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def register_security_interest(
        self, request: RegistrationRequest
    ) -> RegistrationResponse:
        """
        Register security interest (Form I).

        This registers a new security interest with CERSAI.
        """
        payload = self._build_registration_payload(request)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/si/register",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if response.status_code == 200 and data.get("success"):
                    return RegistrationResponse(
                        success=True,
                        transaction_type=TransactionType.REGISTRATION,
                        cersai_reference=data.get("cersaiReference"),
                        registration_number=data.get("registrationNumber"),
                        status=RegistrationStatus(
                            data.get("status", "SUBMITTED")
                        ),
                        registration_date=datetime.strptime(
                            data["registrationDate"], "%Y-%m-%d"
                        ).date()
                        if data.get("registrationDate")
                        else None,
                        payment_reference=data.get("paymentReference"),
                        fee_amount=Decimal(data["feeAmount"])
                        if data.get("feeAmount")
                        else None,
                        metadata=data.get("metadata", {}),
                    )
                else:
                    return RegistrationResponse(
                        success=False,
                        status=RegistrationStatus.REJECTED,
                        error_code=data.get("error", {}).get("code"),
                        error_message=data.get("error", {}).get("message"),
                    )

        except Exception as e:
            raise CersaiError(
                f"Registration failed: {str(e)}",
                code="REGISTRATION_ERROR",
            )

    async def modify_security_interest(
        self, request: RegistrationRequest
    ) -> RegistrationResponse:
        """
        Modify security interest (Form II).

        This modifies an existing security interest registration.
        """
        if not request.cersai_reference:
            raise CersaiError(
                "CERSAI reference required for modification",
                code="MISSING_REFERENCE",
            )

        payload = self._build_registration_payload(request)
        payload["cersaiReference"] = request.cersai_reference
        payload["transactionType"] = "MODIFICATION"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/si/modify",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if response.status_code == 200 and data.get("success"):
                    return RegistrationResponse(
                        success=True,
                        transaction_type=TransactionType.MODIFICATION,
                        cersai_reference=request.cersai_reference,
                        status=RegistrationStatus.MODIFIED,
                        metadata=data.get("metadata", {}),
                    )
                else:
                    return RegistrationResponse(
                        success=False,
                        error_code=data.get("error", {}).get("code"),
                        error_message=data.get("error", {}).get("message"),
                    )

        except Exception as e:
            raise CersaiError(
                f"Modification failed: {str(e)}",
                code="MODIFICATION_ERROR",
            )

    async def satisfy_security_interest(
        self, cersai_reference: str, satisfaction_date: date
    ) -> RegistrationResponse:
        """
        Satisfy security interest (Form III).

        This marks a security interest as satisfied (loan closed).
        """
        payload = {
            "cersaiReference": cersai_reference,
            "satisfactionDate": satisfaction_date.isoformat(),
            "transactionType": "SATISFACTION",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/si/satisfy",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if response.status_code == 200 and data.get("success"):
                    return RegistrationResponse(
                        success=True,
                        transaction_type=TransactionType.SATISFACTION,
                        cersai_reference=cersai_reference,
                        status=RegistrationStatus.SATISFIED,
                    )
                else:
                    return RegistrationResponse(
                        success=False,
                        error_code=data.get("error", {}).get("code"),
                        error_message=data.get("error", {}).get("message"),
                    )

        except Exception as e:
            raise CersaiError(
                f"Satisfaction failed: {str(e)}",
                code="SATISFACTION_ERROR",
            )

    async def search_assets(
        self, request: SearchRequest
    ) -> SearchResponse:
        """
        Search for existing security interests on assets/borrowers.

        This is used for due diligence before loan disbursement.
        """
        payload = {}

        if request.borrower_pan:
            payload["borrowerPan"] = request.borrower_pan
        if request.borrower_aadhaar:
            payload["borrowerAadhaar"] = request.borrower_aadhaar
        if request.borrower_cin:
            payload["borrowerCin"] = request.borrower_cin
        if request.asset_type:
            payload["assetType"] = request.asset_type.value
        if request.property_address:
            payload["propertyAddress"] = request.property_address
        if request.survey_number:
            payload["surveyNumber"] = request.survey_number
        if request.vehicle_registration:
            payload["vehicleRegistration"] = request.vehicle_registration
        if request.cersai_reference:
            payload["cersaiReference"] = request.cersai_reference

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/si/search",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if response.status_code == 200:
                    return SearchResponse(
                        success=True,
                        records=data.get("records", []),
                        total_records=data.get("totalRecords", 0),
                    )
                else:
                    return SearchResponse(
                        success=False,
                        error_code=data.get("error", {}).get("code"),
                        error_message=data.get("error", {}).get("message"),
                    )

        except Exception as e:
            raise CersaiError(
                f"Search failed: {str(e)}",
                code="SEARCH_ERROR",
            )

    async def get_registration_status(
        self, cersai_reference: str
    ) -> RegistrationResponse:
        """Get status of a registration."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/si/status/{cersai_reference}",
                    headers=self._get_headers(),
                    timeout=30.0,
                )

                data = response.json()

                if response.status_code == 200:
                    return RegistrationResponse(
                        success=True,
                        cersai_reference=cersai_reference,
                        registration_number=data.get("registrationNumber"),
                        status=RegistrationStatus(data.get("status", "SUBMITTED")),
                        registration_date=datetime.strptime(
                            data["registrationDate"], "%Y-%m-%d"
                        ).date()
                        if data.get("registrationDate")
                        else None,
                        metadata=data,
                    )
                else:
                    return RegistrationResponse(
                        success=False,
                        cersai_reference=cersai_reference,
                        error_code=data.get("error", {}).get("code"),
                        error_message=data.get("error", {}).get("message"),
                    )

        except Exception as e:
            raise CersaiError(
                f"Status check failed: {str(e)}",
                code="STATUS_ERROR",
            )

    def _build_registration_payload(
        self, request: RegistrationRequest
    ) -> Dict[str, Any]:
        """Build registration payload."""
        return {
            "loanDetails": {
                "accountNumber": request.loan_account_number,
                "sanctionDate": request.sanction_date.isoformat(),
                "disbursementDate": request.disbursement_date.isoformat()
                if request.disbursement_date
                else None,
                "sanctionAmount": str(request.sanction_amount),
                "outstandingAmount": str(request.outstanding_amount),
                "interestRate": str(request.interest_rate)
                if request.interest_rate
                else None,
                "tenureMonths": request.tenure_months,
            },
            "borrowers": [
                {
                    "name": b.name,
                    "pan": b.pan,
                    "aadhaar": b.aadhaar,
                    "cin": b.cin,
                    "address": b.address,
                    "stateCode": b.state_code,
                    "pinCode": b.pin_code,
                    "entityType": b.entity_type,
                }
                for b in request.borrowers
            ],
            "assets": [
                {
                    "assetType": a.asset_type.value,
                    "description": a.description,
                    "propertyAddress": a.property_address,
                    "surveyNumber": a.survey_number,
                    "khataNumber": a.khata_number,
                    "plotArea": str(a.plot_area) if a.plot_area else None,
                    "plotAreaUnit": a.plot_area_unit,
                    "stateCode": a.state_code,
                    "districtCode": a.district_code,
                    "pinCode": a.pin_code,
                    "registrationNumber": a.registration_number,
                    "serialNumber": a.serial_number,
                    "marketValue": str(a.market_value) if a.market_value else None,
                    "valuationDate": a.valuation_date.isoformat()
                    if a.valuation_date
                    else None,
                }
                for a in request.assets
            ],
            "securityInterest": {
                "type": request.security_interest_type,
                "dateOfCreation": request.date_of_creation.isoformat()
                if request.date_of_creation
                else None,
                "priority": request.priority,
            },
        }


# Convenience functions

async def register_security_interest_for_loan(
    loan_account_id: UUID,
    loan_details: Dict[str, Any],
    borrower_details: List[Dict[str, Any]],
    asset_details: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> RegistrationResponse:
    """
    Register security interest for a loan.

    Convenience function for loan disbursement workflow.
    """
    client = CersaiClient(config)

    request = RegistrationRequest(
        loan_account_number=loan_details["account_number"],
        sanction_date=loan_details["sanction_date"],
        disbursement_date=loan_details.get("disbursement_date"),
        sanction_amount=Decimal(str(loan_details["sanction_amount"])),
        outstanding_amount=Decimal(str(loan_details.get("outstanding_amount", loan_details["sanction_amount"]))),
        interest_rate=Decimal(str(loan_details["interest_rate"]))
        if loan_details.get("interest_rate")
        else None,
        tenure_months=loan_details.get("tenure_months"),
        borrowers=[
            Borrower(
                name=b["name"],
                pan=b.get("pan"),
                aadhaar=b.get("aadhaar"),
                address=b.get("address"),
                state_code=b.get("state_code"),
                pin_code=b.get("pin_code"),
            )
            for b in borrower_details
        ],
        assets=[
            Asset(
                asset_type=AssetType(a["asset_type"]),
                description=a["description"],
                property_address=a.get("property_address"),
                survey_number=a.get("survey_number"),
                state_code=a.get("state_code"),
                district_code=a.get("district_code"),
                pin_code=a.get("pin_code"),
                market_value=Decimal(str(a["market_value"]))
                if a.get("market_value")
                else None,
            )
            for a in asset_details
        ],
        security_interest_type=loan_details.get("security_type", "HYPOTHECATION"),
        loan_account_id=loan_account_id,
    )

    return await client.register_security_interest(request)


async def search_existing_charges(
    borrower_pan: Optional[str] = None,
    borrower_aadhaar: Optional[str] = None,
    property_address: Optional[str] = None,
    vehicle_registration: Optional[str] = None,
    config: Dict[str, Any] = None,
) -> SearchResponse:
    """
    Search for existing charges on assets/borrowers.

    Used for due diligence before loan approval.
    """
    client = CersaiClient(config or {})

    request = SearchRequest(
        borrower_pan=borrower_pan,
        borrower_aadhaar=borrower_aadhaar,
        property_address=property_address,
        vehicle_registration=vehicle_registration,
    )

    return await client.search_assets(request)
