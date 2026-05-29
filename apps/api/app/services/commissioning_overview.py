from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
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
from app.services import final_validation, flag_adjustments, zone_leveling

PARAMETER_PAIRS = [
    ("Baja subida", "026D", "273"),
    ("Baja bajada", "026E", "274"),
    ("Media subida", "026F", "275"),
    ("Media bajada", "270", "276"),
    ("Alta subida", "271", "277"),
    ("Alta bajada", "272", "278"),
]

LOAD_STEP_CODES = {
    "mechanical_calibration_completed": "LOAD_CELL_MECHANICAL_CALIBRATION",
    "zero_full_memory_completed": "LOAD_MEMORY_ZERO_FULL",
    "overload_110_completed": "OVERLOAD_110_TEST",
}


async def get_commissioning_overview(session: AsyncSession, elevator_id: UUID) -> dict:
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
    workflow = await _get_workflow(session, elevator_id)
    latest_test_run = await _get_latest_test_run(session, elevator_id)
    workflow_summary = _workflow_summary(workflow) if workflow else None
    load_readiness = _load_readiness(workflow)
    parameter_matrix = await _parameter_matrix_summary(session, latest_test_run.id) if latest_test_run else _empty_parameter_matrix()
    zone_summary = await _zone_analysis_summary(session, latest_test_run.id) if latest_test_run else _empty_zone_analysis()
    flag_summary = await _flag_adjustment_summary(session, latest_test_run.id) if latest_test_run else _empty_flag_adjustments()
    final_summary = await _final_validation_summary(session, latest_test_run.id) if latest_test_run else _empty_final_validation()
    overall_status = _overall_status(workflow, workflow_summary, load_readiness, parameter_matrix, final_summary)

    return {
        "elevator": {
            "id": elevator.id,
            "code": elevator.code,
            "name": elevator.name,
            "project_id": project.id,
            "project_name": project.name,
            "status": elevator.status,
        },
        "workflow": workflow_summary,
        "latest_test_run": _latest_test_run_summary(latest_test_run) if latest_test_run else None,
        "load_readiness": load_readiness,
        "parameter_matrix": parameter_matrix,
        "zone_analysis": zone_summary,
        "flag_adjustments": flag_summary,
        "final_validation": final_summary,
        "overall_status": overall_status,
    }


async def _get_workflow(session: AsyncSession, elevator_id: UUID) -> CommissioningWorkflow | None:
    return await session.scalar(
        select(CommissioningWorkflow)
        .where(CommissioningWorkflow.elevator_id == elevator_id)
        .options(selectinload(CommissioningWorkflow.steps))
    )


async def _get_latest_test_run(session: AsyncSession, elevator_id: UUID) -> TestRun | None:
    return await session.scalar(
        select(TestRun)
        .where(TestRun.elevator_id == elevator_id)
        .order_by(TestRun.updated_at.desc(), TestRun.created_at.desc(), TestRun.id.desc())
        .limit(1)
        .options(selectinload(TestRun.test_type))
    )


def _workflow_summary(workflow: CommissioningWorkflow) -> dict:
    steps = sorted(workflow.steps, key=lambda step: step.sort_order)
    required_steps = [step for step in steps if step.is_required]
    completed_required = [step for step in required_steps if step.status == "completed"]
    critical_blockers = [step.title for step in required_steps if step.is_blocking and step.status != "completed"]
    return {
        "id": workflow.id,
        "status": workflow.status,
        "progress_percent": round((len(completed_required) / len(required_steps)) * 100, 2) if required_steps else 0.0,
        "completed_steps": len(completed_required),
        "total_steps": len(required_steps),
        "critical_blockers": critical_blockers,
        "steps": [
            {
                "code": step.code,
                "title": step.title,
                "status": step.status,
                "is_required": step.is_required,
                "completed_at": step.completed_at,
                "notes": step.notes,
            }
            for step in steps
        ],
    }


def _load_readiness(workflow: CommissioningWorkflow | None) -> dict:
    steps_by_code: dict[str, CommissioningStep] = {step.code: step for step in workflow.steps} if workflow else {}
    statuses = {
        key: (steps_by_code.get(code).status == "completed" if steps_by_code.get(code) else False)
        for key, code in LOAD_STEP_CODES.items()
    }
    warnings = []
    if not statuses["mechanical_calibration_completed"]:
        warnings.append("Calibración mecánica de pesacargas pendiente.")
    if not statuses["zero_full_memory_completed"]:
        warnings.append("Escritura 0% / 100% en memoria pendiente.")
    if not statuses["overload_110_completed"]:
        warnings.append("Prueba 110% de carga pendiente.")

    return {
        **statuses,
        "ready_for_leveling": all(statuses.values()),
        "warnings": warnings,
    }


async def _parameter_matrix_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    rows = (
        await session.execute(
            select(TestRunParameterValue, ParameterDefinition)
            .join(ParameterDefinition, TestRunParameterValue.parameter_definition_id == ParameterDefinition.id)
            .where(TestRunParameterValue.test_run_id == test_run_id)
        )
    ).all()
    values_by_code = {definition.code: value.decimal_value for value, definition in rows}
    ok_windows = 0
    warning_windows = 0
    missing_windows = 0
    warnings: list[str] = []

    for label, min_code, max_code in PARAMETER_PAIRS:
        min_value = values_by_code.get(min_code)
        max_value = values_by_code.get(max_code)
        if min_value is None or max_value is None:
            missing_windows += 1
            warnings.append(f"{label}: faltan parámetros MIN/MAX")
            continue
        window = max_value - min_value
        if max_value <= min_value:
            warning_windows += 1
            warnings.append(f"{label}: MAX <= MIN")
        elif window < 4:
            warning_windows += 1
            warnings.append(f"{label}: ventana menor a 4 unidades")
        elif window > 6:
            warning_windows += 1
            warnings.append(f"{label}: ventana mayor a 6 unidades")
        else:
            ok_windows += 1

    return {
        "ok_windows": ok_windows,
        "warning_windows": warning_windows,
        "missing_windows": missing_windows,
        "most_critical_warning": warnings[0] if warnings else None,
    }


