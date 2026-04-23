"""Background workers for async task processing.

Includes workers for:
- Fixed Assets bulk operations
- Legal alerts and reminders
- Portal notifications
- SLA monitoring
"""

from app.workers.fa_worker import process_bulk_asset_import
from app.workers.legal_alerts_worker import (
    process_legal_alerts,
    run_daily_legal_alerts,
    run_limitation_check,
    run_hearing_reminders,
)
from app.workers.portal_reminders_worker import (
    process_portal_reminders,
    run_daily_emi_reminders,
    run_overdue_notifications,
)
from app.workers.sla_monitor_worker import (
    process_sla_monitoring,
    run_sla_monitoring,
    run_escalation_review,
    generate_sla_report,
)

__all__ = [
    # Fixed Assets
    "process_bulk_asset_import",
    # Legal Alerts
    "process_legal_alerts",
    "run_daily_legal_alerts",
    "run_limitation_check",
    "run_hearing_reminders",
    # Portal Reminders
    "process_portal_reminders",
    "run_daily_emi_reminders",
    "run_overdue_notifications",
    # SLA Monitoring
    "process_sla_monitoring",
    "run_sla_monitoring",
    "run_escalation_review",
    "generate_sla_report",
]
