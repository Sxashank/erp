"""Enums for Legal Module."""

from enum import Enum


class NoticeType(str, Enum):
    """Types of legal notices under Indian law."""

    # SARFAESI Act 2002
    SARFAESI_13_2 = "SARFAESI_13_2"  # Section 13(2) Demand Notice - 60 days
    SARFAESI_13_4_POSSESSION = "SARFAESI_13_4_POSSESSION"  # Possession Notice - 15 days
    SARFAESI_AUCTION = "SARFAESI_AUCTION"  # Auction Notice - 30 days (Rule 8 & 9)

    # Negotiable Instruments Act
    NI_ACT_138 = "NI_ACT_138"  # Cheque Bounce Notice - 15 days

    # DRT Act 1993
    DRT_DEMAND = "DRT_DEMAND"  # DRT Recovery Notice

    # General
    RECALL_NOTICE = "RECALL_NOTICE"  # Loan Recall Notice
    ARBITRATION = "ARBITRATION"  # Arbitration Invocation Notice
    LOK_ADALAT = "LOK_ADALAT"  # Lok Adalat Settlement Notice
    FINAL_DEMAND = "FINAL_DEMAND"  # Final Demand Before Legal Action
    SYMBOLIC_POSSESSION = "SYMBOLIC_POSSESSION"  # Symbolic Possession Notice
    PHYSICAL_POSSESSION = "PHYSICAL_POSSESSION"  # Physical Possession Notice
    SALE_CONFIRMATION = "SALE_CONFIRMATION"  # Sale Confirmation Notice


class NoticeStatus(str, Enum):
    """Status of a legal notice."""

    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    APPROVED = "APPROVED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    RESPONDED = "RESPONDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class DeliveryMode(str, Enum):
    """Notice delivery modes."""

    RPAD = "RPAD"  # Registered Post with Acknowledgement Due
    SPEED_POST = "SPEED_POST"
    COURIER = "COURIER"
    HAND_DELIVERY = "HAND_DELIVERY"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUBLICATION = "PUBLICATION"  # Newspaper publication


class DeliveryStatus(str, Enum):
    """Delivery status of a notice."""

    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    REFUSED = "REFUSED"
    RETURNED_UNDELIVERED = "RETURNED_UNDELIVERED"
    ADDRESS_INSUFFICIENT = "ADDRESS_INSUFFICIENT"
    ADDRESSEE_UNKNOWN = "ADDRESSEE_UNKNOWN"
    UNCLAIMED = "UNCLAIMED"


class DocumentCategory(str, Enum):
    """Categories of legal documents."""

    # Loan Documents
    LOAN_AGREEMENT = "LOAN_AGREEMENT"
    SANCTION_LETTER = "SANCTION_LETTER"
    PDC = "PDC"  # Post-dated cheques
    NACH_MANDATE = "NACH_MANDATE"
    PROMISSORY_NOTE = "PROMISSORY_NOTE"

    # Security Documents
    TITLE_DEED = "TITLE_DEED"
    VALUATION_REPORT = "VALUATION_REPORT"
    MOD = "MOD"  # Memorandum of Deposit
    INSURANCE_POLICY = "INSURANCE_POLICY"
    ENCUMBRANCE_CERTIFICATE = "ENCUMBRANCE_CERTIFICATE"

    # Legal Filings
    PETITION = "PETITION"
    APPLICATION = "APPLICATION"
    AFFIDAVIT = "AFFIDAVIT"
    VAKALATNAMA = "VAKALATNAMA"
    WRITTEN_STATEMENT = "WRITTEN_STATEMENT"
    REJOINDER = "REJOINDER"

    # Court Orders
    INTERIM_ORDER = "INTERIM_ORDER"
    FINAL_ORDER = "FINAL_ORDER"
    DECREE = "DECREE"
    WARRANT = "WARRANT"
    RECOVERY_CERTIFICATE = "RECOVERY_CERTIFICATE"

    # Execution
    POSSESSION_CERTIFICATE = "POSSESSION_CERTIFICATE"
    SALE_CERTIFICATE = "SALE_CERTIFICATE"

    # Notices
    NOTICE_SENT = "NOTICE_SENT"
    NOTICE_RECEIVED = "NOTICE_RECEIVED"
    POD = "POD"  # Proof of Delivery

    # Correspondence
    LEGAL_OPINION = "LEGAL_OPINION"
    CORRESPONDENCE = "CORRESPONDENCE"

    # Other
    PHOTOGRAPH = "PHOTOGRAPH"
    OTHER = "OTHER"


