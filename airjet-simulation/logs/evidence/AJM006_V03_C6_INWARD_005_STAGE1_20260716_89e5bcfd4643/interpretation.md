# AJM006 V03 C6 inward 0.05 mm Stage 1 diagnostic

- Task: `ajm-stage1-geometry-fix-inward-overlap-20260716-002`
- Git commit used: `bff96650dfcc230ce610de3ccb3df1aabfe777e4`
- Job: `AJM006-V03-CONTINUOUS-89e5bcfd4643`
- Runtime phase: `PROCESS_EXITED_0`
- Producer status: `FAIL_PRELIMINARY_GEOMETRY`
- P1-P6: `NOT_RUN`
- Raw STEP SHA256: `a409164a00551714c80f34a13bdc1a8e0e56d3e52bf5953397a360d4ae15eb1a`
- Raw STEP bytes: `1809468`
- Raw producer-report SHA256: `f4ab00b39e6601a4637c38effe5491d0630527a2a54960f25d4ad2debd19cdac`

The C6 candidate kept one closed/manifold body and all 972 finite throats, but
it failed the frozen geometry and boundary gates. Moving the four perimeter
ring inner edges inward by 0.05 mm for the full ring height added about
4.587 mm3, not only a bottom-interface overlap. Native volume was
456.36581884263614 mm3 and STEP volume was 456.360248375297 mm3 versus the
451.77881884263951 mm3 analytic route. Native and STEP membrane-top and
membrane-bottom counts both fell from 12/12 to 0/0. STEP X maximum also moved
to 10.89 mm.

Stage 2 was not authorized or run. The next geometry candidate must leave the
original full-height rings unchanged and add only redundant bridge solids at
the bottom-chamber interface, wholly contained in the frozen final union.
