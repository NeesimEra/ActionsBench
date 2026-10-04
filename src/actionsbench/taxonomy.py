"""Weakness taxonomy.

The ten classes come from the 2026 study of GitHub Actions security scanners
(arXiv 2601.14455) as summarized in docs/PRD.md. They must be checked against the
paper before the taxonomy is treated as final (PRD, open question 7).

The same values appear in both JSON schemas; tests/test_taxonomy_schema.py fails if
they drift apart.
"""

from __future__ import annotations

from enum import StrEnum


class WeaknessClass(StrEnum):
    ARTIFACT_INTEGRITY = "artifact-integrity"
    CONTROL_FLOW = "control-flow"
    EXCESSIVE_PERMISSION = "excessive-permission"
    RUNNER_COMPATIBILITY = "runner-compatibility"
    HARDENING_GAP = "hardening-gap"
    INJECTION = "injection"
    KNOWN_VULNERABLE_COMPONENT = "known-vulnerable-component"
    PRIVILEGED_TRIGGER = "privileged-trigger"
    SECRETS_EXPOSURE = "secrets-exposure"
    UNPINNED_DEPENDENCY = "unpinned-dependency"


# Three-letter code used in case IDs (AB-<CODE>-NNNN). NEG marks negative cases.
CLASS_CODES: dict[WeaknessClass, str] = {
    WeaknessClass.ARTIFACT_INTEGRITY: "ART",
    WeaknessClass.CONTROL_FLOW: "CTL",
    WeaknessClass.EXCESSIVE_PERMISSION: "PRM",
    WeaknessClass.RUNNER_COMPATIBILITY: "RUN",
    WeaknessClass.HARDENING_GAP: "HRD",
    WeaknessClass.INJECTION: "INJ",
    WeaknessClass.KNOWN_VULNERABLE_COMPONENT: "KVC",
    WeaknessClass.PRIVILEGED_TRIGGER: "TRG",
    WeaknessClass.SECRETS_EXPOSURE: "SEC",
    WeaknessClass.UNPINNED_DEPENDENCY: "PIN",
}

NEGATIVE_CODE = "NEG"