class ExpenseCategoryType(str, Enum):
    """Categories of legal expenses."""

    COURT_FEE = "COURT_FEE"
    FILING_FEE = "FILING_FEE"
    PROCESS_FEE = "PROCESS_FEE"
    EXECUTION_FEE = "EXECUTION_FEE"
    ADVOCATE_RETAINER = "ADVOCATE_RETAINER"
    ADVOCATE_APPEARANCE = "ADVOCATE_APPEARANCE"
    ADVOCATE_SUCCESS_FEE = "ADVOCATE_SUCCESS_FEE"
    VALUATION_CHARGES = "VALUATION_CHARGES"
    PUBLICATION_CHARGES = "PUBLICATION_CHARGES"
    TRAVEL_CONVEYANCE = "TRAVEL_CONVEYANCE"
    STAMP_DUTY = "STAMP_DUTY"
    NOTARIZATION = "NOTARIZATION"
    PHOTOCOPYING = "PHOTOCOPYING"
    COURIER_POSTAGE = "COURIER_POSTAGE"
    CERSAI_CHARGES = "CERSAI_CHARGES"
    AUCTION_EXPENSES = "AUCTION_EXPENSES"
    SECURITY_CHARGES = "SECURITY_CHARGES"
    MISCELLANEOUS = "MISCELLANEOUS"


