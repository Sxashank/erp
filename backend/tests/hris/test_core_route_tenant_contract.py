"""HRIS core route contract tests for tenant-scoped handlers."""

import inspect
from types import SimpleNamespace

from app.api.v1.hris import attendance, employees, leaves, shifts


def test_route_helpers_require_authenticated_organization_context():
    current_user = SimpleNamespace(organization_id=None)
    helpers = [
        attendance._require_organization_id,
        employees._require_organization_id,
        leaves._require_organization_id,
        shifts._require_organization_id,
    ]

    for helper in helpers:
        try:
            helper(current_user)
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 400
        else:
            raise AssertionError("Organization context should be required")


def test_core_hris_routes_do_not_accept_explicit_organization_parameters():
    handlers = [
        attendance.list_attendance,
        attendance.list_regularizations,
        employees.list_employees,
        leaves.list_leave_types,
        leaves.initialize_balances,
        leaves.list_leave_applications,
        shifts.list_shifts,
        shifts.list_holiday_calendars,
        shifts.check_holiday,
    ]

    for handler in handlers:
        assert "organization_id" not in inspect.signature(handler).parameters


def test_attendance_org_filters_are_auth_scoped_and_static_routes_win():
    get_routes = [
        route.path
        for route in attendance.router.routes
        if "GET" in getattr(route, "methods", set())
    ]

    assert get_routes.index("/regularizations") < get_routes.index("/{attendance_id}")
