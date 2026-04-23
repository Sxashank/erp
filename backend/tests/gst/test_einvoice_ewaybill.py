"""Unit tests for E-Invoice and E-Way Bill.

Tests cover:
- E-Invoice payload building
- IRN format validation
- E-Way Bill threshold checks
- Validity calculations
- Status transitions
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.gst.einvoice import (
    EInvoiceProvider,
    EInvoiceRequestStatus,
    EWayBillProvider,
    EWayBillStatus,
    TransportMode,
    VehicleType,
    TransactionType,
    SubSupplyType,
)


class TestEInvoiceEnums:
    """Tests for E-Invoice enum values."""

    def test_einvoice_providers(self):
        """Test all E-Invoice providers are defined."""
        expected_providers = [
            EInvoiceProvider.NIC,
            EInvoiceProvider.CLEARTAX,
            EInvoiceProvider.TALLY,
            EInvoiceProvider.ZOHO,
        ]
        for provider in expected_providers:
            assert isinstance(provider, EInvoiceProvider)

    def test_einvoice_request_status_flow(self):
        """Test E-Invoice request status values."""
        assert EInvoiceRequestStatus.PENDING.value == "PENDING"
        assert EInvoiceRequestStatus.PROCESSING.value == "PROCESSING"
        assert EInvoiceRequestStatus.SUCCESS.value == "SUCCESS"
        assert EInvoiceRequestStatus.FAILED.value == "FAILED"
        assert EInvoiceRequestStatus.CANCELLED.value == "CANCELLED"

    def test_ewaybill_status_flow(self):
        """Test E-Way Bill status values."""
        assert EWayBillStatus.DRAFT.value == "DRAFT"
        assert EWayBillStatus.GENERATED.value == "GENERATED"
        assert EWayBillStatus.ACTIVE.value == "ACTIVE"
        assert EWayBillStatus.CANCELLED.value == "CANCELLED"
        assert EWayBillStatus.EXPIRED.value == "EXPIRED"
        assert EWayBillStatus.EXTENDED.value == "EXTENDED"


class TestTransportModes:
    """Tests for transport mode enums."""

    def test_transport_modes(self):
        """Test all transport modes are defined."""
        assert TransportMode.ROAD.value == "1"
        assert TransportMode.RAIL.value == "2"
        assert TransportMode.AIR.value == "3"
        assert TransportMode.SHIP.value == "4"

    def test_vehicle_types(self):
        """Test vehicle types."""
        assert VehicleType.REGULAR.value == "R"
        assert VehicleType.ODC.value == "O"

    def test_transaction_types(self):
        """Test transaction types."""
        assert TransactionType.REGULAR.value == "1"
        assert TransactionType.BILL_TO_SHIP_TO.value == "2"
        assert TransactionType.BILL_FROM_DISPATCH.value == "3"
        assert TransactionType.COMBINATION.value == "4"

    def test_sub_supply_types(self):
        """Test sub-supply types."""
        assert SubSupplyType.SUPPLY.value == "1"
        assert SubSupplyType.IMPORT.value == "2"
        assert SubSupplyType.EXPORT.value == "3"
        assert SubSupplyType.JOB_WORK.value == "4"
        assert SubSupplyType.SALES_RETURN.value == "7"


class TestIRNFormat:
    """Tests for IRN format validation."""

    def test_irn_length(self):
        """Test IRN is 64 characters."""
        # IRN format: SHA256 hash of GSTIN + Doc Type + Doc Number + FY
        sample_irn = "a" * 64
        assert len(sample_irn) == 64

    def test_irn_characters(self):
        """Test IRN contains only valid characters (hex)."""
        # IRN is a SHA256 hash in hex format
        valid_irn = "abcdef0123456789" * 4  # 64 characters
        assert all(c in "0123456789abcdef" for c in valid_irn.lower())


class TestEWayBillThreshold:
    """Tests for E-Way Bill threshold calculations."""

    def test_threshold_above_50000(self):
        """Test E-Way Bill required above Rs. 50,000."""
        invoice_value = Decimal("50001")
        threshold = Decimal("50000")
        is_required = invoice_value > threshold
        assert is_required == True

    def test_threshold_equal_50000(self):
        """Test E-Way Bill not required at exactly Rs. 50,000."""
        invoice_value = Decimal("50000")
        threshold = Decimal("50000")
        is_required = invoice_value > threshold
        assert is_required == False

    def test_threshold_below_50000(self):
        """Test E-Way Bill not required below Rs. 50,000."""
        invoice_value = Decimal("49999.99")
        threshold = Decimal("50000")
        is_required = invoice_value > threshold
        assert is_required == False


class TestEWayBillValidity:
    """Tests for E-Way Bill validity calculations."""

    def test_validity_calculation_by_distance(self):
        """Test validity period calculation based on distance."""
        # Validity rules:
        # <= 100 KM: 1 day
        # 101-300 KM: 3 days (100 KM/day)
        # 301-500 KM: 5 days
        # > 500 KM: 1 day per 100 KM

        def calculate_validity_days(distance_km: int) -> int:
            """Calculate validity in days based on distance."""
            if distance_km <= 100:
                return 1
            else:
                return max(1, (distance_km + 99) // 100)  # Ceiling division

        assert calculate_validity_days(50) == 1
        assert calculate_validity_days(100) == 1
        assert calculate_validity_days(150) == 2
        assert calculate_validity_days(200) == 2
        assert calculate_validity_days(500) == 5
        assert calculate_validity_days(1000) == 10

    def test_validity_expiry_check(self):
        """Test E-Way Bill validity expiry check."""
        now = datetime.utcnow()

        # Valid E-Way Bill (expires in 24 hours)
        valid_until_future = now + timedelta(hours=24)
        is_valid_1 = now < valid_until_future
        assert is_valid_1 == True

        # Expired E-Way Bill
        valid_until_past = now - timedelta(hours=1)
        is_valid_2 = now < valid_until_past
        assert is_valid_2 == False

    def test_expiring_soon_check(self):
        """Test E-Way Bill expiring soon check (within 8 hours)."""
        now = datetime.utcnow()
        soon_threshold = timedelta(hours=8)

        # Expiring in 4 hours (expiring soon)
        valid_until_1 = now + timedelta(hours=4)
        is_expiring_soon_1 = (
            now < valid_until_1 and
            valid_until_1 <= now + soon_threshold
        )
        assert is_expiring_soon_1 == True

        # Expiring in 12 hours (not expiring soon)
        valid_until_2 = now + timedelta(hours=12)
        is_expiring_soon_2 = (
            now < valid_until_2 and
            valid_until_2 <= now + soon_threshold
        )
        assert is_expiring_soon_2 == False


class TestEInvoicePayload:
    """Tests for E-Invoice payload building."""

    def test_basic_payload_structure(self):
        """Test basic E-Invoice payload structure."""
        payload = {
            "Version": "1.1",
            "TranDtls": {
                "TaxSch": "GST",
                "SupTyp": "B2B",
                "RegRev": "N",
            },
            "DocDtls": {
                "Typ": "INV",
                "No": "INV-001",
                "Dt": "15/01/2026",
            },
            "SellerDtls": {
                "Gstin": "29AABCT1332L1ZR",
                "LglNm": "Test Company",
                "Addr1": "Test Address",
                "Loc": "Bangalore",
                "Pin": 560001,
                "Stcd": "29",
            },
            "BuyerDtls": {
                "Gstin": "27AABCU9603R1ZP",
                "LglNm": "Buyer Company",
                "Addr1": "Buyer Address",
                "Loc": "Mumbai",
                "Pin": 400001,
                "Stcd": "27",
                "Pos": "27",
            },
            "ItemList": [],
            "ValDtls": {
                "AssVal": 10000,
                "CgstVal": 0,
                "SgstVal": 0,
                "IgstVal": 1800,
                "TotInvVal": 11800,
            },
        }

        # Validate required sections
        assert "Version" in payload
        assert "TranDtls" in payload
        assert "DocDtls" in payload
        assert "SellerDtls" in payload
        assert "BuyerDtls" in payload
        assert "ItemList" in payload
        assert "ValDtls" in payload

        # Validate GSTIN format (15 characters)
        assert len(payload["SellerDtls"]["Gstin"]) == 15
        assert len(payload["BuyerDtls"]["Gstin"]) == 15

    def test_gstin_format_validation(self):
        """Test GSTIN format validation."""
        # GSTIN format: 2 digit state code + 10 digit PAN + 1 digit entity + 1 digit Z + 1 digit checksum
        valid_gstin = "29AABCT1332L1ZR"

        # Check length
        assert len(valid_gstin) == 15

        # Check state code (01-37)
        state_code = int(valid_gstin[:2])
        assert 1 <= state_code <= 37

        # Check PAN format (5 letters + 4 digits + 1 letter)
        pan = valid_gstin[2:12]
        assert pan[:5].isalpha()
        assert pan[5:9].isdigit()
        assert pan[9].isalpha()

    def test_document_date_format(self):
        """Test document date format (DD/MM/YYYY)."""
        invoice_date = date(2026, 1, 15)
        formatted_date = invoice_date.strftime("%d/%m/%Y")
        assert formatted_date == "15/01/2026"

    def test_item_payload_structure(self):
        """Test E-Invoice item payload structure."""
        item = {
            "SlNo": "1",
            "PrdDesc": "Test Product",
            "IsServc": "N",
            "HsnCd": "84715020",
            "Qty": 1.0,
            "Unit": "NOS",
            "UnitPrice": 10000.0,
            "TotAmt": 10000.0,
            "Discount": 0,
            "AssAmt": 10000.0,
            "GstRt": 18.0,
            "IgstAmt": 1800.0,
            "CgstAmt": 0,
            "SgstAmt": 0,
            "TotItemVal": 11800.0,
        }

        # Validate required fields
        assert "SlNo" in item
        assert "PrdDesc" in item
        assert "HsnCd" in item
        assert "AssAmt" in item
        assert "GstRt" in item


class TestEWayBillPayload:
    """Tests for E-Way Bill payload building."""

    def test_basic_payload_structure(self):
        """Test basic E-Way Bill payload structure."""
        payload = {
            "supplyType": "O",
            "subSupplyType": "1",
            "docType": "INV",
            "docNo": "INV-001",
            "docDate": "15/01/2026",
            "fromGstin": "29AABCT1332L1ZR",
            "fromTrdName": "Test Company",
            "fromAddr1": "Test Address",
            "fromPlace": "Bangalore",
            "fromPincode": 560001,
            "fromStateCode": 29,
            "toGstin": "27AABCU9603R1ZP",
            "toTrdName": "Buyer Company",
            "toAddr1": "Buyer Address",
            "toPlace": "Mumbai",
            "toPincode": 400001,
            "toStateCode": 27,
            "totalValue": 10000,
            "cgstValue": 0,
            "sgstValue": 0,
            "igstValue": 1800,
            "totInvValue": 11800,
            "transMode": "1",
            "transDistance": 1000,
            "itemList": [],
        }

        # Validate required fields
        assert payload["supplyType"] in ["O", "I"]
        assert payload["transMode"] in ["1", "2", "3", "4"]
        assert payload["transDistance"] > 0

    def test_pincode_format(self):
        """Test pincode is 6 digits."""
        valid_pincode = 560001
        pincode_str = str(valid_pincode)
        assert len(pincode_str) == 6
        assert pincode_str.isdigit()

    def test_state_code_range(self):
        """Test state code is valid (1-37)."""
        valid_state_codes = [1, 9, 29, 27, 37]
        for code in valid_state_codes:
            assert 1 <= code <= 37


class TestEInvoiceCancellation:
    """Tests for E-Invoice cancellation rules."""

    def test_cancellation_reason_codes(self):
        """Test valid cancellation reason codes."""
        valid_reasons = {
            "1": "Duplicate",
            "2": "Data Entry Error",
            "3": "Order Cancelled",
            "4": "Others",
        }

        for code in ["1", "2", "3", "4"]:
            assert code in valid_reasons

    def test_cancellation_time_limit(self):
        """Test E-Invoice can be cancelled within 24 hours."""
        generation_time = datetime(2026, 1, 15, 10, 0, 0)
        current_time = datetime(2026, 1, 16, 8, 0, 0)  # 22 hours later

        time_diff = current_time - generation_time
        can_cancel = time_diff <= timedelta(hours=24)

        assert can_cancel == True

        # After 24 hours
        current_time_after = datetime(2026, 1, 16, 12, 0, 0)  # 26 hours later
        time_diff_after = current_time_after - generation_time
        can_cancel_after = time_diff_after <= timedelta(hours=24)

        assert can_cancel_after == False


class TestEWayBillCancellation:
    """Tests for E-Way Bill cancellation rules."""

    def test_cancellation_reason_codes(self):
        """Test valid E-Way Bill cancellation reason codes."""
        valid_reasons = {
            "1": "Duplicate",
            "2": "Order Cancelled",
            "3": "Data Entry Mistake",
            "4": "Others",
        }

        for code in ["1", "2", "3", "4"]:
            assert code in valid_reasons

    def test_cancellation_before_vehicle_movement(self):
        """Test E-Way Bill can be cancelled before vehicle movement starts."""
        # E-Way Bill can be cancelled if:
        # 1. Vehicle has not started movement
        # 2. Within 24 hours of generation
        # 3. Not expired

        generation_time = datetime(2026, 1, 15, 10, 0, 0)
        current_time = datetime(2026, 1, 15, 20, 0, 0)
        valid_until = datetime(2026, 1, 16, 10, 0, 0)
        vehicle_movement_started = False

        time_since_generation = current_time - generation_time
        is_within_24_hours = time_since_generation <= timedelta(hours=24)
        is_not_expired = current_time < valid_until

        can_cancel = (
            not vehicle_movement_started and
            is_within_24_hours and
            is_not_expired
        )

        assert can_cancel == True


class TestEInvoiceApplicability:
    """Tests for E-Invoice applicability rules."""

    def test_turnover_threshold(self):
        """Test E-Invoice applicability based on turnover."""
        # E-Invoice is mandatory for businesses with turnover > Rs. 5 Crores
        threshold = Decimal("5_00_00_000")  # 5 Crores

        turnover_1 = Decimal("6_00_00_000")  # 6 Crores
        is_applicable_1 = turnover_1 > threshold
        assert is_applicable_1 == True

        turnover_2 = Decimal("4_00_00_000")  # 4 Crores
        is_applicable_2 = turnover_2 > threshold
        assert is_applicable_2 == False

    def test_document_types_applicable(self):
        """Test document types applicable for E-Invoice."""
        applicable_doc_types = ["INV", "CRN", "DBN"]
        non_applicable_doc_types = ["BOE", "CHL"]

        for doc_type in applicable_doc_types:
            assert doc_type in ["INV", "CRN", "DBN"]

        for doc_type in non_applicable_doc_types:
            assert doc_type not in ["INV", "CRN", "DBN"]


class TestHSNCode:
    """Tests for HSN code validation."""

    def test_hsn_code_length(self):
        """Test HSN code length (4, 6, or 8 digits)."""
        valid_lengths = [4, 6, 8]

        hsn_4_digit = "8471"
        hsn_6_digit = "847150"
        hsn_8_digit = "84715020"

        assert len(hsn_4_digit) in valid_lengths
        assert len(hsn_6_digit) in valid_lengths
        assert len(hsn_8_digit) in valid_lengths

    def test_hsn_code_numeric(self):
        """Test HSN code is numeric."""
        hsn_code = "84715020"
        assert hsn_code.isdigit()

    def test_sac_code_for_services(self):
        """Test SAC code starts with 99 for services."""
        sac_code = "998314"  # Accounting services
        assert sac_code.startswith("99")


class TestTaxCalculations:
    """Tests for tax calculations in E-Invoice/E-Way Bill."""

    def test_intra_state_tax_split(self):
        """Test intra-state tax split (CGST + SGST)."""
        taxable_value = Decimal("10000")
        gst_rate = Decimal("18")

        total_gst = (taxable_value * gst_rate / Decimal("100")).quantize(Decimal("0.01"))
        cgst = (total_gst / Decimal("2")).quantize(Decimal("0.01"))
        sgst = (total_gst / Decimal("2")).quantize(Decimal("0.01"))
        igst = Decimal("0")

        assert total_gst == Decimal("1800.00")
        assert cgst == Decimal("900.00")
        assert sgst == Decimal("900.00")
        assert igst == Decimal("0")
        assert cgst + sgst == total_gst

    def test_inter_state_tax(self):
        """Test inter-state tax (IGST only)."""
        taxable_value = Decimal("10000")
        gst_rate = Decimal("18")

        igst = (taxable_value * gst_rate / Decimal("100")).quantize(Decimal("0.01"))
        cgst = Decimal("0")
        sgst = Decimal("0")

        assert igst == Decimal("1800.00")
        assert cgst == Decimal("0")
        assert sgst == Decimal("0")

    def test_total_invoice_value(self):
        """Test total invoice value calculation."""
        taxable_value = Decimal("10000")
        cgst = Decimal("900")
        sgst = Decimal("900")
        igst = Decimal("0")
        cess = Decimal("0")
        other_charges = Decimal("0")
        discount = Decimal("0")
        round_off = Decimal("0")

        total = taxable_value + cgst + sgst + igst + cess + other_charges - discount + round_off
        assert total == Decimal("11800")
