"""Inventory module API routers."""

from fastapi import APIRouter

from app.api.v1.inventory import categories, items, warehouses, stock

router = APIRouter()

router.include_router(categories.router, prefix="/categories", tags=["inventory-categories"])
router.include_router(items.router, prefix="/items", tags=["inventory-items"])
router.include_router(warehouses.router, prefix="/warehouses", tags=["inventory-warehouses"])
router.include_router(stock.router, prefix="/stock", tags=["inventory-stock"])
