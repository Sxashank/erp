"""Workflow API package."""

from fastapi import APIRouter

from app.api.v1.workflow.definitions import router as definitions_router
from app.api.v1.workflow.tasks import router as tasks_router
from app.api.v1.workflow.instances import router as instances_router
from app.api.v1.workflow.templates import router as templates_router

router = APIRouter()

router.include_router(definitions_router, prefix="/definitions", tags=["Workflow Definitions"])
router.include_router(tasks_router, prefix="/tasks", tags=["Workflow Tasks"])
router.include_router(instances_router, prefix="/instances", tags=["Workflow Instances"])
router.include_router(templates_router, prefix="/templates", tags=["Notification Templates"])
