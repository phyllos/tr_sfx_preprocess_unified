# Test report

Tested on 2026-07-28 in the virtual environment.

## Passed

- Python syntax compilation for `driver.py`, `functions/`, and `tests/`.
- Light mode step discovery: C1-C13.
- Dark mode step discovery: C1-C9.
- Editable installation and the `tr-sfx-preprocess` command.
- Light pipeline: C8-C13.
- Dark pipeline: C8-C9.
- Supplied-style one-cell CSV `.xlsx` tag-delay parsing.
- Light C6 key-based joining when stream and params arrays are intentionally in different orders.
- Pytest suite: 5 tests passed.


- Full C1-to-final processing with the real `.stream`, `.params`, delay `.mat`, or packed light-data file. 
- Full-memory behavior on the Mortimer compute nodes.


## Uploaded delay file checks

The uploaded `tag_delay_all.xlsx.zip` was read successfully:

```text
rows:        388935
unique tags: 388935
tag range:   1497032506 to 1498681680
delay range: -1882.2666666652 to 3358.800000015
```

The 388935 rows equal the previous MATLAB vector sizes exactly:

```text
69131 tag_3ps/delay_3ps rows
+ 319804 tag_1ps/delay_1ps rows
= 388935 combined rows
```

At data row 69132, the combined file starts the 1 ps block with tag `1497731206` and delay `188.9333333348`; the following delay sequence matches the MATLAB `delay_1ps` screenshot.


## Not tested here

- Numerical equivalence to the original MATLAB outputs on the complete datasets.

Run the package first on a small dataset, then compare its HKL and HDF5 outputs with the other package before replacing a production workflow.





