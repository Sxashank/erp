"""HRIS models package."""

from app.models.hris.employee import (
    Employee,
    EmployeeDocument,
    EmployeeFamily,
    EmployeeBankAccount,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeStatutory,
    EmployeeLifecycleEvent,
)
from app.models.hris.shift import (
    Shift,
    HolidayCalendar,
    Holiday,
)
from app.models.hris.leave import (
    LeaveType,
    LeaveBalance,
    LeaveApplication,
    LeaveEncashment,
)
from app.models.hris.attendance import (
    AttendancePunch,
    Attendance,
    AttendanceRegularization,
    MonthlyAttendanceSummary,
)
from app.models.hris.separation import (
    Separation,
    SeparationType,
    SeparationStatus,
    ResignationReason,
    ClearanceChecklist,
    SeparationClearance,
    ClearanceStatus,
    FnFSettlement,
    FnFStatus,
)
from app.models.hris.training import (
    TrainingProgram,
    TrainingNomination,
    TrainingFeedback,
)
from app.models.hris.performance import (
    AppraisalCycle,
    PerformanceGoal,
    EmployeeAppraisal,
)

__all__ = [
    # Employee
    "Employee",
    "EmployeeDocument",
    "EmployeeFamily",
    "EmployeeBankAccount",
    "EmployeeEducation",
    "EmployeeExperience",
    "EmployeeStatutory",
    "EmployeeLifecycleEvent",
    # Shift & Holiday
    "Shift",
    "HolidayCalendar",
    "Holiday",
    # Leave
    "LeaveType",
    "LeaveBalance",
    "LeaveApplication",
    "LeaveEncashment",
    # Attendance
    "AttendancePunch",
    "Attendance",
    "AttendanceRegularization",
    "MonthlyAttendanceSummary",
    # Separation & FnF
    "Separation",
    "SeparationType",
    "SeparationStatus",
    "ResignationReason",
    "ClearanceChecklist",
    "SeparationClearance",
    "ClearanceStatus",
    "FnFSettlement",
    "FnFStatus",
    # Training
    "TrainingProgram",
    "TrainingNomination",
    "TrainingFeedback",
    # Performance
    "AppraisalCycle",
    "PerformanceGoal",
    "EmployeeAppraisal",
]
