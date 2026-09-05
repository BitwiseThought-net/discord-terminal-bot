#!/usr/bin/env python3
"""
Merges the Python bot's test/coverage results with the Node.js editor API's
test/coverage results into a single combined coverage.xml and junit.xml,
then shells out to `genbadge` to render badges/coverage-badge.svg and
badges/tests-badge.svg from the real, current numbers.

Scope note: this intentionally covers only lib/ (Python bot) and
editor/web-server.js (Node API) — the two components the README explicitly
claims 100% coverage for. The React dashboard (editor/dashboard) is a
separate, not-yet-fully-tested component and is excluded so the badges don't
silently misrepresent it as covered.

Inputs (must exist before running this script):
  - coverage.xml                        (from: pytest --cov=lib --cov-report=xml)
  - pytest-results.xml                  (from: pytest --junitxml=pytest-results.xml)
  - editor/coverage/cobertura-coverage.xml  (from: jest --coverage, coverageReporters=cobertura)
  - editor/junit.xml                    (from: jest-junit reporter)

Outputs:
  - badges/combined-coverage.xml (intermediate, genbadge input)
  - badges/combined-junit.xml    (intermediate, genbadge input)
  - badges/coverage-badge.svg
  - badges/tests-badge.svg
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BADGES_DIR = ROOT / "badges"

PYTHON_COVERAGE = ROOT / "coverage.xml"
PYTHON_JUNIT = ROOT / "pytest-results.xml"
EDITOR_COVERAGE = ROOT / "editor" / "coverage" / "cobertura-coverage.xml"
EDITOR_JUNIT = ROOT / "editor" / "junit.xml"


def require(path: Path) -> Path:
    if not path.exists():
        sys.exit(
            f"ERROR: expected input file not found: {path}\n"
            "Make sure the test suites ran (with coverage + junit/cobertura "
            "reporters enabled) before calling this script."
        )
    return path


def merge_coverage(python_xml: Path, editor_xml: Path, out_path: Path) -> None:
    """Sum lines/branches covered+valid across both cobertura reports and
    write a single synthetic <coverage> root with matching rates."""
    py_root = ET.parse(python_xml).getroot()
    ed_root = ET.parse(editor_xml).getroot()

    def attr_int(root, name):
        return int(root.attrib.get(name, "0"))

    lines_covered = attr_int(py_root, "lines-covered") + attr_int(ed_root, "lines-covered")
    lines_valid = attr_int(py_root, "lines-valid") + attr_int(ed_root, "lines-valid")
    branches_covered = attr_int(py_root, "branches-covered") + attr_int(ed_root, "branches-covered")
    branches_valid = attr_int(py_root, "branches-valid") + attr_int(ed_root, "branches-valid")

    line_rate = (lines_covered / lines_valid) if lines_valid > 0 else 0.0
    branch_rate = (branches_covered / branches_valid) if branches_valid > 0 else 0.0

    combined = ET.Element("coverage", {
        "line-rate": f"{line_rate:.4f}",
        "branch-rate": f"{branch_rate:.4f}",
        "lines-covered": str(lines_covered),
        "lines-valid": str(lines_valid),
        "branches-covered": str(branches_covered),
        "branches-valid": str(branches_valid),
        "complexity": "0",
        "version": "combined-lib+editor",
    })
    ET.ElementTree(combined).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Combined coverage: {lines_covered}/{lines_valid} lines, "
          f"{branches_covered}/{branches_valid} branches -> {out_path}")


def merge_junit(python_xml: Path, editor_xml: Path, out_path: Path) -> None:
    """Concatenate every <testsuite> from both reports under one <testsuites> root."""
    combined = ET.Element("testsuites", {"name": "combined bot+editor tests"})

    for src in (python_xml, editor_xml):
        root = ET.parse(src).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        for suite in suites:
            combined.append(suite)

    ET.ElementTree(combined).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Combined junit results -> {out_path}")


def run_genbadge(kind: str, input_file: Path, output_file: Path) -> None:
    subprocess.run(
        ["genbadge", kind, "-i", str(input_file), "-o", str(output_file), "--local"],
        check=True,
    )
    print(f"Wrote {output_file}")


def main() -> None:
    require(PYTHON_COVERAGE)
    require(PYTHON_JUNIT)
    require(EDITOR_COVERAGE)
    require(EDITOR_JUNIT)

    BADGES_DIR.mkdir(exist_ok=True)

    combined_coverage_xml = BADGES_DIR / "combined-coverage.xml"
    combined_junit_xml = BADGES_DIR / "combined-junit.xml"

    merge_coverage(PYTHON_COVERAGE, EDITOR_COVERAGE, combined_coverage_xml)
    merge_junit(PYTHON_JUNIT, EDITOR_JUNIT, combined_junit_xml)

    run_genbadge("coverage", combined_coverage_xml, BADGES_DIR / "coverage-badge.svg")
    run_genbadge("tests", combined_junit_xml, BADGES_DIR / "tests-badge.svg")


if __name__ == "__main__":
    main()
