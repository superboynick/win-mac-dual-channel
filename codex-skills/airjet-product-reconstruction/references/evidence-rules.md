# Evidence and parameter rules

## Source hierarchy

1. Model-specific official data sheet: envelope and system performance.
2. Official technical tutorial/case study: mechanism and integration context.
3. Patent text and figures: architecture candidates and bounded embodiments.
4. Peer-reviewed numerical literature: algorithms and validation methods.
5. Official marketing image: qualitative flow direction and uncertain proportions.
6. Inference: explicit equation/measurement plus uncertainty.

Never move a lower-level claim upward without stronger evidence.

## Parameter record

Each solver input needs:

- stable ID;
- physical name and symbol;
- value/range and unit;
- evidence class `D/P/I/C/U`;
- exact source file and page/paragraph when possible;
- derivation or selection rule;
- models that consume it;
- calibration/validation observable;
- uncertainty and current status.

## Derived parameters

Write the equation and input IDs. Example:

`h_bottom = A_tip + clearance_margin`

If either input changes, mark the derived output stale until regenerated.

## Image measurements

Store the source image, known scale, pixel endpoints, conversion, and pixel uncertainty. Treat diagrams as not-to-scale unless a dimensional cross-check supports them.

## Patent values

Use patent values to create bounded candidates. Do not write “AirJet Mini uses 250 um orifices”; write “R0 uses a 250 um initial candidate within the 200-300 um patent embodiment range.”

## Conflicts

When sources conflict:

1. Check product generation and test conditions.
2. Prefer the exact model's primary data sheet.
3. Preserve both values in the ledger.
4. Create separate configurations if neither can be rejected.
5. Record the decision and validation test.

## Calibration integrity

- Use at least three independent physical layers when possible.
- Hold one observable out for validation.
- Penalize hard-constraint violations.
- Keep multiple acceptable solutions when parameters are non-identifiable.
- Never reinterpret the Mini noise curve as airflow.

## Heat accounting

For the Mini 1 W point:

`Q_total = Q_chip_net + P_airjet = 4.25 W + 1.00 W = 5.25 W`

Model chip heat and AirJet self-heating as separate sources.
