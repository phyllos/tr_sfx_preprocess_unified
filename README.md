# Unified TR-SFX Dark/Light Preprocessing Package

This package combines the two preprocessing repositories while retaining separate legacy function folders:

```text
functions/dark/   # C1-C9
functions/light/  # C1-C13
```

A single `driver.py` reads `dataset.mode` from YAML and loads only the matching pipeline.

## Layout

```text
tr_sfx_preprocess_unified/
├── driver.py
├── configs/
│   ├── dark_full.yaml
│   ├── dark_from_c7.yaml
│   ├── light_full.yaml
│   └── light_from_c7.yaml
├── functions/
│   ├── common/
│   ├── dark/
│   └── light/
├── jobs/preprocess.sbatch
├── inputs/
├── outputs/
├── logs/
├── environment.yml
└── KNOWN_ISSUES.md
```

## Environment

```bash
conda env create -f environment.yml
conda activate tr_sfx_preprocess

# Optional: install the command-line entry point
pip install -e .
```

## Run locally or on a login node for a small test

```bash
python driver.py --config configs/light_from_c7.yaml
python driver.py --config configs/dark_full.yaml

# Equivalent after pip install -e .
tr-sfx-preprocess --config configs/light_from_c7.yaml
```

Relative paths are anchored at the package root. `~` and environment variables such as `$HOME` are expanded.

List the available stages:

```bash
python driver.py --config configs/light_full.yaml --list-steps
```

## Submit to SLURM

```bash
sbatch jobs/preprocess.sbatch configs/light_full.yaml
sbatch jobs/preprocess.sbatch configs/dark_full.yaml
```

## Switching mode

Light:

```yaml
dataset:
  mode: light
```

Dark:

```yaml
dataset:
  mode: dark
```

The mode parameter is used only to select `functions/light/pipeline.py` or `functions/dark/pipeline.py`. The individual C functions do not contain repeated mode checks.

## Starting from an intermediate step

For the common light fast test:

```yaml
inputs:
  c7_file: inputs/DATA_upto1ps/dataPhyto_upto1ps_int_sortdelay_nS135041_nBrg62530.mat
pipeline:
  start_step: C8
  stop_step: C13
```

A ready-to-edit example is provided in `configs/dark_from_c7.yaml`. For a dark C8 restart, supply the required artifacts:

```yaml
inputs:
  c6_file: outputs/.../merged_snapshotInfo_dark_allInfo.hdf5
  c7_file: outputs/.../dark_Intensity_sortEvent_....hdf5
  c7_directory: outputs/.../dark-clean-2024_PreProcessed_Data_0
pipeline:
  start_step: C8
  stop_step: C9
```

## Important

Read `KNOWN_ISSUES.md`. The purpose of this first unified version is structural integration and output-comparison testing. It deliberately does not hide known snapshot-alignment, q-metric, or memory concerns inherited from the previous packages.

## Included tests

```bash
pytest -q
```

The tests check mode selection and run small synthetic smoke pipelines for light C8-C13 and dark C8-C9. They do not replace validation with the real SACLA datasets.

## Source provenance

See `SOURCE_NOTES.md` for how the two existing projects were incorporated. Before replacing a production checkout on Mortimer, compare the files under `functions/dark/` and `functions/light/` with the exact versions currently used by the jobs.
