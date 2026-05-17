"""Tiny JUnit XML parser.

We deliberately don't pull a full XML library; a few `xml.etree` lines are
enough to extract pass / fail counts for the dashboard.
"""

from __future__ import annotations

import logging
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


def parse_junit(xml: str) -> tuple[int, int, int]:
    """Return `(tests_collected, tests_passed, tests_failed)`."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        logger.warning("Bad JUnit XML: %s", e)
        return (0, 0, 0)

    suites = [root] if root.tag.endswith("testsuite") else list(root.iter("testsuite"))
    total = failures = errors = skipped = 0
    for suite in suites:
        total += int(suite.attrib.get("tests", 0) or 0)
        failures += int(suite.attrib.get("failures", 0) or 0)
        errors += int(suite.attrib.get("errors", 0) or 0)
        skipped += int(suite.attrib.get("skipped", 0) or 0)
    passed = max(total - failures - errors - skipped, 0)
    return total, passed, failures + errors
