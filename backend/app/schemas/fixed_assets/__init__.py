"""Fixed Assets schemas."""

from app.schemas.fixed_assets.asset_category import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCategoryResponse,
    AssetCategoryTreeResponse,
)
from app.schemas.fixed_assets.fixed_asset import (
    FixedAssetCreate,
    FixedAssetUpdate,
    FixedAssetResponse,
    AssetCapitalizeRequest,
    AssetDisposeRequest,
    AssetTransferRequest,
    AssetRevalueRequest,
    AssetImpairRequest,
)
from app.schemas.fixed_assets.depreciation import (
    DepreciationRunCreate,
    DepreciationRunResponse,
    DepreciationResponse,
    DepreciationScheduleItem,
    DepreciationScheduleResponse,
    DepreciationReverseRequest,
)

__all__ = [
    # Asset Category
    "AssetCategoryCreate",
    "AssetCategoryUpdate",
    "AssetCategoryResponse",
    "AssetCategoryTreeResponse",
    # Fixed Asset
    "FixedAssetCreate",
    "FixedAssetUpdate",
    "FixedAssetResponse",
    "AssetCapitalizeRequest",
    "AssetDisposeRequest",
    "AssetTransferRequest",
    "AssetRevalueRequest",
    "AssetImpairRequest",
    # Depreciation
    "DepreciationRunCreate",
    "DepreciationRunResponse",
    "DepreciationResponse",
    "DepreciationScheduleItem",
    "DepreciationScheduleResponse",
    "DepreciationReverseRequest",
]
