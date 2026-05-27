"""HRIS separation route contract tests."""

import inspect
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.hris import separation


def test_tenant_organization_requires_authenticated_context():
    user_org_id = uuid4()
    current_user = SimpleNamespace(organization_id=user_org_id)

    assert separation._require_organization_id(current_user) == user_org_id


def test_separation_mutations_use_authenticated_actor():
    mutation_handlers = [
        separation.initiate_separation,
        separation.approve_separation,
        separation.reject_separation,
        separation.withdraw_separation,
        separation.update_clearance,
        separation.calculate_fnf,
        separation.approve_fnf,
        separation.process_fnf_payment,
        separation.create_checklist_item,
        separation.seed_default_checklist,
    ]

    for handler in mutation_handlers:
        assert "current_user" in inspect.signature(handler).parameters


def test_separation_routes_do_not_use_placeholder_actor_ids():
    source = inspect.getsource(separation)

    assert "00000000-0000-0000-0000-000000000000" not in source
    assert "Replace with current_user.id" not in source


def test_checklist_routes_are_registered_before_dynamic_separation_id_route():
    get_routes = [
        route.path
        for route in separation.router.routes
        if "GET" in getattr(route, "methods", set())
    ]

    assert get_routes.index("/separation/checklist") < get_routes.index(
        "/separation/{separation_id}"
    )


def test_checklist_routes_do_not_accept_explicit_organization_parameters():
    handlers = [
        separation.create_checklist_item,
        separation.list_checklist_items,
        separation.seed_default_checklist,
    ]

    for handler in handlers:
        assert "organization_id" not in inspect.signature(handler).parameters
