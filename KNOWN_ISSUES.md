# Known issues retained from the legacy implementations

This package intentionally preserves the original C-step algorithms as much as practical. It does **not** silently change scientific behavior.

1. Dark C6 uses independent `np.intersect1d` index sorting and may misalign snapshot metadata.
2. Dark C7 sorts matrix rows by event/serial number, while C6 scaling metadata may remain in another order.
3. Dark C8 retains the legacy hexagonal-style q formula. Confirm this against the intended unit-cell metric before scientific use.
4. Light C6  matches stream and params by `(runID, eventID)` and delay by event tag, but the complete real C1-C7 output still needs comparison against a trusted MATLAB/Python golden dataset.
5. The `power` column in `tag_delay_all.xlsx` is not propagated beyond the input reader. Only tag and delay reproduce the old MAT-file role.
6. Dark C7/C8 remain memory-intensive; the package structure is unified, but the algorithms are not yet fully sparse-optimized.

Use a small MATLAB/Python golden dataset before accepting scientific results.
