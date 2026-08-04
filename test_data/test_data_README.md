# Small Test Data

This directory contains small dark- and light-data examples (20 and 100 chunks) for testing the unified TR-SFX preprocessing package on a local computer or the Mortimer HPC cluster.


## Prepare a test run

Run the commands from the project root.

### Dark-data test

Copy the dark test inputs and configuration into the main project directories:

```bash
cp test_data/dark_small_test_100/inputs/* path/to/package/inputs/
cp test_data/dark_small_test_100/configs/* path/to/package/configs/
```

Check that the configuration can be loaded:

```bash
python driver.py --config configs/dark-small-100.yaml --list-steps
```

Run locally:

```bash
python driver.py --config configs/dark-small-100.yaml
```

* Submit to SLURM:

```bash
sbatch jobs/preprocess.sbatch configs/dark-small-100.yaml
```

### Light-data test

Copy the light test inputs and configuration into the main project directories:

```bash
cp test_data/light_small_test_100/inputs/* path/to/package/inputs/
cp test_data/light_small_test_100/configs/* path/to/package/configs/
```

Check that the configuration can be loaded:

```bash
python driver.py --config configs/light-small-100.yaml --list-steps
```

Run locally:

```bash
python driver.py --config configs/light-small-100.yaml
```

* Submit to SLURM:

```bash
sbatch jobs/preprocess.sbatch configs/light-small-100.yaml
```

SLURM jobs should be submitted from the project root because the shared `preprocess.sbatch` script uses the submission directory as the project root.

## Important note about the data

These files are intended only for parser, configuration, pipeline, output, and memory smoke tests.

A small subset of the `.stream` chunk blocks was taken from the original source files. The remaining chunk blocks were structurally replicated and their event metadata was modified so that approximately 100 matched snapshots are available for testing.

The `.params` records and the light-data tag-delay records are aligned with the event tags used in the test `.stream` files.

Because part of each test `.stream` file is synthetic or replicated, these files must not be used for scientific analysis, statistical validation, or comparison with production results.

## Cleaning copied test files

After testing, the copied files can be removed from the main input and configuration directories:

```bash
rm -f inputs/dark-small-100.stream \
      inputs/dark-small-100.params \
      inputs/light-small-100.stream \
      inputs/light-small-100.params \
      inputs/light-small-tag-delay-100.xlsx

rm -f configs/dark-small-100.yaml \
      configs/light-small-100.yaml
```

The original copies remain under `test_data/`.
