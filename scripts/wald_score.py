#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Optional

LINT_TARGETS = ["src", "tests", "tools"]
WALD_STATE_FILE = ".council/wald_state.json"


def resolve_ruff() -> Optional[str]:
    venv_ruff = os.path.join(os.getcwd(), ".venv", "bin", "ruff")
    if os.path.isfile(venv_ruff) and os.access(venv_ruff, os.X_OK):
        return venv_ruff
    if command_exists("ruff"):
        return "ruff"
    return None


def get_coverage() -> Optional[float]:
    coverage_xml = "coverage.xml"
    if os.path.exists(coverage_xml):
        return parse_coverage_xml(coverage_xml)

    if os.path.exists(".coverage"):
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "xml", "-i"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and os.path.exists(coverage_xml):
            return parse_coverage_xml(coverage_xml)

    return None


def parse_coverage_xml(path: str) -> Optional[float]:
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return None

    line_rate = root.attrib.get("line-rate")
    if line_rate is not None:
        try:
            return max(0.0, min(1.0, float(line_rate)))
        except ValueError:
            return None

    lines_valid = root.attrib.get("lines-valid")
    lines_covered = root.attrib.get("lines-covered")
    if lines_valid and lines_covered:
        try:
            valid = float(lines_valid)
            covered = float(lines_covered)
            return max(0.0, min(1.0, covered / valid if valid else 0.0))
        except ValueError:
            return None

    return None


def get_lint_errors() -> Optional[int]:
    ruff_cmd = resolve_ruff()
    if not ruff_cmd:
        return None

    result = subprocess.run(
        [ruff_cmd, "check", *LINT_TARGETS],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return 0

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return len(lines)


def check_spec_compliance() -> float:
    # Placeholder for semantic check
    if os.path.exists("SPEC.md") or os.path.exists(os.path.join(".council", "SPEC.md")):
        return 1.0
    return 0.5


def command_exists(cmd: str) -> bool:
    return (
        subprocess.run(
            ["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"],
            capture_output=True,
        ).returncode
        == 0
    )


def calculate_wald_score(
    coverage: Optional[float],
    lint_errors: Optional[int],
    spec_compliance: float,
) -> float:
    weights = {
        "coverage": 0.4,
        "lint": 0.4,
        "spec": 0.2,
    }

    metrics = {}
    if coverage is not None:
        metrics["coverage"] = coverage
    else:
        weights["coverage"] = 0.0

    if lint_errors is not None:
        lint_score = max(0.0, 1.0 - (lint_errors / 10.0))
        metrics["lint"] = lint_score
    else:
        weights["lint"] = 0.0

    metrics["spec"] = spec_compliance

    total_weight = sum(weights.values())
    if total_weight <= 0:
        return 0.0

    pi = 0.0
    for key, weight in weights.items():
        if weight <= 0:
            continue
        pi += metrics.get(key, 0.0) * weight

    pi = pi / total_weight
    return min(1.0, max(0.0, pi))


def main():
    parser = argparse.ArgumentParser(description="Wald Score Calculator")
    parser.add_argument("--coverage", type=float, help="Override coverage (0.0-1.0)")
    parser.add_argument("--lint", type=int, help="Override lint error count")
    parser.add_argument(
        "--risk",
        choices=["low", "medium", "high"],
        default="medium",
        help="Risk level for this operation",
    )
    parser.add_argument(
        "--update",
        choices=["success", "failure"],
        help="Update pi state (success: +0.15, failure: -0.1)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset pi state to initial value (0.5)",
    )

    args = parser.parse_args()

    # Handle --reset
    if args.reset:
        state = {"pi": 0.5, "successes": 0, "failures": 0}
        os.makedirs(os.path.dirname(WALD_STATE_FILE), exist_ok=True)
        with open(WALD_STATE_FILE, "w") as f:
            json.dump(state, f)
        print("🔄 Wald state reset to pi=0.5")
        return

    # Handle --update
    if args.update:
        state = {"pi": 0.5, "successes": 0, "failures": 0}
        if os.path.exists(WALD_STATE_FILE):
            with open(WALD_STATE_FILE) as f:
                state = json.load(f)
        if args.update == "success":
            state["successes"] += 1
            state["pi"] = min(1.0, state["pi"] + 0.15)
        else:
            state["failures"] += 1
            state["pi"] = max(0.0, state["pi"] - 0.1)
        os.makedirs(os.path.dirname(WALD_STATE_FILE), exist_ok=True)
        with open(WALD_STATE_FILE, "w") as f:
            json.dump(state, f)
        print(
            f"📊 Wald π updated: {state['pi']:.4f} (s={state['successes']}, f={state['failures']})"
        )
        return

    coverage = args.coverage if args.coverage is not None else get_coverage()
    lint_errors = args.lint if args.lint is not None else get_lint_errors()
    spec_compliance = check_spec_compliance()

    pi = calculate_wald_score(coverage, lint_errors, spec_compliance)

    # Dynamic Thresholds
    thresholds = {"low": 0.80, "medium": 0.95, "high": 0.99}
    required_pi = thresholds[args.risk]

    print(f"📊 Wald Score Calculation (Risk: {args.risk.upper()}):")
    print(f"  Coverage: {coverage:.2f}" if coverage is not None else "  Coverage: N/A")
    print(
        f"  Lint Errors: {lint_errors}"
        if lint_errors is not None
        else "  Lint Errors: N/A"
    )
    print(f"  Spec Compliance: {spec_compliance:.2f}")
    if coverage is None:
        print("  Warning: coverage.xml not found; skipping coverage metric.")
    if lint_errors is None:
        print("  Warning: ruff not found; skipping lint metric.")
    print("---------------------------")
    print(f"  π (Confidence): {pi:.4f}")
    print(f"  Required π: {required_pi:.2f}")

    if pi >= required_pi:
        if args.risk == "high":
            print("⚠️ Status: HUMAN_APPROVAL_REQUIRED (High Risk Passed)")
            exit(0)  # Technically a pass, but needs HITL
        else:
            print("✅ Status: AUTO_COMMIT")
            exit(0)
    elif pi > 0.30:
        print("⚠️ Status: VERIFY_REQUIRED")
        exit(1)
    else:
        print("❌ Status: REJECT")
        exit(2)


if __name__ == "__main__":
    main()
