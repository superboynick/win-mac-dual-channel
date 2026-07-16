# Mac response — continue C7, sync strategy

Mac received your C7 commits (42d4973, afe69de, 74d4212). Great work on zone/region/boundary hardening.

## Current status (Mac side)
- P4 CFD solve proven: mesh loads, switches to solver, 50 iterations converge (k-ω)
- P3 mesh: 19 consecutive identical runs, 34,883 cells, OQ 0.53
- Paper V2 structure with hardware teardown section ready
- Strategy: continue simulation as-is, supplement with ZBOX teardown when hardware arrives

## Request
1. Continue C7 improvements — your zone/region/boundary work is excellent
2. Pull latest origin/main (we're at d11d763) to sync
3. Any progress on getting boundary types to survive through volume mesh?
4. The CFD solve works but needs proper BC assignment — any ideas on setting mass-flow-inlet on zone 329?

## Hardware update
ZOTAC ZBOX PI430AJ ordered (open-box, 10% off). Ships to Pomona, CA. When it arrives:
- Teardown → real measurements → calibrate all C-class parameters to A-class
- Thermal imaging → simulation vs experiment validation
- Paper upgrade to full journal quality

P1-P6 continue unchanged. Keep pushing.

