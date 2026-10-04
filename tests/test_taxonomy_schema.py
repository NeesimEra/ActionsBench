"""Guard against the taxonomy drifting between the code and the two JSON schemas."""

from __future__ import annotations

import re

from actionsbench.corpus import load_schema
from actionsbench.taxonomy import CLASS_CODES, NEGATIVE_CODE, WeaknessClass

ALL_CLASSES = {c.value for c in WeaknessClass}


def test_every_class_has_a_unique_code() -> None:
    assert set(CLASS_CODES) == set(WeaknessClass)
    codes = list(CLASS_CODES.values())
    assert len(codes) == len(set(codes))
    assert NEGATIVE_CODE not in codes


def test_case_schema_class_enum_matches_taxonomy() -> None:
    schema = load_schema("case.schema.json")
    enum = schema["properties"]["expected"]["items"]["properties"]["weakness_class"]["enum"]
    assert set(enum) == ALL_CLASSES


def test_findings_schema_class_enums_match_taxonomy() -> None:
    schema = load_schema("findings.schema.json")
    scope = schema["properties"]["scope"]["items"]["enum"]
    finding = schema["properties"]["findings"]["items"]["properties"]["weakness_class"]["enum"]
    assert set(scope) == ALL_CLASSES
    assert set(finding) == ALL_CLASSES


def test_case_id_pattern_accepts_exactly_the_known_codes() -> None:
    schema = load_schema("case.schema.json")
    pattern = re.compile(schema["properties"]["id"]["pattern"])
    for code in [*CLASS_CODES.values(), NEGATIVE_CODE]:
        assert pattern.match(f"AB-{code}-0001")
    assert not pattern.match("AB-XXX-0001")
    assert not pattern.match("AB-INJ-1")
