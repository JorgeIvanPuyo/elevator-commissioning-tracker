from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.db.models import (
    CommissioningStep,
    CommissioningWorkflow,
    Elevator,
    ParameterDefinition,
    Project,
    TestRun,
    TestRunParameterValue,
    TestType,
)
from app.schemas.commissioning import CommissioningStepUpdate, CommissioningWorkflowUpdate
from app.services.elevators import get_elevator
from app.services.leveling_summary import get_leveling_summary
from app.services.test_run_parameters import list_test_run_parameters

WORKFLOW_STATUSES = {"not_started", "in_progress", "completed", "blocked", "cancelled"}
STEP_STATUSES = {"pending", "in_progress", "completed", "skipped", "not_applicable", "blocked"}
CRITICAL_PARAMETER_CODES = ["026D", "026E", "026F", "270", "271", "272", "273", "274", "275", "276", "277", "278"]

DEFAULT_WORKFLOW_STEPS = [
    {
        "code": "LOAD_CELL_MECHANICAL_CALIBRATION",
        "title": "Calibración mecánica de pesacargas",
        "description": (
            "Verificar y ajustar mecánicamente los potenciómetros/sensores de pesacargas antes de cualquier proceso de "
            "nivelación. Si esta lectura no es confiable, la nivelación posterior no debe continuar."
        ),
        "is_required": True,
        "is_blocking": True,
        "sort_order": 1,
    },
    {
        "code": "LOAD_MEMORY_ZERO_FULL",
        "title": "Escritura 0% / 100% en memoria",
        "description": (
            "Ejecutar los procesos de escritura del valor de carga al 0% y al 100% en memoria del ascensor. Estos "
            "procesos corresponden a A61E y A62E, pero no son parámetros HEX editables."
        ),
        "is_required": True,
        "is_blocking": True,
        "sort_order": 2,
    },
    {
        "code": "OVERLOAD_110_TEST",
        "title": "Prueba 110% de carga",
        "description": (
            "Verificar alarma de sobrepeso, bloqueo de llamadas mientras el exceso de carga permanece en cabina, "
            "indicador FULL en PB y recuperación normal al retirar el peso."
        ),
        "is_required": True,
        "is_blocking": True,
        "sort_order": 3,
    },
    {
        "code": "AUTO_LEVELING_A65E_A66E",
        "title": "Calibración automática de nivelación A65E/A66E",
        "description": (
            "Proceso opcional/recomendado cuando la nivelación inicial está muy desajustada o errática. A65E corresponde "
            "a 0% de carga y A66E a 100% de carga."
        ),
        "is_required": False,
        "is_blocking": False,
        "sort_order": 4,
    },
    {
        "code": "AUTO_GAIN_COMPENSATION_A67E",
        "title": "Calibración automática de ganancias A67E",
        "description": (
            "Proceso opcional/recomendado si la cabina presenta tirones, deslizamientos, frenado/arranque errático o "
            "comportamiento inestable."
        ),
        "is_required": False,
        "is_blocking": False,
        "sort_order": 5,
    },
    {
        "code": "ZONE_FINE_LEVELING",
        "title": "Nivelación fina por zonas",
        "description": (
            "Dividir el elevador en zona baja, media y alta. Medir cinco pisos consecutivos por zona en subida y bajada, "
            "calcular promedio de aterrizaje y usarlo para sugerir ajuste de parámetros bias MIN/MAX por zona y dirección."
        ),
        "is_required": True,
        "is_blocking": False,
        "sort_order": 6,
    },
    {
        "code": "FLOOR_BY_FLOOR_MEASUREMENT",
        "title": "Medición piso a piso",
        "description": (
            "Medir nivelación final piso a piso en subida y bajada para determinar si cada piso queda dentro de tolerancia "
            "y si requiere movimiento físico de bandera."
        ),
        "is_required": True,
        "is_blocking": False,
        "sort_order": 7,
    },
    {
        "code": "FLAG_ADJUSTMENT",
        "title": "Ajuste físico de banderas",
        "description": "Mover físicamente las banderas recomendadas para acercar el nivel final de cabina a 0 mm respecto al pasillo.",
        "is_required": True,
        "is_blocking": False,
        "sort_order": 8,
    },
    {
        "code": "FHM_RUN",
        "title": "Ejecución FHM",
        "description": "Ejecutar viaje FHM para almacenar en memoria las nuevas alturas/distancias de pisos después del ajuste físico de banderas.",
        "is_required": True,
        "is_blocking": False,
        "sort_order": 9,
    },
    {
        "code": "FINAL_LEVELING_VALIDATION",
        "title": "Validación final de nivelación",
        "description": "Repetir medición final y validar que los pisos requeridos estén dentro de tolerancia ±5 mm.",
        "is_required": True,
        "is_blocking": False,
        "sort_order": 10,
    },
]


