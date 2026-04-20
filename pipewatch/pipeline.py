"""Pipeline health aggregation module.

Provides a high-level view of an entire pipeline's health by combining
metric statuses, dependency checks, anomaly results, and trend data
into a single PipelineHealth report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from pipewatch.metrics import Metric, MetricStatus
from pipewatch.aggregator import aggregate_metrics, AggregatedMetric
from pipewatch.dependency import DependencyNode, check_dependencies, DependencyCheckResult
from pipewatch.trend import compute_trend, TrendDirection
from pipewatch.anomaly import detect_anomaly, AnomalyResult
from pipewatch.history import load_history


@dataclass
class PipelineStageHealth:
    """Health summary for a single named pipeline stage."""

    stage: str
    metrics: List[AggregatedMetric]
    worst_status: MetricStatus
    anomalies: List[AnomalyResult] = field(default_factory=list)
    trend: TrendDirection = TrendDirection.STABLE
    blocked_by: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "worst_status": self.worst_status.value,
            "trend": self.trend.value,
            "blocked_by": self.blocked_by,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "metrics": [m.to_dict() for m in self.metrics],
        }


@dataclass
class PipelineHealth:
    """Overall health report for a multi-stage pipeline."""

    pipeline_name: str
    stages: List[PipelineStageHealth]
    overall_status: MetricStatus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline": self.pipeline_name,
            "overall_status": self.overall_status.value,
            "stages": [s.to_dict() for s in self.stages],
        }

    def summary_lines(self) -> List[str]:
        """Return a human-readable summary of pipeline health."""
        lines = [
            f"Pipeline : {self.pipeline_name}",
            f"Overall  : {self.overall_status.value.upper()}",
            "-" * 40,
        ]
        for stage in self.stages:
            blocked = f" [blocked by: {', '.join(stage.blocked_by)}]" if stage.blocked_by else ""
            anomaly_flag = " [ANOMALY]" if stage.anomalies else ""
            lines.append(
                f"  {stage.stage:<20} {stage.worst_status.value:<10}"
                f" trend={stage.trend.value}{blocked}{anomaly_flag}"
            )
        return lines


def _resolve_worst(statuses: List[MetricStatus]) -> MetricStatus:
    """Return the most severe MetricStatus from a list."""
    priority = {
        MetricStatus.CRITICAL: 2,
        MetricStatus.WARNING: 1,
        MetricStatus.OK: 0,
    }
    if not statuses:
        return MetricStatus.OK
    return max(statuses, key=lambda s: priority.get(s, 0))


def build_pipeline_health(
    pipeline_name: str,
    stage_metrics: Dict[str, List[Metric]],
    dependency_graph: Optional[List[DependencyNode]] = None,
    history_path: Optional[str] = None,
) -> PipelineHealth:
    """Build a PipelineHealth report from per-stage metrics.

    Args:
        pipeline_name: Human-readable name for the pipeline.
        stage_metrics: Mapping of stage name -> list of Metric objects.
        dependency_graph: Optional list of DependencyNode definitions.
        history_path: Optional path to history file for trend/anomaly analysis.

    Returns:
        A PipelineHealth instance summarising all stages.
    """
    history = load_history(history_path) if history_path else []
    dep_results: Dict[str, DependencyCheckResult] = {}
    if dependency_graph:
        all_metrics = [m for ms in stage_metrics.values() for m in ms]
        for node in dependency_graph:
            dep_results[node.name] = check_dependencies(node, all_metrics)

    stage_healths: List[PipelineStageHealth] = []

    for stage_name, metrics in stage_metrics.items():
        aggregated = aggregate_metrics(metrics)
        worst = _resolve_worst([a.worst_status for a in aggregated])

        # Trend: use the first metric's history as a proxy for the stage
        stage_trend = TrendDirection.STABLE
        if metrics and history:
            trend_result = compute_trend(
                [e for e in history if e.metric_name == metrics[0].name]
            )
            stage_trend = trend_result.direction

        # Anomaly detection across all stage metrics
        anomalies: List[AnomalyResult] = []
        for m in metrics:
            result = detect_anomaly(
                m.name,
                m.value,
                [e for e in history if e.metric_name == m.name],
            )
            if result and result.is_anomaly:
                anomalies.append(result)

        # Dependency blocking
        blocked_by: List[str] = []
        if stage_name in dep_results and dep_results[stage_name].is_blocked:
            blocked_by = dep_results[stage_name].blocking_metrics

        stage_healths.append(
            PipelineStageHealth(
                stage=stage_name,
                metrics=aggregated,
                worst_status=worst,
                anomalies=anomalies,
                trend=stage_trend,
                blocked_by=blocked_by,
            )
        )

    overall = _resolve_worst([s.worst_status for s in stage_healths])
    return PipelineHealth(
        pipeline_name=pipeline_name,
        stages=stage_healths,
        overall_status=overall,
    )
