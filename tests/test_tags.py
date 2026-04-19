"""Tests for pipewatch.tags module."""
import pytest
from pipewatch.tags import TagFilter, filter_metrics, group_by_tag


class _M:
    def __init__(self, name, tags=None):
        self.name = name
        self.tags = tags or []


def test_tag_filter_matches_required():
    tf = TagFilter(required=["prod"])
    assert tf.matches(["prod", "db"]) is True
    assert tf.matches(["staging"]) is False


def test_tag_filter_matches_excluded():
    tf = TagFilter(excluded=["debug"])
    assert tf.matches(["prod"]) is True
    assert tf.matches(["prod", "debug"]) is False


def test_tag_filter_combined():
    tf = TagFilter(required=["prod"], excluded=["deprecated"])
    assert tf.matches(["prod"]) is True
    assert tf.matches(["prod", "deprecated"]) is False
    assert tf.matches(["staging"]) is False


def test_tag_filter_empty_always_matches():
    tf = TagFilter()
    assert tf.matches([]) is True
    assert tf.matches(["anything"]) is True


def test_filter_metrics_returns_matching():
    metrics = [_M("a", ["prod"]), _M("b", ["staging"]), _M("c", ["prod", "db"])]
    tf = TagFilter(required=["prod"])
    result = filter_metrics(metrics, tf)
    assert len(result) == 2
    assert all("prod" in m.tags for m in result)


def test_filter_metrics_no_tags_attr():
    class Bare:
        name = "bare"
    tf = TagFilter(required=["prod"])
    result = filter_metrics([Bare()], tf)
    assert result == []


def test_group_by_tag_basic():
    metrics = [_M("a", ["prod", "db"]), _M("b", ["prod"]), _M("c", ["staging"])]
    groups = group_by_tag(metrics)
    assert "prod" in groups
    assert len(groups["prod"]) == 2
    assert len(groups["staging"]) == 1
    assert len(groups["db"]) == 1


def test_group_by_tag_empty():
    assert group_by_tag([]) == {}


def test_group_by_tag_no_tags():
    groups = group_by_tag([_M("x", [])])
    assert groups == {}