async def _zone_analysis_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    analysis = await zone_leveling.get_zone_leveling_analysis(session, test_run_id)
    averages = [abs(entry["average_landing_mm"]) for entry in analysis["zones"] if entry["average_landing_mm"] is not None]
    warning_count = sum(len(entry["warnings"]) for entry in analysis["zones"]) + len(analysis["global_warnings"])
    has_data = any(entry["measurement_count"] > 0 for entry in analysis["zones"])
    return {
        "available": has_data,
        "rows_count": len(analysis["zones"]),
        "warnings_count": warning_count,
        "max_abs_average_landing_mm": max(averages) if averages else None,
    }


async def _flag_adjustment_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    response = await flag_adjustments.get_flag_adjustment_recommendations(session, test_run_id)
    summary = response["summary"]
    available = summary["floors_with_complete_data"] > 0 or summary["floors_partial_data"] > 0
    return {
        "available": available,
        "floors_requiring_adjustment": summary["floors_requiring_flag_adjustment"],
        "floors_ok": summary["floors_within_tolerance"],
        "floors_missing_data": summary["floors_missing_data"] + summary["floors_partial_data"],
        "max_abs_recommended_movement_mm": summary["max_abs_recommended_movement_mm"],
    }


async def _final_validation_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    response = await final_validation.get_final_validation_summary(session, test_run_id)
    summary = response["summary"]
    available = summary["floors_with_complete_data"] > 0 or summary["floors_partial_data"] > 0
    ready_to_close = (
        response["fhm_completed"]
        and available
        and summary["floors_out_of_tolerance"] == 0
        and summary["floors_missing_data"] == 0
        and summary["floors_partial_data"] == 0
    )
    return {
        "available": available,
        "fhm_completed": response["fhm_completed"],
        "floors_within_tolerance": summary["floors_within_tolerance"],
        "floors_out_of_tolerance": summary["floors_out_of_tolerance"],
        "floors_missing_data": summary["floors_missing_data"] + summary["floors_partial_data"],
        "within_tolerance_percent": summary["within_tolerance_percent"],
        "ready_to_close": ready_to_close,
    }


def _overall_status(
    workflow: CommissioningWorkflow | None,
    workflow_summary: dict | None,
    load_readiness: dict,
    parameter_matrix: dict,
    final_summary: dict,
) -> dict:
    if workflow is None or workflow_summary is None or workflow_summary["completed_steps"] == 0:
        return {"status": "not_started", "label": "No iniciado", "reasons": ["Workflow de commissioning no iniciado."]}

    reasons: list[str] = []
    if not load_readiness["ready_for_leveling"]:
        reasons.extend(load_readiness["warnings"])
    if workflow_summary["critical_blockers"]:
        reasons.extend([f"Bloqueo crítico: {item}" for item in workflow_summary["critical_blockers"]])
    if parameter_matrix["warning_windows"] > 0:
        reasons.append(f"{parameter_matrix['warning_windows']} ventanas de parámetros requieren revisión.")
    if parameter_matrix["missing_windows"] > 0:
        reasons.append(f"{parameter_matrix['missing_windows']} ventanas de parámetros sin datos completos.")
    if final_summary["floors_out_of_tolerance"] > 0:
        reasons.append(f"{final_summary['floors_out_of_tolerance']} pisos fuera de tolerancia en validación final.")
    if final_summary["floors_missing_data"] > 0:
        reasons.append(f"{final_summary['floors_missing_data']} pisos sin validación final completa.")
    if not final_summary["fhm_completed"]:
        reasons.append("FHM no está completado.")

    required_complete = workflow_summary["completed_steps"] == workflow_summary["total_steps"]
    ready_to_close = required_complete and final_summary["ready_to_close"] and not reasons
    if workflow.status == "completed" and ready_to_close:
        return {"status": "completed", "label": "Completado", "reasons": []}
    if ready_to_close:
        return {"status": "ready_to_close", "label": "Listo para cierre", "reasons": []}
    if reasons:
        return {"status": "needs_attention", "label": "Requiere revisión", "reasons": reasons}
    return {"status": "in_progress", "label": "En proceso", "reasons": ["Aún hay pasos requeridos pendientes."]}


def _latest_test_run_summary(test_run: TestRun) -> dict:
    test_type: TestType = test_run.test_type
    return {
        "id": test_run.id,
        "name": test_run.title or test_type.name,
        "status": test_run.status,
        "technician_name": test_run.technician_name,
        "created_at": test_run.created_at,
    }


def _empty_parameter_matrix() -> dict:
    return {"ok_windows": 0, "warning_windows": 0, "missing_windows": 6, "most_critical_warning": None}


def _empty_zone_analysis() -> dict:
    return {"available": False, "rows_count": 0, "warnings_count": 0, "max_abs_average_landing_mm": None}


def _empty_flag_adjustments() -> dict:
    return {"available": False, "floors_requiring_adjustment": 0, "floors_ok": 0, "floors_missing_data": 0, "max_abs_recommended_movement_mm": None}


def _empty_final_validation() -> dict:
    return {
        "available": False,
        "fhm_completed": False,
        "floors_within_tolerance": 0,
        "floors_out_of_tolerance": 0,
        "floors_missing_data": 0,
        "within_tolerance_percent": 0.0,
        "ready_to_close": False,
    }
