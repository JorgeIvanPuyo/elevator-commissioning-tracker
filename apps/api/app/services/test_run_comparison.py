from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.db.models import TestRun, TestType
from app.services import leveling_summary as leveling_summary_service
from app.services import test_run_parameters as parameter_service

STATUS_SCORE = {
    "not_required": None,
    "pending": 0,
    "critical": 1,
    "warning": 2,
    "ok": 3,
}


async def list_comparison_candidates(session: AsyncSession, test_run_id: UUID) -> list[dict]:
    current_run = await _get_test_run_with_type(session, test_run_id)
    test_run, _ = current_run
    rows = (
        await session.execute(
            select(TestRun, TestType)
            .join(TestType, TestRun.test_type_id == TestType.id)
            .where(TestRun.elevator_id == test_run.elevator_id, TestRun.id != test_run_id)
            .order_by(TestRun.created_at.desc())
        )
    ).all()

    candidates = []
    for candidate_run, candidate_type in rows:
        summary = await leveling_summary_service.get_leveling_summary(session, candidate_run.id)
        candidates.append(
            {
                **_brief(candidate_run, candidate_type),
                "coverage_percentage": summary["coverage_percentage"],
                "within_final_tolerance_percentage": summary["within_final_tolerance_percentage"],
                "acceptable_renivelation_percentage": summary["acceptable_renivelation_percentage"],
            }
        )
    return candidates


async def compare_test_runs(session: AsyncSession, test_run_id: UUID, baseline_test_run_id: UUID) -> dict:
    current_run, current_type = await _get_test_run_with_type(session, test_run_id)
    baseline_run, baseline_type = await _get_test_run_with_type(session, baseline_test_run_id)
    if current_run.elevator_id != baseline_run.elevator_id:
        raise AppError("Test runs must belong to the same elevator")

    current_summary = await leveling_summary_service.get_leveling_summary(session, current_run.id)
    baseline_summary = await leveling_summary_service.get_leveling_summary(session, baseline_run.id)
    global_metrics = _build_global_metrics(baseline_summary, current_summary)
    floor_comparisons = _build_floor_comparisons(baseline_summary, current_summary)
    parameter_comparisons = await _build_parameter_comparisons(session, baseline_run.id, current_run.id)
    overall_trend = _overall_trend(global_metrics, floor_comparisons)

    return {
        "baseline_test_run": _brief(baseline_run, baseline_type),
        "current_test_run": _brief(current_run, current_type),
        "global_metrics": global_metrics,
        "floor_comparisons": floor_comparisons,
        "parameter_comparisons": parameter_comparisons,
        "overall_trend": overall_trend,
        "summary_text": _summary_text(overall_trend, global_metrics, floor_comparisons),
    }


async def _get_test_run_with_type(session: AsyncSession, test_run_id: UUID) -> tuple[TestRun, TestType]:
    row = (
        await session.execute(
            select(TestRun, TestType).join(TestType, TestRun.test_type_id == TestType.id).where(TestRun.id == test_run_id)
        )
    ).one_or_none()
    if row is None:
        raise NotFoundError("Test run not found")
    return row


def _brief(test_run: TestRun, test_type: TestType) -> dict:
    return {
        "id": test_run.id,
        "title": test_run.title,
        "name": test_run.title or test_type.name,
        "test_type_code": test_type.code,
        "test_type_name": test_type.name,
        "status": test_run.status,
        "technician_name": test_run.technician_name,
        "started_at": test_run.started_at,
        "completed_at": test_run.completed_at,
        "created_at": test_run.created_at,
    }


