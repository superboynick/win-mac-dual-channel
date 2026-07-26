"""Small validation CLI."""

from __future__ import annotations

import argparse
import json
import sys

from .validator import ContractValidationError, validate_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an AirJet coupling handoff")
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("document")
    args = parser.parse_args(argv)
    try:
        validate_file(args.document)
    except ContractValidationError as exc:
        errors = list(exc.errors)
        print(json.dumps({"accepted": False, "errors": errors}, indent=2), file=sys.stderr)
        return 2
    except OSError:
        errors = ["$: document could not be read"]
        print(json.dumps({"accepted": False, "errors": errors}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({
        "metadata_contract_accepted": True,
        "artifact_contents_verified": False,
        "scope": "REFERENCE_METADATA_CONTRACT_ONLY",
        "solver_authorized": False,
        "stage_gate_advanced": False,
        "consumer_action_required": "Open each relative artifact through a trusted snapshot boundary and revalidate size and SHA-256 before use.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
