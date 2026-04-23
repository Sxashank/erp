"""Fixed Assets services."""

from app.services.fixed_assets.asset_category_service import AssetCategoryService
from app.services.fixed_assets.asset_service import AssetService
from app.services.fixed_assets.depreciation_service import DepreciationService

__all__ = [
    "AssetCategoryService",
    "AssetService",
    "DepreciationService",
]
