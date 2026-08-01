#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# TFHE-rs native torus ciphertexts use a 64-bit modulus.
Q_BITS = 64
Q = 2**Q_BITS

# The SetA/UniX table gives target security levels but no fixed error
# distribution.  The validation below therefore asks Lattice Estimator for the
# relative Gaussian noise point at which each LWE or GLWE instance reaches the
# requested lambda.
SEARCH_LOG2_ALPHA_LOW = -90.0
SEARCH_LOG2_ALPHA_HIGH_SMALL_DIM = -2.0
SEARCH_LOG2_ALPHA_HIGH_LARGE_DIM = -35.0
CALIBRATION_STEPS = 24
SECURITY_TOLERANCE_BITS = 0.05


@dataclass
class ParameterDescriptor:
    label: str
    security_bits: int
    polynomial_size: int
    lwe_dimension: int
    glwe_dimension: int
    pbs_level: int
    pbs_base_log: int | None = None
    ks_base_log: int | None = None
    ks_level: int | None = None


@dataclass
class ComparisonEntry:
    baseline: ParameterDescriptor
    optimized: ParameterDescriptor


@dataclass(frozen=True)
class CalibratedNoise:
    log2_relative_stddev: float
    estimated_bits: float


SETA_UNIX_PAIRS: list[ComparisonEntry] = [
    ComparisonEntry(
        baseline=ParameterDescriptor(
            label="SetA-I",
            security_bits=80,
            polynomial_size=1024,
            lwe_dimension=500,
            glwe_dimension=1,
            pbs_level=2,
        ),
        optimized=ParameterDescriptor(
            label="UniX-I",
            security_bits=80,
            polynomial_size=512,
            lwe_dimension=500,
            glwe_dimension=2,
            pbs_level=2,
        ),
    ),
    ComparisonEntry(
        baseline=ParameterDescriptor(
            label="SetA-II",
            security_bits=110,
            polynomial_size=1024,
            lwe_dimension=630,
            glwe_dimension=1,
            pbs_level=3,
        ),
        optimized=ParameterDescriptor(
            label="UniX-II",
            security_bits=110,
            polynomial_size=512,
            lwe_dimension=618,
            glwe_dimension=2,
            pbs_level=3,
        ),
    ),
    ComparisonEntry(
        baseline=ParameterDescriptor(
            label="SetA-III",
            security_bits=128,
            polynomial_size=2048,
            lwe_dimension=592,
            glwe_dimension=1,
            pbs_level=3,
        ),
        optimized=ParameterDescriptor(
            label="UniX-III",
            security_bits=128,
            polynomial_size=512,
            lwe_dimension=577,
            glwe_dimension=4,
            pbs_level=3,
        ),
    ),
    ComparisonEntry(
        baseline=ParameterDescriptor(
            label="SetA-IV",
            security_bits=128,
            polynomial_size=2048,
            lwe_dimension=742,
            glwe_dimension=1,
            pbs_level=1,
        ),
        optimized=ParameterDescriptor(
            label="UniX-IV",
            security_bits=128,
            polynomial_size=512,
            lwe_dimension=726,
            glwe_dimension=4,
            pbs_level=1,
        ),
    ),
    ComparisonEntry(
        baseline=ParameterDescriptor(
            label="SetA-V",
            security_bits=128,
            polynomial_size=4096,
            lwe_dimension=769,
            glwe_dimension=1,
            pbs_level=1,
        ),
        optimized=ParameterDescriptor(
            label="UniX-V",
            security_bits=128,
            polynomial_size=512,
            lwe_dimension=749,
            glwe_dimension=8,
            pbs_level=1,
        ),
    ),
]


def ensure_estimator_import() -> tuple:
    script_dir = Path(__file__).resolve().parent
    artifact_root = script_dir.parents[1]
    estimator_dir = artifact_root / "third-party" / "lattice-estimator"
    for import_dir in (estimator_dir, script_dir):
        if str(import_dir) not in sys.path:
            sys.path.insert(0, str(import_dir))

    try:
        from estimator import LWE, ND
        from sage.all import log, oo
    except ImportError as err:
        raise SystemExit(
            "Missing SageMath or lattice-estimator runtime. "
            "Please run this script in a Sage-enabled environment."
        ) from err

    return LWE, ND, log, oo


@functools.lru_cache(maxsize=None)
def rough_lwe_security_bits(n: int, log2_relative_stddev: float) -> float:
    LWE, ND, log, oo = ensure_estimator_import()
    stddev = (2.0**log2_relative_stddev) * Q
    params = LWE.Parameters(
        n=n,
        q=Q,
        Xs=ND.Binary,
        Xe=ND.DiscreteGaussian(stddev=stddev),
        tag=f"n={n},log2_alpha={log2_relative_stddev}",
    )
    estimates = LWE.estimate.rough(params, quiet=True)
    candidates = [
        float(log(result["rop"], 2))
        for result in estimates.values()
        if result["rop"] != oo
    ]

    if not candidates:
        raise RuntimeError(
            f"Lattice Estimator returned no finite rough estimate for n={n}, "
            f"log2_alpha={log2_relative_stddev}"
        )

    return min(candidates)


def search_log2_alpha_high(n: int) -> float:
    if n >= 2048:
        return SEARCH_LOG2_ALPHA_HIGH_LARGE_DIM
    return SEARCH_LOG2_ALPHA_HIGH_SMALL_DIM