def _build_global_metrics(baseline: dict, current: dict) -> list[dict]:
    metrics = [
        ("coverage_percent", "Cobertura", baseline["coverage_percentage"], current["coverage_percentage"], True),
        (
            "final_tolerance_percent",
            "Tolerancia final",
            baseline["within_final_tolerance_percentage"],
            current["within_final_tolerance_percentage"],
            True,
        ),
        (
            "acceptable_releveling_percent",
            "Renivelación aceptable",
            baseline["acceptable_renivelation_percentage"],
            current["acceptable_renivelation_percentage"],
            True,
        ),
        ("hysteresis_ok_percent", "Histerisis correcta", baseline["hysteresis_ok_percentage"], current["hysteresis_ok_percentage"], True),
        ("measured_floor_count", "Pisos medidos", baseline["measured_required_floor_count"], current["measured_required_floor_count"], True),
        ("critical_floor_count", "Pisos críticos", _critical_count(baseline), _critical_count(current), False),
    ]
    return [
        {
            "metric": metric,
            "label": label,
            "baseline_value": baseline_value,
            "current_value": current_value,
            "delta": _delta(baseline_value, current_value),
            "trend": _metric_trend(baseline_value, current_value, higher_is_better),
        }
        for metric, label, baseline_value, current_value, higher_is_better in metrics
    ]


def _critical_count(summary: dict) -> int:
    return len([floor for floor in summary["floor_summaries"] if floor["status"] == "critical"])


def _delta(baseline_value: float | int | None, current_value: float | int | None) -> float | int | None:
    if baseline_value is None or current_value is None:
        return None
    return round(current_value - baseline_value, 2)


def _metric_trend(baseline_value: float | int | None, current_value: float | int | None, higher_is_better: bool) -> str:
    if baseline_value is None or current_value is None:
        return "not_comparable"
    if current_value == baseline_value:
        return "unchanged"
    improved = current_value > baseline_value if higher_is_better else current_value < baseline_value
    return "improved" if improved else "worsened"


def _build_floor_comparisons(baseline: dict, current: dict) -> list[dict]:
    baseline_by_floor = {floor["floor_id"]: floor for floor in baseline["floor_summaries"]}
    current_by_floor = {floor["floor_id"]: floor for floor in current["floor_summaries"]}
    floor_ids = set(baseline_by_floor) | set(current_by_floor)
    comparisons = []
    for floor_id in floor_ids:
        baseline_floor = baseline_by_floor.get(floor_id)
        current_floor = current_by_floor.get(floor_id)
        baseline_final = _representative_final_mm(baseline_floor) if baseline_floor else None
        current_final = _representative_final_mm(current_floor) if current_floor else None
        comparisons.append(
            {
                "floor_id": floor_id,
                "floor_label": (current_floor or baseline_floor)["floor_label"],
                "baseline_status": baseline_floor["status"] if baseline_floor else "not_comparable",
                "current_status": current_floor["status"] if current_floor else "not_comparable",
                "baseline_final_mm": baseline_final,
                "current_final_mm": current_final,
                "absolute_delta_mm": _absolute_error_delta(baseline_final, current_final),
                "trend": _floor_trend(baseline_floor, current_floor, baseline_final, current_final),
            }
        )
    return sorted(comparisons, key=lambda item: (baseline_by_floor.get(item["floor_id"]) or current_by_floor[item["floor_id"]])["sort_order"])


def _representative_final_mm(floor_summary: dict | None) -> int | None:
    if floor_summary is None:
        return None
    values = [value for value in floor_summary["final_values_mm"].values() if value is not None]
    if not values:
        return None
    return max(values, key=lambda value: abs(value))


def _absolute_error_delta(baseline_value: int | None, current_value: int | None) -> int | None:
    if baseline_value is None or current_value is None:
        return None
    return abs(current_value) - abs(baseline_value)


def _floor_trend(baseline_floor: dict | None, current_floor: dict | None, baseline_final: int | None, current_final: int | None) -> str:
    if baseline_floor is None or baseline_final is None:
        return "newly_measured" if current_final is not None else "not_comparable"
    if current_floor is None or current_final is None:
        return "missing_current"

    baseline_ok = abs(baseline_final) <= 5
    current_ok = abs(current_final) <= 5
    if not baseline_ok and current_ok:
        return "improved"
    if baseline_ok and not current_ok:
        return "worsened"

    baseline_error = abs(baseline_final)
    current_error = abs(current_final)
    if current_error < baseline_error:
        return "improved"
    if current_error > baseline_error:
        return "worsened"

    baseline_score = STATUS_SCORE.get(baseline_floor["status"])
    current_score = STATUS_SCORE.get(current_floor["status"])
    if baseline_score is None or current_score is None:
        return "not_comparable"
    if current_score > baseline_score:
        return "improved"
    if current_score < baseline_score:
        return "worsened"
    return "unchanged"


