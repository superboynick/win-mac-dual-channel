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

foam_version="$(foamVersion 2>&1)"
case "$foam_version" in
    *OpenFOAM-14*|*"OpenFOAM 14"*) ;;
    *)
        echo "TOOLING_VERSION_MISMATCH observed=$foam_version expected=OpenFOAM-14" >&2
        exit 21
        ;;
esac

if [[ -z "${FOAM_TUTORIALS:-}" || ! -d "$FOAM_TUTORIALS" ]]; then
    echo "TOOLING_ENVIRONMENT_INVALID FOAM_TUTORIALS=${FOAM_TUTORIALS:-UNSET}" >&2
    exit 22
fi

mapfile -t tutorial_candidates < <(
    find "$FOAM_TUTORIALS" -type d -name pitzDailySteady -print | LC_ALL=C sort
)
if [[ "${#tutorial_candidates[@]}" -ne 1 ]]; then
    echo "TOOLING_TUTORIAL_IDENTITY_FAIL count=${#tutorial_candidates[@]} expected=1" >&2
    exit 23
fi

smoke_root="$(mktemp -d "${TMPDIR:-/tmp}/ajm-openfoam14-tooling.XXXXXX")"
trap 'rm -rf "$smoke_root"' EXIT
cp -R "${tutorial_candidates[0]}" "$smoke_root/case"
cd "$smoke_root/case"

blockMesh >"$smoke_root/blockMesh.log" 2>&1
checkMesh -allGeometry -allTopology >"$smoke_root/checkMesh.log" 2>&1
foamRun >"$smoke_root/foamRun.log" 2>&1

if ! grep -Eq '^[[:space:]]*End[[:space:]]*$' "$smoke_root/foamRun.log"; then
    echo "TOOLING_SMOKE_FAIL reason=solver_did_not_reach_End" >&2
    exit 24
fi

echo "TOOLING_SMOKE_PASS case=pitzDailySteady version=$foam_version"
