"""HRIS core route tenant contract tests."""

import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.hris import attendance, employees, leaves, shifts


@pytest.mark.parametrize("module", [attendance, employees, leaves, shifts])
def test_tenant_organization_prefers_authenticated_user_org(module):
    user_org_id = uuid4()
    spoofed_org_id = uuid4()
    current_user = SimpleNamespace(organization_id=user_org_id)

    assert module._tenant_organization_id(current_user, spoofed_org_id) == user_org_id


@pytest.mark.parametrize("module", [attendance, employees, leaves, shifts])
def test_tenant_organization_requires_context_for_platform_user(module):
    current_user = SimpleNamespace(organization_id=None)

    with pytest.raises(HTTPException) as exc_info:
        module._tenant_organization_id(current_user)

    assert exc_info.value.status_code == 400


@pytest.mark.parametrize("module", [attendance, employees, leaves, shifts])
def test_request_org_rejects_cross_tenant_body(module):
    current_user = SimpleNamespace(organization_id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        module._assert_request_org(current_user, uuid4())

    assert exc_info.value.status_code == 403


def test_leave_org_query_params_are_optional():
    handlers = [
        leaves.list_leave_types,
        leaves.initialize_balances,
        leaves.list_leave_applications,
    ]

    for handler in handlers:
        parameter = inspect.signature(handler).parameters["organization_id"]
        assert parameter.default is None


def test_shift_org_query_params_are_optional():
    handlers = [
        shifts.list_shifts,
        shifts.list_holiday_calendars,
        shifts.check_holiday,
    ]

    for handler in handlers:
        parameter = inspect.signature(handler).parameters["organization_id"]
        assert parameter.default is None


def test_attendance_org_filters_are_auth_scoped_and_static_routes_win():
    handlers = [
        attendance.list_attendance,
        attendance.list_regularizations,
    ]

    for handler in handlers:
        parameter = inspect.signature(handler).parameters["organization_id"]
        assert parameter.default is None

    get_routes = [
        route.path
        for route in attendance.router.routes
        if "GET" in getattr(route, "methods", set())
    ]

    assert get_routes.index("/regularizations") < get_routes.index("/{attendance_id}")


def test_employee_org_query_params_are_optional():
    parameter = inspect.signature(employees.list_employees).parameters["organization_id"]
    assert parameter.default is None
