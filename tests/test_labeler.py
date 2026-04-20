"""Tests for pipewatch.labeler."""

import pytest
from pipewatch.labeler import LabelSet, label_metrics, group_by_label, label_summary
from pipewatch.metrics import Metric, ThresholdConfig


def _make_metric(name: str, labels: dict) -> Metric:
    cfg = ThresholdConfig(warning=50.0, critical=100.0)
    m = Metric(name=name, value=10.0, config=cfg)
    m.labels = LabelSet(labels)
    return m


# --- LabelSet unit tests ---

def test_labelset_get_existing():
    ls = LabelSet({"env": "prod"})
    assert ls.get("env") == "prod"


def test_labelset_get_missing():
    ls = LabelSet({})
    assert ls.get("env") is None


def test_labelset_set():
    ls = LabelSet({})
    ls.set("region", "us-east")
    assert ls.get("region") == "us-east"


def test_labelset_matches_all():
    ls = LabelSet({"env": "prod", "team": "alpha"})
    assert ls.matches({"env": "prod", "team": "alpha"}) is True


def test_labelset_matches_partial():
    ls = LabelSet({"env": "prod", "team": "alpha"})
    assert ls.matches({"env": "prod"}) is True


def test_labelset_no_match():
    ls = LabelSet({"env": "staging"})
    assert ls.matches({"env": "prod"}) is False


def test_labelset_to_dict_roundtrip():
    data = {"env": "prod", "layer": "db"}
    ls = LabelSet.from_dict(data)
    assert ls.to_dict() == data


# --- label_metrics tests ---

def test_label_metrics_filters_correctly():
    m1 = _make_metric("a", {"env": "prod"})
    m2 = _make_metric("b", {"env": "staging"})
    result = label_metrics([m1, m2], {"env": "prod"})
    assert len(result) == 1
    assert result[0].name == "a"


def test_label_metrics_empty_selector_returns_all():
    m1 = _make_metric("a", {"env": "prod"})
    m2 = _make_metric("b", {"env": "staging"})
    result = label_metrics([m1, m2], {})
    assert len(result) == 2


def test_label_metrics_skips_unlabeled():
    cfg = ThresholdConfig(warning=50.0, critical=100.0)
    m = Metric(name="bare", value=1.0, config=cfg)  # no .labels attribute
    result = label_metrics([m], {"env": "prod"})
    assert result == []


# --- group_by_label tests ---

def test_group_by_label_basic():
    m1 = _make_metric("a", {"team": "alpha"})
    m2 = _make_metric("b", {"team": "beta"})
    m3 = _make_metric("c", {"team": "alpha"})
    groups = group_by_label([m1, m2, m3], "team")
    assert len(groups["alpha"]) == 2
    assert len(groups["beta"]) == 1


def test_group_by_label_missing_key_goes_to_empty_string():
    m = _make_metric("x", {})
    groups = group_by_label([m], "team")
    assert "" in groups
    assert groups[""][0].name == "x"


# --- label_summary tests ---

def test_label_summary_contains_key():
    m1 = _make_metric("a", {"layer": "db"})
    m2 = _make_metric("b", {"layer": "api"})
    lines = label_summary([m1, m2], "layer")
    combined = "\n".join(lines)
    assert "layer" in combined
    assert "db" in combined
    assert "api" in combined