async def _build_parameter_comparisons(session: AsyncSession, baseline_test_run_id: UUID, current_test_run_id: UUID) -> list[dict]:
    baseline_parameters = await parameter_service.list_test_run_parameters(session, baseline_test_run_id)
    current_parameters = await parameter_service.list_test_run_parameters(session, current_test_run_id)
    baseline_by_code = {value["parameter_code"]: value for value in baseline_parameters["values"]}
    current_by_code = {value["parameter_code"]: value for value in current_parameters["values"]}
    current_warning_by_code = _warnings_by_code(current_parameters["validation_warnings"])
    codes = sorted(set(baseline_by_code) | set(current_by_code))
    comparisons = []
    for code in codes:
        baseline_value = baseline_by_code.get(code)
        current_value = current_by_code.get(code)
        baseline_decimal = baseline_value["decimal_value"] if baseline_value else None
        current_decimal = current_value["decimal_value"] if current_value else None
        comparisons.append(
            {
                "parameter_code": code,
                "name": (current_value or baseline_value)["parameter_name"],
                "baseline_hex_value": baseline_value["hex_value"] if baseline_value else None,
                "baseline_decimal_value": baseline_decimal,
                "current_hex_value": current_value["hex_value"] if current_value else None,
                "current_decimal_value": current_decimal,
                "decimal_delta": current_decimal - baseline_decimal if baseline_decimal is not None and current_decimal is not None else None,
                "changed": _parameter_changed(baseline_value, current_value),
                "warning": current_warning_by_code.get(code),
            }
        )
    return comparisons


def _warnings_by_code(warnings: list[dict]) -> dict[str, str]:
    warnings_by_code = {}
    for warning in warnings:
        warnings_by_code[warning["parameter_code"]] = warning["message"]
        warnings_by_code[warning["paired_parameter_code"]] = warning["message"]
    return warnings_by_code


def _parameter_changed(baseline_value: dict | None, current_value: dict | None) -> bool:
    if baseline_value is None or current_value is None:
        return baseline_value != current_value
    return baseline_value["hex_value"] != current_value["hex_value"] or baseline_value["decimal_value"] != current_value["decimal_value"]


def _overall_trend(global_metrics: list[dict], floor_comparisons: list[dict]) -> str:
    trends = [item["trend"] for item in global_metrics + floor_comparisons]
    improved = trends.count("improved") + trends.count("newly_measured")
    worsened = trends.count("worsened") + trends.count("missing_current")
    comparable = improved + worsened + trends.count("unchanged")
    if comparable == 0:
        return "not_comparable"
    if improved and worsened:
        return "mixed"
    if improved:
        return "improved"
    if worsened:
        return "worsened"
    return "unchanged"


def _summary_text(overall_trend: str, global_metrics: list[dict], floor_comparisons: list[dict]) -> str:
    critical_current = len([floor for floor in floor_comparisons if floor["current_status"] == "critical"])
    improved_metrics = [metric["label"] for metric in global_metrics if metric["trend"] == "improved"]
    worsened_metrics = [metric["label"] for metric in global_metrics if metric["trend"] == "worsened"]
    if overall_trend == "not_comparable":
        return "No hay datos suficientes para comparar estas pruebas."
    if overall_trend == "improved":
        text = "La prueba actual muestra mejora general"
    elif overall_trend == "worsened":
        text = "La prueba actual muestra deterioro general"
    elif overall_trend == "mixed":
        text = "La prueba actual muestra resultados mixtos"
    else:
        text = "La prueba actual se mantiene similar a la referencia"

    details = []
    if improved_metrics:
        details.append(f"mejora en {', '.join(improved_metrics[:2])}")
    if worsened_metrics:
        details.append(f"deterioro en {', '.join(worsened_metrics[:2])}")
    if critical_current:
        details.append(f"{critical_current} piso(s) crítico(s) pendientes")
    return f"{text}: {'; '.join(details)}." if details else f"{text}."
