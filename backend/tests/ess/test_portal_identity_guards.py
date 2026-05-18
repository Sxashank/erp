"""ESS portal endpoint identity isolation tests."""

import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.ess import auth, helpdesk, it_declaration, reimbursement


class ClaimServiceStub:
    def __init__(self, claim):
        self.claim = claim

    async def get_claim_by_id(self, claim_id, include_items=True):
        return self.claim


class TicketServiceStub:
    def __init__(self, ticket):
        self.ticket = ticket

    async def get_ticket_by_id(
        self,
        ticket_id,
        include_comments=True,
        include_history=False,
    ):
        return self.ticket


class DeclarationServiceStub:
    def __init__(self, declaration):
        self.declaration = declaration

    async def get_declaration_by_id(self, declaration_id):
        return self.declaration


@pytest.mark.asyncio
async def test_reimbursement_claim_guard_allows_owned_claim():
    employee_id = uuid4()
    claim = SimpleNamespace(employee_id=employee_id)

    result = await reimbursement._get_owned_claim(
        ClaimServiceStub(claim),
        uuid4(),
        employee_id,
    )

    assert result is claim


@pytest.mark.asyncio
async def test_reimbursement_claim_guard_hides_other_employee_claim():
    claim = SimpleNamespace(employee_id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        await reimbursement._get_owned_claim(
            ClaimServiceStub(claim),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_helpdesk_ticket_guard_allows_owned_ticket():
    employee_id = uuid4()
    ticket = SimpleNamespace(employee_id=employee_id)

    result = await helpdesk._get_owned_ticket(
        TicketServiceStub(ticket),
        uuid4(),
        employee_id,
    )

    assert result is ticket


@pytest.mark.asyncio
async def test_helpdesk_ticket_guard_hides_other_employee_ticket():
    ticket = SimpleNamespace(employee_id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        await helpdesk._get_owned_ticket(
            TicketServiceStub(ticket),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 404


def test_reimbursement_ess_routes_do_not_accept_identity_query_params():
    unsafe_params = {"organization_id", "ess_user_id", "employee_id"}
    route_handlers = [
        reimbursement.get_categories,
        reimbursement.create_claim,
        reimbursement.get_claims,
        reimbursement.get_claim_summary,
        reimbursement.get_claim_detail,
        reimbursement.update_claim,
        reimbursement.submit_claim,
        reimbursement.cancel_claim,
        reimbursement.delete_claim,
        reimbursement.add_line_item,
        reimbursement.remove_line_item,
    ]

    for handler in route_handlers:
        assert unsafe_params.isdisjoint(inspect.signature(handler).parameters)


def test_helpdesk_ess_routes_do_not_accept_identity_query_params():
    unsafe_params = {"organization_id", "ess_user_id", "employee_id"}
    route_handlers = [
        helpdesk.get_categories,
        helpdesk.create_ticket,
        helpdesk.get_tickets,
        helpdesk.get_ticket_summary,
        helpdesk.get_ticket_detail,
        helpdesk.add_comment,
        helpdesk.close_ticket,
        helpdesk.reopen_ticket,
        helpdesk.submit_feedback,
    ]

    for handler in route_handlers:
        assert unsafe_params.isdisjoint(inspect.signature(handler).parameters)


@pytest.mark.asyncio
async def test_it_declaration_guard_allows_owned_declaration():
    employee_id = uuid4()
    declaration = SimpleNamespace(employee_id=employee_id)

    result = await it_declaration._get_owned_declaration(
        DeclarationServiceStub(declaration),
        uuid4(),
        employee_id,
    )

    assert result is declaration


@pytest.mark.asyncio
async def test_it_declaration_guard_hides_other_employee_declaration():
    declaration = SimpleNamespace(employee_id=uuid4())

    with pytest.raises(HTTPException) as exc_info:
        await it_declaration._get_owned_declaration(
            DeclarationServiceStub(declaration),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 404


def test_it_declaration_ess_routes_do_not_accept_identity_query_params():
    unsafe_params = {"organization_id", "ess_user_id", "employee_id"}
    route_handlers = [
        it_declaration.get_sections,
        it_declaration.get_declarations,
        it_declaration.create_regularization,
        it_declaration.get_regularizations,
        it_declaration.cancel_regularization,
        it_declaration.get_or_create_declaration,
        it_declaration.get_declaration_detail,
        it_declaration.update_tax_regime,
        it_declaration.add_declaration_item,
        it_declaration.update_declaration_item,
        it_declaration.delete_declaration_item,
        it_declaration.update_hra_details,
        it_declaration.add_hra_receipt,
        it_declaration.update_home_loan_details,
        it_declaration.submit_declaration,
        it_declaration.submit_proofs,
        it_declaration.calculate_tax,
    ]

    for handler in route_handlers:
        assert unsafe_params.isdisjoint(inspect.signature(handler).parameters)


def test_ess_auth_routes_do_not_accept_identity_query_params():
    unsafe_params = {"ess_user_id", "employee_id", "organization_id"}
    route_handlers = [
        auth.logout,
        auth.logout_all_sessions,
        auth.get_active_sessions,
        auth.revoke_session,
        auth.register_device,
        auth.register_device_legacy,
    ]

    for handler in route_handlers:
        assert unsafe_params.isdisjoint(inspect.signature(handler).parameters)
