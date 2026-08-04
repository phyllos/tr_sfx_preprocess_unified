# Source notes

This integration package was assembled on 2026-07-16 from two preprocessing projects: 

- Light-data project: `dataPhyto_reduction_light`
- Dark-data project: `tr_sfx_preprocess`

The tag-delay migration was added on 2026-07-28 using the uploaded `tag_delay_all.xlsx.zip` structure.

## What was retained

- The light workflow retains the C1-C13 file/function layout.
- The dark workflow retains the C1-C9 file/function layout and the call sequence used by the existing headless driver.
- A thin `pipeline.py` wrapper was added to each mode.
- Common configuration loading, path resolution, step selection, logging, and memory monitoring were moved into shared code.
- The C6 output schema remains `runID, eventID, nBrg, DRL, delay, OSF, relB`, so C7-C13 do not require format changes.

## Tag-delay migration

The old `delays_original.mat` lookup can now be replaced by the supplied Excel/ZIP table. Legacy MAT support remains available for comparison. Light C6 was also changed from positional C1/C2 pairing to explicit `(runID, eventID)` matching.