async def get_workflow_for_elevator(session: AsyncSession, elevator_id: UUID) -> CommissioningWorkflow:
    await get_elevator(session, elevator_id)
    workflow = await _get_workflow_by_elevator_id(session, elevator_id)
    if workflow is None:
        raise NotFoundError("Commissioning workflow not found")
    return workflow


async def initialize_workflow_for_elevator(session: AsyncSession, elevator_id: UUID) -> CommissioningWorkflow:
    await get_elevator(session, elevator_id)
    existing = await _get_workflow_by_elevator_id(session, elevator_id)
    if existing is not None:
        return existing

    workflow = CommissioningWorkflow(elevator_id=elevator_id, status="not_started")
    session.add(workflow)
    await session.flush()
    for step in DEFAULT_WORKFLOW_STEPS:
        session.add(CommissioningStep(workflow_id=workflow.id, status="pending", **step))

    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        existing_after_conflict = await _get_workflow_by_elevator_id(session, elevator_id)
        if existing_after_conflict is not None:
            return existing_after_conflict
        raise ConflictError("Commissioning workflow could not be initialized") from error

    return await get_workflow(session, workflow.id)


async def update_workflow(session: AsyncSession, workflow_id: UUID, payload: CommissioningWorkflowUpdate) -> CommissioningWorkflow:
    workflow = await get_workflow(session, workflow_id)
    data = payload.model_dump(exclude_unset=True)
    status = data.get("status")
    if status is not None and status not in WORKFLOW_STATUSES:
        raise AppError("Invalid commissioning workflow status")

    for field, value in data.items():
        setattr(workflow, field, value)

    await session.commit()
    return await get_workflow(session, workflow.id)


async def update_step(session: AsyncSession, step_id: UUID, payload: CommissioningStepUpdate) -> CommissioningStep:
    step = await session.get(CommissioningStep, step_id)
    if step is None:
        raise NotFoundError("Commissioning step not found")

    data = payload.model_dump(exclude_unset=True)
    status = data.get("status")
    if status is not None and status not in STEP_STATUSES:
        raise AppError("Invalid commissioning step status")

    for field, value in data.items():
        setattr(step, field, value)

    if status == "completed" and step.completed_at is None:
        step.completed_at = datetime.now(UTC)
    elif status is not None and status != "completed":
        step.completed_at = None

    await session.commit()
    await session.refresh(step)
    return step


async def get_workflow(session: AsyncSession, workflow_id: UUID) -> CommissioningWorkflow:
    workflow = await session.scalar(
        select(CommissioningWorkflow)
        .where(CommissioningWorkflow.id == workflow_id)
        .options(selectinload(CommissioningWorkflow.steps))
    )
    if workflow is None:
        raise NotFoundError("Commissioning workflow not found")
    return workflow


