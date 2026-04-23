"""HRIS API routes package."""

from fastapi import APIRouter

from app.api.v1.hris.employees import router as employees_router
from app.api.v1.hris.shifts import router as shifts_router
from app.api.v1.hris.leaves import router as leaves_router
from app.api.v1.hris.attendance import router as attendance_router
from app.api.v1.hris.separation import router as separation_router

router = APIRouter()

router.include_router(employees_router, prefix="/employees", tags=["HRIS - Employees"])
router.include_router(shifts_router, tags=["HRIS - Shifts & Holidays"])
router.include_router(leaves_router, prefix="/leaves", tags=["HRIS - Leave Management"])
router.include_router(attendance_router, prefix="/attendance", tags=["HRIS - Attendance"])
router.include_router(separation_router, tags=["HRIS - Separation & FnF"])
