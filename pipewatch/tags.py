"""Tag-based filtering for metrics."""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TagFilter:
    required: List[str] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)

    def matches(self, tags: List[str]) -> bool:
        """Return True if tags satisfy required/excluded constraints."""
        for r in self.required:
            if r not in tags:
                return False
        for e in self.excluded:
            if e in tags:
                return False
        return True


def filter_metrics(metrics, tag_filter: TagFilter):
    """Filter a list of Metric objects by a TagFilter.

    Metrics without a 'tags' attribute are treated as having no tags.
    """
    result = []
    for m in metrics:
        tags = getattr(m, "tags", []) or []
        if tag_filter.matches(tags):
            result.append(m)
    return result


def group_by_tag(metrics) -> Dict[str, list]:
    """Return a dict mapping each tag to the metrics that carry it."""
    groups: Dict[str, list] = {}
    for m in metrics:
        tags = getattr(m, "tags", []) or []
        for tag in tags:
            groups.setdefault(tag, []).append(m)
    return groups