async def get_operational_dashboard(session: AsyncSession, elevator_id: UUID) -> dict:
    row = (
        await session.execute(
            select(Elevator, Project)
            .join(Project, Elevator.project_id == Project.id)
            .where(Elevator.id == elevator_id)
        )
    ).one_or_none()
    if row is None:
        raise NotFoundError("Elevator not found")
    elevator, project = row
    workflow = await _get_workflow_by_elevator_id(session, elevator_id)
    latest_test_run = await _get_latest_test_run(session, elevator_id)
    leveling_summary = None
    parameter_summary = {"latest_test_run_id": None, "warning_count": 0, "critical_values": []}

    if latest_test_run is not None:
        parameter_summary = await _build_parameter_summary(session, latest_test_run.id)
        try:
            full_summary = await get_leveling_summary(session, latest_test_run.id)
            leveling_summary = {
                "test_run_id": full_summary["test_run_id"],
                "measurement_count": full_summary["measurement_count"],
                "required_floor_count": full_summary["required_floor_count"],
                "measured_required_floor_count": full_summary["measured_required_floor_count"],
                "coverage_percentage": full_summary["coverage_percentage"],
                "within_final_tolerance_percentage": full_summary["within_final_tolerance_percentage"],
                "overall_status": full_summary["overall_status"],
            }
        except NotFoundError:
            leveling_summary = None

    return {
        "elevator": {
            "id": elevator.id,
            "project_id": elevator.project_id,
            "code": elevator.code,
            "name": elevator.name,
            "status": elevator.status,
            "floor_count": elevator.floor_count,
            "controller_model": elevator.controller_model,
            "machine_room": elevator.machine_room,
        },
        "project": {
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "location": project.location,
        },
        "workflow": _workflow_summary(workflow) if workflow is not None else None,
        "latest_test_run": _latest_test_run_summary(latest_test_run) if latest_test_run is not None else None,
        "leveling_summary": leveling_summary,
        "parameter_summary": parameter_summary,
        "quick_links": {
            "latest_test_run_id": latest_test_run.id if latest_test_run is not None else None,
            "project_id": project.id,
            "elevator_id": elevator.id,
        },
    }


async def _get_workflow_by_elevator_id(session: AsyncSession, elevator_id: UUID) -> CommissioningWorkflow | None:
    return await session.scalar(
        select(CommissioningWorkflow)
        .where(CommissioningWorkflow.elevator_id == elevator_id)
        .options(selectinload(CommissioningWorkflow.steps))
    )


async def _get_latest_test_run(session: AsyncSession, elevator_id: UUID) -> TestRun | None:
    return await session.scalar(
        select(TestRun)
        .where(TestRun.elevator_id == elevator_id)
        .order_by(TestRun.created_at.desc(), TestRun.id.desc())
        .limit(1)
        .options(selectinload(TestRun.test_type))
    )


async def _build_parameter_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    parameter_response = await list_test_run_parameters(session, test_run_id)
    warning_count = len(parameter_response["validation_warnings"])
    rows = (
        await session.execute(
            select(TestRunParameterValue, ParameterDefinition)
            .join(ParameterDefinition, TestRunParameterValue.parameter_definition_id == ParameterDefinition.id)
            .where(TestRunParameterValue.test_run_id == test_run_id, ParameterDefinition.code.in_(CRITICAL_PARAMETER_CODES))
            .order_by(ParameterDefinition.sort_order.asc(), ParameterDefinition.code.asc())
        )
    ).all()
    return {
        "latest_test_run_id": test_run_id,
        "warning_count": warning_count,
        "critical_values": [
            {
                "parameter_code": definition.code,
                "parameter_name": definition.name,
                "hex_value": value.hex_value,
                "decimal_value": value.decimal_value,
            }
            for value, definition in rows
        ],
    }


def _workflow_summary(workflow: CommissioningWorkflow) -> dict:
    steps = list(workflow.steps)
    required_steps = [step for step in steps if step.is_required]
    completed_steps = [step for step in steps if step.status == "completed"]
    required_pending_steps = [step for step in required_steps if step.status != "completed"]
    blocking_pending_steps = [step for step in required_steps if step.is_blocking and step.status != "completed"]
    return {
        "id": workflow.id,
        "status": workflow.status,
        "technician_name": workflow.technician_name,
        "total_steps": len(steps),
        "completed_steps": len(completed_steps),
        "required_steps": len(required_steps),
        "required_pending_steps": len(required_pending_steps),
        "required_blocking_steps_incomplete": len(blocking_pending_steps),
        "progress_percentage": round((len(completed_steps) / len(steps)) * 100, 2) if steps else 0.0,
    }


def _latest_test_run_summary(test_run: TestRun) -> dict:
    test_type: TestType = test_run.test_type
    return {
        "id": test_run.id,
        "title": test_run.title,
        "name": test_run.title or test_type.name,
        "status": test_run.status,
        "test_type_code": test_type.code,
        "test_type_name": test_type.name,
        "technician_name": test_run.technician_name,
        "created_at": test_run.created_at,
        "updated_at": test_run.updated_at,
    }
