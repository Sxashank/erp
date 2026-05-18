"""Payroll salary tenant and route contract tests."""

import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.payroll import payroll, salary
from app.services.payroll.salary_service import EmployeeSalaryService


def test_tenant_organization_prefers_authenticated_user_org():
    user_org_id = uuid4()
    spoofed_org_id = uuid4()
    current_user = SimpleNamespace(organization_id=user_org_id)

    assert salary._tenant_organization_id(current_user, spoofed_org_id) == user_org_id


def test_tenant_organization_requires_context_for_platform_user():
    current_user = SimpleNamespace(organization_id=None)

    with pytest.raises(HTTPException) as exc_info:
        salary._tenant_organization_id(current_user)

    assert exc_info.value.status_code == 400


def test_request_org_rejects_cross_tenant_salary_config_body():
    current_user = SimpleNamespace(organization_id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        salary._assert_request_org(current_user, uuid4())

    assert exc_info.value.status_code == 403


def test_employee_salary_routes_are_auth_scoped_and_static_routes_win():
    assert "organization_id" not in inspect.signature(salary.list_employee_salaries).parameters
    assert "organization_id" not in inspect.signature(salary.create_employee_salary).parameters

    get_routes = [
        route.path
        for route in salary.router.routes
        if "GET" in getattr(route, "methods", set())
    ]

    assert get_routes.index("/employee-salaries/employee/{employee_id}/current") < get_routes.index(
        "/employee-salaries/{id}"
    )


def test_employee_salary_service_requires_tenant_context_for_listing_and_create():
    list_signature = inspect.signature(EmployeeSalaryService.list)
    create_signature = inspect.signature(EmployeeSalaryService.create)

    assert list_signature.parameters["organization_id"].default is inspect.Parameter.empty
    assert create_signature.parameters["organization_id"].default is inspect.Parameter.empty


def test_payroll_statutory_routes_prefer_authenticated_user_org():
    user_org_id = uuid4()
    spoofed_org_id = uuid4()
    current_user = SimpleNamespace(organization_id=user_org_id)

    assert payroll._tenant_organization_id(current_user, spoofed_org_id) == user_org_id


def test_payroll_statutory_rejects_cross_tenant_body():
    current_user = SimpleNamespace(organization_id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        payroll._assert_request_org(current_user, uuid4())

    assert exc_info.value.status_code == 403


def test_payroll_batch_and_payslip_routes_are_auth_scoped():
    batch_handlers = [
        payroll.get_payroll_batch,
        payroll.update_payroll_batch,
        payroll.process_payroll_batch,
        payroll.approve_payroll_batch,
        payroll.mark_payroll_batch_paid,
        payroll.export_payroll_bank_file,
        payroll.post_payroll_to_gl,
    ]
    payslip_handlers = [
        payroll.list_payslips,
        payroll.get_employee_payslips,
        payroll.get_payslip,
        payroll.update_payslip,
    ]

    for handler in [*batch_handlers, *payslip_handlers]:
        assert "organization_id" not in inspect.signature(handler).parameters


def test_payroll_static_payslip_routes_win():
    get_routes = [
        route.path
        for route in payroll.router.routes
        if "GET" in getattr(route, "methods", set())
    ]

    assert get_routes.index("/payslips/employee/{employee_id}") < get_routes.index("/payslips/{id}")