class ExpenseStatus(str, Enum):
    """Status of legal expense."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    PARTIALLY_RECOVERED = "PARTIALLY_RECOVERED"
    FULLY_RECOVERED = "FULLY_RECOVERED"
    WRITTEN_OFF = "WRITTEN_OFF"


class RecoveryType(str, Enum):
    """Types of expense recovery."""

    FROM_BORROWER = "FROM_BORROWER"
    FROM_SALE_PROCEEDS = "FROM_SALE_PROCEEDS"
    FROM_OTS = "FROM_OTS"  # One-time Settlement
    FROM_GUARANTOR = "FROM_GUARANTOR"
    WRITE_OFF = "WRITE_OFF"
    WAIVED = "WAIVED"


class FeeStructureType(str, Enum):
    """Types of advocate fee structures."""

    FIXED = "FIXED"
    HOURLY = "HOURLY"
    PER_APPEARANCE = "PER_APPEARANCE"
    SUCCESS_FEE = "SUCCESS_FEE"
    PERCENTAGE = "PERCENTAGE"  # Percentage of recovery
    RETAINER_PLUS_APPEARANCE = "RETAINER_PLUS_APPEARANCE"


class AdvocateRole(str, Enum):
    """Role of advocate in a case."""

    LEAD_COUNSEL = "LEAD_COUNSEL"
    ASSOCIATE_COUNSEL = "ASSOCIATE_COUNSEL"
    JUNIOR_COUNSEL = "JUNIOR_COUNSEL"
    CONSULTANT = "CONSULTANT"
    ADVISOR = "ADVISOR"


class SpecializationType(str, Enum):
    """Advocate specialization areas."""

    BANKING_FINANCE = "BANKING_FINANCE"
    DEBT_RECOVERY = "DEBT_RECOVERY"
    SARFAESI = "SARFAESI"
    DRT = "DRT"
    CIVIL = "CIVIL"
    CRIMINAL = "CRIMINAL"
    ARBITRATION = "ARBITRATION"
    NCLT_IBC = "NCLT_IBC"
    PROPERTY = "PROPERTY"
    CORPORATE = "CORPORATE"
    TAX = "TAX"
    CONSUMER = "CONSUMER"


class CourtType(str, Enum):
    """Types of courts and tribunals."""

    DRT = "DRT"  # Debt Recovery Tribunal
    DRAT = "DRAT"  # Debt Recovery Appellate Tribunal
    NCLT = "NCLT"  # National Company Law Tribunal
    NCLAT = "NCLAT"  # National Company Law Appellate Tribunal
    DISTRICT_COURT = "DISTRICT_COURT"
    HIGH_COURT = "HIGH_COURT"
    SUPREME_COURT = "SUPREME_COURT"
    LOK_ADALAT = "LOK_ADALAT"
    ARBITRATION_CENTER = "ARBITRATION_CENTER"
    CONSUMER_FORUM = "CONSUMER_FORUM"
    MAGISTRATE_COURT = "MAGISTRATE_COURT"


class AlertPriority(str, Enum):
    """Priority levels for limitation alerts."""

    LOW = "LOW"  # > 30 days remaining
    MEDIUM = "MEDIUM"  # 15-30 days remaining
    HIGH = "HIGH"  # 7-14 days remaining
    CRITICAL = "CRITICAL"  # < 7 days remaining
    OVERDUE = "OVERDUE"  # Deadline passed


class SARFAESIStage(str, Enum):
    """SARFAESI proceeding stages."""

    DEMAND_13_2 = "DEMAND_13_2"  # Section 13(2) demand notice
    OBJECTION_PERIOD = "OBJECTION_PERIOD"  # 60 days objection period
    OBJECTION_13_3A = "OBJECTION_13_3A"  # Section 13(3A) objection received
    POSSESSION_13_4 = "POSSESSION_13_4"  # Section 13(4) possession
    SYMBOLIC_POSSESSION = "SYMBOLIC_POSSESSION"
    PHYSICAL_POSSESSION = "PHYSICAL_POSSESSION"
    AUCTION_SCHEDULED = "AUCTION_SCHEDULED"
    AUCTION_CONDUCTED = "AUCTION_CONDUCTED"
    SALE_CONFIRMED = "SALE_CONFIRMED"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class PossessionType(str, Enum):
    """Type of possession under SARFAESI."""

    SYMBOLIC = "SYMBOLIC"
    PHYSICAL = "PHYSICAL"


class AuctionStatus(str, Enum):
    """Status of property auction."""

    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    BIDDING_OPEN = "BIDDING_OPEN"
    BIDDING_CLOSED = "BIDDING_CLOSED"
    HIGHEST_BID_ACCEPTED = "HIGHEST_BID_ACCEPTED"
    SALE_CONFIRMED = "SALE_CONFIRMED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    TITLE_TRANSFERRED = "TITLE_TRANSFERRED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class PropertyType(str, Enum):
    """Types of secured property."""

    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"
    AGRICULTURAL = "AGRICULTURAL"
    PLOT = "PLOT"
    VEHICLE = "VEHICLE"
    MACHINERY = "MACHINERY"
    STOCK = "STOCK"
    RECEIVABLES = "RECEIVABLES"
    OTHER = "OTHER"


class BarCouncilState(str, Enum):
    """Indian State Bar Councils."""

    ANDHRA_PRADESH = "AP"
    ARUNACHAL_PRADESH = "AR"
    ASSAM = "AS"
    BIHAR = "BR"
    CHHATTISGARH = "CG"
    DELHI = "DL"
    GOA = "GA"
    GUJARAT = "GJ"
    HARYANA = "HR"
    HIMACHAL_PRADESH = "HP"
    JHARKHAND = "JH"
    KARNATAKA = "KA"
    KERALA = "KL"
    MADHYA_PRADESH = "MP"
    MAHARASHTRA = "MH"
    MANIPUR = "MN"
    MEGHALAYA = "ML"
    MIZORAM = "MZ"
    NAGALAND = "NL"
    ODISHA = "OD"
    PUNJAB = "PB"
    RAJASTHAN = "RJ"
    SIKKIM = "SK"
    TAMIL_NADU = "TN"
    TELANGANA = "TS"
    TRIPURA = "TR"
    UTTAR_PRADESH = "UP"
    UTTARAKHAND = "UK"
    WEST_BENGAL = "WB"
