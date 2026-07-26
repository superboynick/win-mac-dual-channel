# AirJet B coupling contract reference prototype v2

`REFERENCE_ONLY_NO_COUPLED_RUNTIME_P1_P6_NOT_PASSED`

This repository reference package defines two solver-neutral handoff contracts:

- `schemas/p2_to_p3_structural_displacement_handoff.schema.json` transfers a full-field P2 structural displacement result into P3 cell CFD.
- `schemas/p4_to_p5_wall_cht_handoff.schema.json` transfers full-product P4 wall fields into P5 CHT.

It does not run ANSYS, OpenFOAM, a coupled solver, Git, or any project watcher. It does not prove any P1-P6 gate. The final target remains the complete product; a single-cell P2/P3 handoff is calibration input only.

## Trust boundary

The JSON Schema files are genuine Draft 2020-12 schemas. The standard-library validator implements the schema keywords used here and then applies engineering semantic checks which JSON Schema alone cannot safely express. Acceptance means only that a document satisfies this reference contract. It is not solver authorization, artifact authenticity proof, or stage-gate PASS. Input is limited to 1 MiB, 32 JSON levels, and 10,000 JSON nodes before recursive validation.

Every handoff binds `task_id`, `session_id`, opaque `snapshot_id`, `receipt_id`, and the SHA-256 of the exact schema bytes. Every external artifact has a unique role, normalized unique relative path, byte size, and SHA-256.

### Artifact consumer boundary

This prototype validates artifact **metadata only**. It neither opens an external field artifact nor recomputes its size/hash, and therefore cannot claim that nodes, connectivity, displacement vectors, wall fields, or region maps contain valid full-field data. `metadata_contract_accepted` is deliberately not `artifact_contents_verified`.

A production consumer must resolve each artifact only below a trusted snapshot capability, using the declared relative path; reject symlinks/reparse escapes and substitutions; open the artifact through that boundary; recompute byte size and SHA-256 from the opened handle; compare both to the descriptor; then parse and validate the expected field format. Validation and use must remain tied to the same opened object to avoid time-of-check/time-of-use substitution.

Paths are interpreted conservatively for cross-platform/Windows consumption. Colons and ADS syntax, absolute/parent/dot/empty segments, control characters, trailing dot/space, and Windows device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`, including extensions) are rejected. Uniqueness is checked after separator normalization, Unicode NFC normalization, and case folding.

Provenance classes are `D` direct model-specific data, `P` patent bounds, `I` inference, `C` calibration, and `U` unresolved. The schema can represent all five classes, while the semantic gate rejects any active input that references `U`. Class and assertion kind must agree. An inference must remain labeled `I` / `inference`, cite a derivation, and carry non-zero uncertainty; it cannot masquerade as a measured fact.

## P2 to P3 invariants

- explicit coordinate frame, origin, orthonormal axes, handedness, and length unit;
- explicit frequency, phase reference, samples per cycle, period count, and time origin;
- node, connectivity, and three-component displacement-field artifacts;
- displacement components exactly `ux`, `uy`, `uz`; scalar displacement roles are forbidden;
- mapping tolerance and a conservative `maximum_unmapped_fraction <= 0.0001` (0.01%) over all displacement-field nodes; any unmapped active membrane node is an unconditional failure;
- independent minimum-gap, maximum-stress, and electrical-power fields. Minimum gap must be strictly positive because zero/negative means closure or penetration and must return to P2; stress and electrical power may be zero but not negative;
- no nulls, unknown sentinels, duplicate JSON keys, duplicate artifact roles, or duplicate paths.

## P4 to P5 invariants

- an `h(x,y,t)` wall-field artifact plus either wall temperature or wall heat-flux field;
- region/interface map with dimensionless unit `1`, explicit interface list, and an exactly equal set of solid/material regions—neither missing nor unreferenced extras;
- explicit coordinate frame and one of three non-ambiguous time forms: `cycle_phase` is periodic with at least two non-duplicated phase samples and requires `step * sample_count = cycle_period_s`; `instantaneous` is non-periodic with one or more samples; `cycle_mean` is exactly one non-periodic averaged field with an averaging window;
- independent `q_chip`, `q_airjet_self`, and `q_total`, with `q_total = q_chip + q_airjet_self` checked using decimal arithmetic;
- at `MINI_1W_REFERENCE`, the only accepted accounting is 4.25 W net chip heat + 1.00 W AirJet self-heat = 5.25 W total. A 5.25 W chip load plus another 1 W is rejected.

## Run

From this directory:

```powershell
python -m compileall -q src tests
python run_tests.py
python -m airjet_coupling.cli validate fixtures/valid/p2_to_p3.json
python -m airjet_coupling.cli validate fixtures/valid/p4_to_p5_temperature.json
```

The CLI command needs `PYTHONPATH=src` when the package is not installed. Tests set that path themselves. No third-party package is required. If `jsonschema` is later available, these schemas can additionally be checked with an independent Draft 2020-12 implementation.

`SOURCE_MANIFEST.csv` hashes every authored source/fixture except the manifest and seal. `SEAL.txt` binds that manifest and records the verification commands; it is reproducibility metadata, not a cryptographic signature.
