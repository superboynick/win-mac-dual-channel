#!/usr/bin/env bash
set -euo pipefail

# Deterministic tooling-only smoke for a configured OpenFOAM Foundation v14
# shell. This is not an AirJet case and cannot satisfy any P3-P6 gate.

required_commands=(foamVersion blockMesh checkMesh foamRun)
for command_name in "${required_commands[@]}"; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "TOOLING_NOT_INSTALLED missing=$command_name" >&2
        exit 20
    fi
done

if ! foam_version="$(foamVersion 2>&1)"; then
    echo "TOOLING_VERSION_MISMATCH reason=foamVersion_command_failed expected=OpenFOAM-14" >&2
    exit 21
fi
if [[ "$foam_version" != "OpenFOAM-14" ]]; then
    echo "TOOLING_VERSION_MISMATCH observed=$foam_version expected=OpenFOAM-14" >&2
    exit 21
fi

if [[ -z "${FOAM_TUTORIALS:-}" || ! -d "$FOAM_TUTORIALS" ]]; then
    echo "TOOLING_ENVIRONMENT_INVALID FOAM_TUTORIALS=${FOAM_TUTORIALS:-UNSET}" >&2
    exit 22
fi

tutorial_candidates=()
while IFS= read -r tutorial_candidate; do
    tutorial_candidates+=("$tutorial_candidate")
done < <(
    find "$FOAM_TUTORIALS" -type d -name pitzDailySteady -print | LC_ALL=C sort
)
if [[ "${#tutorial_candidates[@]}" -ne 1 ]]; then
    echo "TOOLING_TUTORIAL_IDENTITY_FAIL count=${#tutorial_candidates[@]} expected=1" >&2
    exit 23
fi

if ! smoke_root="$(
    mktemp -d "${TMPDIR:-/tmp}/ajm-openfoam14-tooling.XXXXXX" 2>/dev/null
)"; then
    echo "TOOLING_SMOKE_FAIL reason=tempdir_creation_failed" >&2
    exit 24
fi
trap 'rm -rf "$smoke_root"' EXIT
if ! cp -R "${tutorial_candidates[0]}" "$smoke_root/case"; then
    echo "TOOLING_SMOKE_FAIL reason=tutorial_copy_failed" >&2
    exit 24
fi
if ! cd "$smoke_root/case"; then
    echo "TOOLING_SMOKE_FAIL reason=tutorial_copy_directory_invalid" >&2
    exit 24
fi

if ! blockMesh >"$smoke_root/blockMesh.log" 2>&1; then
    echo "TOOLING_SMOKE_FAIL reason=blockMesh_command_failed" >&2
    exit 24
fi
if ! checkMesh -allGeometry -allTopology >"$smoke_root/checkMesh.log" 2>&1; then
    echo "TOOLING_SMOKE_FAIL reason=checkMesh_command_failed" >&2
    exit 24
fi
if ! foamRun >"$smoke_root/foamRun.log" 2>&1; then
    echo "TOOLING_SMOKE_FAIL reason=foamRun_command_failed" >&2
    exit 24
fi

if ! grep -Eq '^[[:space:]]*End[[:space:]]*$' "$smoke_root/foamRun.log"; then
    echo "TOOLING_SMOKE_FAIL reason=solver_did_not_reach_End" >&2
    exit 24
fi

echo "TOOLING_SMOKE_PASS case=pitzDailySteady version=$foam_version"
