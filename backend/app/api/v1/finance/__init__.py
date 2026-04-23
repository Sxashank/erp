"""Finance API routes."""

from app.api.v1.finance.financial_years import router as financial_years_router
from app.api.v1.finance.account_groups import router as account_groups_router
from app.api.v1.finance.accounts import router as accounts_router
from app.api.v1.finance.voucher_types import router as voucher_types_router
from app.api.v1.finance.vouchers import router as vouchers_router
from app.api.v1.finance.year_end import router as year_end_router
from app.api.v1.finance.recurring_vouchers import router as recurring_vouchers_router
from app.api.v1.finance.voucher_templates import router as voucher_templates_router
from app.api.v1.finance.gl_entries import router as gl_entries_router
from app.api.v1.finance.cost_centers import router as cost_centers_router

__all__ = [
    "financial_years_router",
    "account_groups_router",
    "accounts_router",
    "voucher_types_router",
    "vouchers_router",
    "year_end_router",
    "recurring_vouchers_router",
    "voucher_templates_router",
    "gl_entries_router",
    "cost_centers_router",
]