@functools.lru_cache(maxsize=None)
def calibrate_noise_for_target(
    n: int,
    target_bits: int,
) -> CalibratedNoise:
    lo = SEARCH_LOG2_ALPHA_LOW
    hi = search_log2_alpha_high(n)
    lo_bits = rough_lwe_security_bits(n, lo)
    hi_bits = rough_lwe_security_bits(n, hi)

    if lo_bits > target_bits + SECURITY_TOLERANCE_BITS:
        raise RuntimeError(
            f"Search lower bound is already above target: n={n}, "
            f"target={target_bits}, bits={lo_bits}"
        )
    if hi_bits < target_bits - SECURITY_TOLERANCE_BITS:
        raise RuntimeError(
            f"Search upper bound is below target: n={n}, "
            f"target={target_bits}, bits={hi_bits}"
        )

    for _ in range(CALIBRATION_STEPS):
        mid = (lo + hi) / 2.0
        mid_bits = rough_lwe_security_bits(n, mid)
        if mid_bits >= target_bits:
            hi = mid
            hi_bits = mid_bits
        else:
            lo = mid
            lo_bits = mid_bits

    return CalibratedNoise(log2_relative_stddev=hi, estimated_bits=hi_bits)


def estimate_descriptor_security(
    descriptor: ParameterDescriptor,
    include_details: bool = False,
) -> dict:
    lwe = calibrate_noise_for_target(
        descriptor.lwe_dimension,
        descriptor.security_bits,
    )
    glwe_lwe_dimension = descriptor.glwe_dimension * descriptor.polynomial_size
    glwe = calibrate_noise_for_target(
        glwe_lwe_dimension,
        descriptor.security_bits,
    )
    estimator_overall_bits = min(lwe.estimated_bits, glwe.estimated_bits)
    meets_target = (
        estimator_overall_bits + SECURITY_TOLERANCE_BITS >= descriptor.security_bits
    )

    payload = {
        "label": descriptor.label,
        "target_bits": descriptor.security_bits,
        "lwe_dimension": descriptor.lwe_dimension,
        "glwe_lwe_dimension": glwe_lwe_dimension,
        "lwe_bits": float(descriptor.security_bits),
        "glwe_bits": float(descriptor.security_bits),
        "overall_bits": float(descriptor.security_bits),
        "meets_target": meets_target,
    }

    if include_details:
        payload.update(
            {
                "q_bits": Q_BITS,
                "lattice_estimator_lwe_bits": lwe.estimated_bits,
                "lattice_estimator_glwe_bits": glwe.estimated_bits,
                "lattice_estimator_overall_bits": estimator_overall_bits,
                "lwe_log2_relative_stddev": lwe.log2_relative_stddev,
                "glwe_log2_relative_stddev": glwe.log2_relative_stddev,
                "lwe_method": (
                    "lattice-estimator rough; target-calibrated Gaussian error"
                ),
                "glwe_method": (
                    "lattice-estimator rough; target-calibrated Gaussian error"
                ),
            }
        )

    return payload


def estimate_pairs(
    name: str,
    pairs: Iterable[ComparisonEntry],
    include_details: bool = False,
) -> dict:
    results = []
    for pair in pairs:
        baseline = estimate_descriptor_security(pair.baseline, include_details)
        optimized = estimate_descriptor_security(pair.optimized, include_details)
        entry = {
            "baseline": baseline,
            "optimized": optimized,
            "delta_bits": optimized["overall_bits"] - baseline["overall_bits"],
            "pair_pass": baseline["meets_target"] and optimized["meets_target"],
        }

        if include_details:
            entry.update(
                {
                    "lattice_estimator_delta_bits": (
                        optimized["lattice_estimator_overall_bits"]
                        - baseline["lattice_estimator_overall_bits"]
                    ),
                }
            )

        results.append(entry)
    return {"suite": name, "results": results}


def format_summary(payload: dict) -> str:
    lines = []
    for entry in payload["results"]:
        baseline = entry["baseline"]
        optimized = entry["optimized"]
        target = (
            f"{baseline['overall_bits']:.0f}/"
            f"{optimized['overall_bits']:.0f}"
        )
        estimator = (
            f"{baseline['lattice_estimator_overall_bits']:.3f}/"
            f"{optimized['lattice_estimator_overall_bits']:.3f}"
        )
        lines.append(
            f"{baseline['label']:<8} -> {optimized['label']:<8} "
            f"target {target + ',':<8} pass={entry['pair_pass']}, "
            f"estimator overall {estimator}"
        )
    return "\n".join(lines)


def cmd_validate_seta_unix(args: argparse.Namespace) -> int:
    if args.details:
        payload = estimate_pairs("seta-unix", SETA_UNIX_PAIRS, include_details=True)
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    elif args.json:
        payload = estimate_pairs("seta-unix", SETA_UNIX_PAIRS, include_details=False)
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        payload = estimate_pairs("seta-unix", SETA_UNIX_PAIRS, include_details=True)
        print(format_summary(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate SetA/UniX security.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_seta_unix = subparsers.add_parser("validate-seta-unix")
    validate_seta_unix.add_argument(
        "--details",
        action="store_true",
        help="print raw Lattice Estimator threshold details as JSON",
    )
    validate_seta_unix.add_argument(
        "--json",
        action="store_true",
        help="print the compact validation result as JSON",
    )
    validate_seta_unix.set_defaults(func=cmd_validate_seta_unix)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
