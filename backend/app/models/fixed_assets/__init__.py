"""Fixed Assets models."""

from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.depreciation import (
    Depreciation,
    DepreciationRun,
    ITBlockSummary,
)
from app.models.fixed_assets.asset_transfer import AssetTransfer
from app.models.fixed_assets.asset_revaluation import AssetRevaluation
from app.models.fixed_assets.physical_verification import (
    PhysicalVerificationSchedule,
    PhysicalVerificationEntry,
    PhysicalVerificationDiscrepancy,
)
from app.models.fixed_assets.lease import (
    Lease,
    LeasePaymentSchedule,
    LeaseModification,
)
from app.models.fixed_assets.maintenance import (
    AMCContract,
    MaintenanceRequest,
    MaintenanceSchedule,
    AssetWarranty,
)
from app.models.fixed_assets.insurance import (
    InsurancePolicy,
    InsuranceClaim,
)
from app.models.fixed_assets.fa_config import FAConfiguration

__all__ = [
    "AssetCategory",
    "FixedAsset",
    "Depreciation",
    "DepreciationRun",
    "ITBlockSummary",
    "AssetTransfer",
    "AssetRevaluation",
    "PhysicalVerificationSchedule",
    "PhysicalVerificationEntry",
    "PhysicalVerificationDiscrepancy",
    "Lease",
    "LeasePaymentSchedule",
    "LeaseModification",
    "AMCContract",
    "MaintenanceRequest",
    "MaintenanceSchedule",
    "AssetWarranty",
    "InsurancePolicy",
    "InsuranceClaim",
    "FAConfiguration",
]
