"""Tests for pipewatch.dependency."""
import pytest
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.dependency import (
    DependencyNode,
    build_graph,
    check_dependencies,
    check_all,
)


def _m(name: str, status: MetricStatus = MetricStatus.OK) -> Metric:
    return Metric(name=name, value=1.0, status=status)


def test_build_graph():
    nodes = [DependencyNode("b", ["a"]), DependencyNode("c", ["a", "b"])]
    graph = build_graph(nodes)
    assert graph["b"] == ["a"]
    assert graph["c"] == ["a", "b"]


def test_no_deps_not_blocked():
    m = _m("standalone")
    graph = {}
    result = check_dependencies(m, graph, {"standalone": m})
    assert not result.blocked
    assert result.blocking_metrics == []


def test_upstream_ok_not_blocked():
    upstream = _m("upstream", MetricStatus.OK)
    downstream = _m("downstream")
    graph = {"downstream": ["upstream"]}
    metric_map = {"upstream": upstream, "downstream": downstream}
    result = check_dependencies(downstream, graph, metric_map)
    assert not result.blocked


def test_upstream_warning_blocks():
    upstream = _m("upstream", MetricStatus.WARNING)
    downstream = _m("downstream")
    graph = {"downstream": ["upstream"]}
    metric_map = {"upstream": upstream, "downstream": downstream}
    result = check_dependencies(downstream, graph, metric_map)
    assert result.blocked
    assert "upstream" in result.blocking_metrics
    assert result.reason is not None


def test_upstream_critical_blocks():
    upstream = _m("ingest", MetricStatus.CRITICAL)
    downstream = _m("transform")
    graph = {"transform": ["ingest"]}
    metric_map = {"ingest": upstream, "transform": downstream}
    result = check_dependencies(downstream, graph, metric_map)
    assert result.blocked


def test_check_all_mixed():
    a = _m("a", MetricStatus.CRITICAL)
    b = _m("b", MetricStatus.OK)
    c = _m("c", MetricStatus.OK)
    nodes = [DependencyNode("b", ["a"]), DependencyNode("c", [])]
    results = check_all([a, b, c], nodes)
    result_map = {r.metric_name: r for r in results}
    assert result_map["b"].blocked
    assert not result_map["c"].blocked
    assert not result_map["a"].blocked


def test_node_roundtrip():
    node = DependencyNode("x", ["y", "z"])
    assert DependencyNode.from_dict(node.to_dict()) == node
