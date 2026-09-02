# Unified TR-SFX Dark/Light Preprocessing Package

Table of Contents
- [Background](#background)
- [Main features](#main-features)
- [Project structure](#project-structure)
- [Processing workflows](#processing-workflows)
- [Getting started](#getting-started)
- [Output files, HDF5 file organization and memory logs](#output-files-hdf5-file-organization-and-memory-logs)
- [Run the tests](#run-the-tests)
- [Additional documentation](#additional-documentation)
- [Starting from an intermediate step](#starting-from-an-intermediate-step)
- [Common problems](#common-problems)


-=- -=- -=- -=- -=- -=- -=- -=- 

## Background

This package provides one configuration-driven interface for preprocessing **dark** and **light** time-resolved serial femtosecond crystallography (TR-SFX) datasets.

It combines the previous dark-data and light-data preprocessing projects while retaining their numbered processing functions:

```text
functions/dark/    C1-C9
functions/light/   C1-C13
```

Keeping the original C-stage structure makes it easier to compare this unified package with earlier runs, MATLAB/Python implementations, and existing analysis notes. A single `driver.py` reads `dataset.mode` from a YAML file and loads the matching pipeline.

This package is designed for:

- full preprocessing jobs on the UWM Mortimer HPC cluster;
- small tests on a local workstation or laptop;
- reproducible runs controlled by YAML configuration files;
- monitoring the memory use of each processing stage;
- keeping dark- and light-data processing under one project structure;
- restarting from selected intermediate products.

> Read [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) before using generated files for scientific interpretation. This version focuses on structural integration and reproducible execution; it does not automatically resolve every scientific or performance concern inherited from the original packages.

---

## Main features

### One driver for dark and light data

Select the processing mode in the configuration file:

```yaml
dataset:
  mode: light
```

or:

```yaml
dataset:
  mode: dark
```

The driver loads either `functions/light/pipeline.py` or `functions/dark/pipeline.py`. The original C functions remain in separate folders and do not need repeated mode checks.

### YAML-based configuration

The files under `configs/` define:

- input and output paths;
- dark/light mode;
- start and stop stages;
- unit-cell and experimental parameters;
- delay-selection settings for light data;
- negative-value, DRL-mask, averaging, and other processing options.

Relative paths are resolved from the package root. `~` and environment variables such as `$HOME` are expanded.

### Per-stage memory monitor

The driver records memory consumption and runtime for every C stage. Typical log entries are:

```text
[START] light C8 | current=... | process_peak=...
[MONITOR] light C8 | elapsed=... | current=... | step_peak=... | process_peak=...
[ END ] light C8 | elapsed=... | current=... | step_peak=... | process_peak=...
```

Memory is sampled approximately every 5 seconds and reported approximately every 30 seconds. This helps identify expensive stages such as matrix packing and scaling.

### Local and SLURM execution

The same driver and configuration files can be used for small local tests and full HPC (Mortimer) jobs.

### Intermediate restart

The pipeline can begin and end at selected C stages. Example restart configurations are included for light C8-C13 and dark C8-C9.

---

## Project structure

```text
tr_sfx_preprocess_unified/
├── driver.py                    # Unified command-line driver
├── environment.yml              # Conda environment
├── pyproject.toml               # Optional editable installation
│
├── configs/
│   ├── dark_full.yaml           # Full dark C1-C9 run
│   ├── dark_from_c7.yaml        # Dark restart at C8
│   ├── light_full.yaml          # Full light C1-C13 run
│   └── light_from_c7.yaml       # Light restart at C8
│
├── functions/
│   ├── common/
│   │   ├── config.py            # Configuration and path handling
│   │   └── memory_monitor.py    # Memory monitoring
│   ├── dark/                    # Dark C1-C9 functions
│   │   └── pipeline.py
│   └── light/                   # Light C1-C13 functions
│       └── pipeline.py
│
├── inputs/                      # User-provided input files
├── outputs/                     # Generated preprocessing products
├── logs/                        # SLURM stdout/stderr logs
├── jobs/preprocess.sbatch       # Shared SLURM script
├── results_metric/              # Output-comparison tools
├── tests/                       # Driver and smoke tests
│
├── KNOWN_ISSUES.md
├── SOURCE_NOTES.md
└── TEST_REPORT.md
```

## Processing workflows

The unified package preserves the numbered processing stages from the original dark- and light-data projects. Both pipelines convert CrystFEL and partialator outputs into reflection matrices that can be used for downstream analysis.

```text
CrystFEL .stream and partialator .params files
                    |
                    v
      snapshot metadata and reflections
                    |
                    v
       packed reflection matrices T and M
                    |
                    v
     corrections, scaling, and boosting
                    |
                    v
       HDF5 products for later analysis
```

The main difference is that light data contains pump-probe delay information. It therefore includes additional stages for delay selection, Lorentz-polarization-factor correction, and an optional diffraction-resolution-limit mask.


### Light-data pipeline: C1-C13

Light-data preprocessing normally uses (Example):

```text
upto1ps.params
upto1ps.stream
tag_delay_all.xlsx
```

The tag-delay file can also be supplied as `tag_delay_all.xlsx.zip`. The light pipeline uses the event tag shared by the `.stream`, `.params`, and tag-delay table to attach a pump-probe delay to each matched snapshot, then produces delay-resolved sparse reflection matrices.

| Step | Main purpose | Main input | Main output |
|---|---|---|---|
| C1 | Read partialator parameters | Light `.params` file | `runID`, `eventID`, `OSF`, `relB` |
| C2 | Read stream metadata | Light `.stream` file | `runID`, `eventID`, `nRefl`, `DRL` |
| C3 | Extract indexed reflections | Light `.stream` file | Per-snapshot `h k l I` files |
| C4 | Find the maximum Miller-index range | C3 reflection files | `h_max`, `k_max`, `l_max` |
| C5 | Compute reflection redundancy | C3 reflection files | Reflection-redundancy array |
| C6 | Combine light-data metadata by snapshot/event keys | C1, C2, and a tag-delay table | Snapshot metadata including delay |
| C7 | Pack the final reflection matrices | C3, C5, and C6 | Delay-sorted sparse `T` and `M` matrices |
| C8 | Uniformize the delay distribution | C7 file | Reduced, delay-balanced HDF5 file |
| C9 | Apply the LPF correction | C8 file | LPF-corrected HDF5 file |
| C10 | Generate a DRL mask, optionally | C9 file | Sparse `maskDRL` matrix |
| C11 | Apply or bypass the DRL mask | C9 and optional C10 files | LPF+DRL HDF5 file |
| C12 | Apply partialator scaling | C11 file | Scaled HDF5 file and optional average `.hkl` file |
| C13 | Boost by reflection multiplicity | C12 file | Final boosted HDF5 file |

The principal packed matrices are:

- `T`: reflection intensities for every snapshot;
- `M`: an observation mask showing which reflections were measured.

Each row represents one snapshot. Each column represents one unique Miller index `(h, k, l)`.

#### DRL-mask behavior

By default, C11 can reproduce the current MATLAB test behavior:

```matlab
maskDRL = ones(nS,nBrg)
```

In this mode, reflections beyond the diffraction-resolution limit are not removed. To generate and apply the physical DRL mask, enable both options in the light configuration:

```yaml
processing:
  make_drl_mask: true
  use_drl_mask: true
```

#### Tag-delay input and C6 matching

The preferred delay input is a lookup table containing at least these columns:

```text
tag_number,delay
```

An optional `power` column is allowed but is not used by the current preprocessing stages:

```text
tag_number,delay,power
1497731226,203.3333333348,118.906
```

The reader supports:

```text
.xlsx
.xlsm
.csv
.txt
.tsv
.zip   # archive containing exactly one supported table file
.mat   # legacy delays_original.mat compatibility
```

Both a normal multi-column Excel worksheet and the supplied one-cell CSV-style worksheet are accepted. In the one-cell form, each row contains text such as `1497731226,203.3333333348,118.906` in column A.

```text
C2 stream metadata
(runID, eventID, nRefl, DRL)
            |
            | join by (runID, eventID)
            v
C1 partialator metadata
(runID, eventID, OSF, relB)
            |
            | join by eventID == tag_number
            v
tag-delay table
(tag_number, delay)
```

The generated C6 HDF5 file also records matching statistics in attributes including:

```text
tag_delay_source
matched_snapshots
missing_params_snapshots
missing_delay_snapshots
duplicate_identical_params
duplicate_identical_tags
```

Conflicting duplicate tags or conflicting duplicate `(runID, eventID)` parameter records cause an error rather than being silently overwritten.


### Dark-data pipeline: C1-C9

Dark-data preprocessing normally uses (Example):

```text
dark-clean-2024.params
dark-clean-2024.stream
```

Dark data has no pump-probe delay dimension, so it does not include delay uniformization or the light-specific LPF/DRL stages.

| Step | Main purpose | Main input | Main output |
|---|---|---|---|
| C1 | Read partialator parameters | Dark `.params` file | `nSer`, `OSF`, `relB` |
| C2 | Read stream metadata | Dark `.stream` file | `nSer`, `nRefl`, `DRL` |
| C3 | Extract and symmetry-reduce indexed reflections | Dark `.stream` file | Per-snapshot `h k l I` files and snapshot summary |
| C4 | Find the maximum Miller-index range | C3 reflection files | `h_max`, `k_max`, `l_max` |
| C5 | Compute reflection redundancy | C3 reflection files | Reflection-redundancy array |
| C6 | Combine parameters and snapshot metadata | C1, C2, and C3 summary | `SerNo`, `nBrg`, `DRL`, `OSF`, `relB` |
| C7 | Pack the final reflection matrices | C3, C4, C5, and C6 | Sparse `T` and `M` matrices |
| C8 | Apply partialator scaling | C6 and C7 files | Scaled matrix and optional average `.hkl` file |
| C9 | Boost by reflection multiplicity | C7 and C8 files | Final boosted HDF5 file |

The dark and light implementations remain separate under:

```text
functions/dark/
functions/light/
```

The unified driver selects one numbered pipeline according to `dataset.mode`. It does not merge all dark- and light-specific calculations into one large function.


---

## Getting started

### 1. Enter the package directory

On HPC (Mortimer):

```bash
cd "$HOME/Data-cxfel/tr_sfx_preprocess_unified"
```

Or:

```bash
cd /path/to/tr_sfx_preprocess_unified
```

On a local computer:

```bash
cd /path/to/tr_sfx_preprocess_unified
```

Run the following commands from the package root.

---

### 2. Rebuild the environment

#### Load Conda on HPC (Mortimer)

When rebuilding the environment on the server, first source the base Conda installation:

```bash
source "$HOME/Data-cxfel/conda/etc/profile.d/conda.sh"
```

Or:

```bash
source "/path/to/conda/etc/profile.d/conda.sh"
```

The Conda installation path above matches the current HPC (Mortimer) setup. If Conda is installed elsewhere, update the corresponding path in jobs/preprocess.sbatch before submitting a job.

#### Create the environment

```bash
conda env create -f environment.yml
```

The Conda `Solving environment` step may take a long time. In that case, use the faster `libmamba` solver:

```bash
conda env create -f environment.yml --solver libmamba
```

To remove and rebuild an existing environment:

```bash
conda env remove -n tr_sfx_preprocess
conda env create -f environment.yml --solver libmamba
```

#### Activate and deactivate

```bash
conda activate tr_sfx_preprocess
```

When finished:

```bash
conda deactivate
```

#### Test the environment

Make sure the environment is active:

```bash
python -c "import numpy, scipy, h5py, yaml, pyxtal, openpyxl; print('Environment OK')"
```

Expected output:

```text
Environment OK
```

The package can be run directly with `python driver.py`. Optionally install the command-line entry point:

```bash
pip install -e . --no-deps
```

---

### 3. Test the driver and configuration

Check that Python can access the driver and light configuration:

```bash
python driver.py \
    --config configs/light_full.yaml \
    --list-steps
```

Expected light stages:

```text
C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12 C13
```

Check the dark pipeline:

```bash
python driver.py \
    --config configs/dark_full.yaml \
    --list-steps
```

Expected dark stages:

```text
C1 C2 C3 C4 C5 C6 C7 C8 C9
```

`--list-steps` only validates configuration loading and module imports; it does not process the data.

---

### 4. Add input files

Copy the required files from the existing project input folders into this package's `inputs/` directory. `.stream` files are usually much larger than `.params` or `.xlsx` (tag-delay tables) files and may take longer to transfer.

For large files, `rsync` is recommended because it shows progress and can resume an interrupted transfer:

```bash
rsync -ah --info=progress2 /path/to/source.file inputs/
```

#### Dark data

Example input files:

```text
inputs/dark-clean-2024.params
inputs/dark-clean-2024.stream
```

Example commands on HPC (Mortimer):

```bash
cp "$HOME/Data-cxfel/tr_sfx_preprocess/inputs/dark-clean-2024.params" \
   "$HOME/Data-cxfel/tr_sfx_preprocess_unified/inputs/"

rsync -ah --info=progress2 \
   "$HOME/Data-cxfel/tr_sfx_preprocess/inputs/dark-clean-2024.stream" \
   "$HOME/Data-cxfel/tr_sfx_preprocess_unified/inputs/"
```

Alternatively, locate the required files and copy them into the `inputs/` directory.

#### Light data

Example input files:

```text
inputs/tag_delay_all.xlsx
inputs/upto1ps.params
inputs/upto1ps.stream
```

Example commands on HPC (Mortimer):

```bash
cp "$HOME/Data-cxfel/phytochrome2026/dataPhyto_reduction_light/inputs/tag_delay_all.xlsx" \
   "$HOME/Data-cxfel/tr_sfx_preprocess_unified/inputs/"

cp "$HOME/Data-cxfel/phytochrome2026/dataPhyto_reduction_light/inputs/upto1ps.params" \
   "$HOME/Data-cxfel/tr_sfx_preprocess_unified/inputs/"

rsync -ah --info=progress2 \
   "$HOME/Data-cxfel/phytochrome2026/dataPhyto_reduction_light/inputs/upto1ps.stream" \
   "$HOME/Data-cxfel/tr_sfx_preprocess_unified/inputs/"
```

Alternatively, locate the required files and copy them into the `inputs/` directory.

Confirm the files:

```bash
ls -lh inputs/
```

Large experimental inputs and generated outputs should not be committed to Git.

---

### 5. Review the configuration

Before running, edit the relevant YAML file and confirm the paths and parameters.

#### Light example

```yaml
dataset:
  mode: light
  name: upto1ps

inputs:
  stream: inputs/upto1ps.stream
  params: inputs/upto1ps.params
  tag_delay_file: inputs/tag_delay_all.xlsx

# Optional. Omit this block to use the first worksheet.
delay_input:
  sheet: in

output:
  directory: outputs/light_upto1ps

pipeline:
  start_step: C1
  stop_step: C13
```

`delay_input.sheet` is optional. When it is omitted, the first worksheet is used. For the supplied workbook, the worksheet is named `in`.

The remaining light sections define the unit cell, wavelength, delay selection, random seed, DRL-mask settings, negative-value handling, and HKL averaging.

#### Dark example

```yaml
dataset:
  mode: dark
  name: dark_clean_2024

inputs:
  stream: inputs/dark-clean-2024.stream
  params: inputs/dark-clean-2024.params

output:
  directory: outputs/dark_clean_2024

pipeline:
  start_step: C1
  stop_step: C9
```

The remaining dark sections define the unit cell, HKL search limits, intensity/amplitude mode, negative-value handling, and HKL averaging.

Use YAML booleans without quotation marks:

```yaml
remove_negative_pixels: false
```

---

### 6. Run a small local test

Activate the environment and run an appropriately small dataset or restart configuration:

```bash
conda activate tr_sfx_preprocess

python driver.py \
    --config configs/light_from_c7.yaml
```

Dark example:

```bash
python driver.py \
    --config configs/dark_from_c7.yaml
```

Do not run a full production dataset on the HPC (Mortimer) submit/login node. Direct execution there should be limited to imports, `--list-steps`, tests, and small files.

---

### 7. Submit a full SLURM job

From the package root:

```bash
cd "path/to/tr_sfx_preprocess_unified"
```

Submit light data:

```bash
sbatch jobs/preprocess.sbatch configs/light_full.yaml
```

Or:

```bash
sbatch jobs/preprocess_light_job01.sbatch configs/light_full.yaml
```

Submit dark data:

```bash
sbatch jobs/preprocess.sbatch configs/dark_full.yaml
```

Or:

```bash
sbatch jobs/preprocess_dark_job01.sbatch configs/dark_full.yaml
```

The shared SBATCH script uses the directory from which `sbatch` is submitted as the project root. Therefore, submit it from the package root unless `PROJECT_ROOT` is explicitly provided.

Example:

```bash
export PROJECT_ROOT=/path/to/tr_sfx_preprocess_unified

sbatch \
    "$PROJECT_ROOT/jobs/preprocess.sbatch" \
    "$PROJECT_ROOT/configs/light_full.yaml"
```

Check the queue:

```bash
squeue -u "$USER"
```

Logs are written to:

```text
logs/<job-name>-<job-id>.out
logs/<job-name>-<job-id>.err
```

Follow a log:

```bash
tail -f logs/<job-name>-<job-id>.out
```

Before a production run, review the resource requests in `jobs/preprocess.sbatch`, especially `--job-name`, `--partition`, `--nodelist`, `--mem`, `--time`, and `--cpus-per-task`.

The current pipeline launches one Python process, so the normal layout is:

```bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
```

A fixed `--nodelist` can be useful for debugging but may increase queue time.

---

## Output files, HDF5 file organization and memory logs

Output directories are defined in the YAML files, for example:

```yaml
output:
  directory: outputs/light_upto1ps
```

or:

```yaml
output:
  directory: outputs/dark_clean_2024
```

The package keeps intermediate products because parsing large `.stream` files and packing reflection matrices can be expensive. These files can also be used to restart the pipeline from a later stage.

### Light-data outputs

A full light-data run creates files similar to:

```text
partialator_params_phyto_<name>.hdf5
partialator_params_phyto_<name>.dat
merged_snapshotInfo_phyto_<name>.hdf5
merged_snapshotInfo_phyto_<name>.dat
sacla2021_<name>_hklI/
<name>_snapshotInfo.dat
hkl_max_<name>.dat
redundancy_<name>.hdf5
merged_snapshotInfo_phyto_<name>_allInfo.hdf5
merged_snapshotInfo_phyto_<name>_allInfo.dat
dataPhyto_<name>_int_sortdelay_nS..._nBrg....hdf5
dataPhyto_<name>_C8_unifdelay.hdf5
dataPhyto_<name>_C9_LPF.hdf5
maskDRL_<name>.hdf5
dataPhyto_<name>_C11_LPF_DRL.hdf5
dataPhyto_<name>_C12_LPF_DRL_SCL.hdf5
dataPhyto_<name>_C12_LPF_DRL_SCL_AVG.hkl
dataPhyto_<name>_C13_LPF_DRL_SCL_BST.hdf5
```

The exact C7 filename includes the number of selected snapshots (`nS`) and unique reflections (`nBrg`). Later filenames are generated by the unified pipeline from the dataset name and stage number.

Important light-data matrices include:

| Stage | Main sparse matrices |
|---|---|
| C7-C8 | `T`, `M` |
| C9 | `T_lpf`, `M` |
| C10 | `maskDRL` |
| C11 | `T_lpf_drl`, `M_drl` |
| C12 | `T_lpf_drl_scl`, `M_drl` |
| C13 | `T_lpf_drl_scl_bst`, `M_drl` |

When the configuration contains:

```yaml
processing:
  generate_hkl_average: true
```

C12 also writes an average `.hkl` file. This file can be used by tools under `results_metric/` to compare the current result with earlier MATLAB or Python outputs.

Depending on the processing stage, common light-data metadata datasets include:

```text
/delay
/DRL
/OSF
/relB
/runID
/eventID
/miller_h
/miller_k
/miller_l
/indSort_delay
/ind_delay_uniform
```

C8 also records both MATLAB-style 1-based indices and Python-style 0-based indices for selected snapshots.

The C6 HDF5 file contains the joined metadata datasets:

```text
/runID
/eventID
/nBrg
/DRL
/delay
/OSF
/relB
```

It also stores the tag-delay source path and C6 matching counts as HDF5 attributes. Check these attributes and the printed C6 summary when the final snapshot count is smaller than the number of `.params` or `.stream` records.


### Dark-data outputs

A full dark-data run creates intermediate products similar to:

```text
PARAMETERS_0/
PARAMETERS_0/partialator_params_<params-name>.hdf5
PARAMETERS_0/merged_snapshot_info_<name>_dark.hdf5
PARAMETERS_0/merged_snapshot_info_<name>_dark.dat
individual_snapshots_0/
snapshotInfo0.dat
max_vals.hdf5
redundancy.hdf5
merged_snapshotInfo_dark_allInfo.hdf5
merged_snapshotInfo_dark_allInfo.dat
<stream-name>_PreProcessed_Data_0/
```

The directory numbers increase automatically if previous runs already exist.

Typical final dark-data products are:

```text
dark_Intensity_sortEvent_nS..._nBrg....hdf5
data_dark_int_sortEvent_scl_nS..._nBrg....hdf5
data_dark_int_sortEvent_scl_avg_nS..._nBrg....hkl
data_dark_int_sortEvent_scl_bst_nS..._nBrg....hdf5
```

When amplitude mode is selected, the corresponding intensity labels are replaced by amplitude labels.

Important dark-data matrices include:

| Stage | Main sparse matrices |
|---|---|
| C7 | `T`, `M` |
| C8 | `T_scl` |
| C9 | `T_bst`, `T_scl`, `M` |

Common dark-data metadata include:

```text
/nSer or /SerNo
/nBrg
/DRL
/OSF
/relB
/miller_h
/miller_k
/miller_l
```

Not every metadata vector is copied into every later-stage file. The C6 metadata file and C7 packed file should be retained together with the final products.

### Sparse-matrix storage

The dark and light functions retain the storage conventions of their original packages.

#### Light-data sparse groups

Light matrices are stored in SciPy CSC format:

```text
/<matrix-name>/data
/<matrix-name>/indices
/<matrix-name>/indptr
/<matrix-name>/shape
```

For example:

```text
/T/data
/T/indices
/T/indptr
/T/shape
```

The sparse group also contains the attribute:

```text
format = csc
```

#### Dark-data sparse groups

Dark matrices use the legacy CSR group naming convention:

```text
/<matrix-name>_csr/data
/<matrix-name>_csr/indices
/<matrix-name>_csr/indptr
```

The matrix shape is stored as a group attribute. Examples include:

```text
/T_csr/
/M_csr/
/T_scl_csr/
/T_bst_csr/
```

Do not assume that a sparse matrix is stored as a normal two-dimensional HDF5 dataset. Use the package's sparse-reading functions or reconstruct the matrix with SciPy.


### Logs and memory monitoring

SLURM output and error logs are written to:

```text
logs/<job-name>-<job-id>.out
logs/<job-name>-<job-id>.err
```

The memory monitor prints records such as:

```text
[START] light C8 | current=... | process_peak=...
[MONITOR] light C8 | elapsed=... | current=... | step_peak=...
[ END ] light C8 | elapsed=... | step_peak=... | process_peak=...
```

The reported values mean:

- `current`: current resident memory (RSS) used by the Python process;
- `step_peak`: highest memory (RSS) observed during the current C stage;
- `process_peak`: highest memory (RSS) observed during the complete driver run;
- `elapsed`: time spent in the current stage.


At the end of a successful run, the driver prints the generated artifact paths and final process-memory peak. If a stage fails, look for `[FAIL]`, read the Python traceback, and inspect both the `.out` and `.err` files.

Use this to identify whether C7, C8, or another step is the memory bottleneck.

---

## Run the tests

```bash
conda activate tr_sfx_preprocess
pytest -q
```

The tests cover:

- dark/light pipeline selection;
- reading the supplied one-cell CSV-style `.xlsx` tag-delay table;
- reading a `.zip` archive containing the tag-delay workbook;
- C6 key-based matching when C1 and C2 use different row orders;
- a small synthetic light C8-C13 workflow;
- a small synthetic dark C8-C9 workflow.

These are package smoke tests. They do not replace scientific validation against trusted outputs from the original packages or full SACLA datasets.

---

## Additional documentation

- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md): inherited scientific and performance concerns.
- [`SOURCE_NOTES.md`](SOURCE_NOTES.md): origin of the dark and light functions.
- [`TEST_REPORT.md`](TEST_REPORT.md): packaged smoke-test status.

Compare production outputs with trusted results from the previous packages before replacing an established workflow.

---

## Starting from an intermediate step

Restarting from an intermediate stage avoids repeating expensive parsing and packing. The intermediate files must match the current dataset and relevant configuration.

### Light: C8-C13 from an existing C7 file

Edit `configs/light_from_c7.yaml`:

```yaml
dataset:
  mode: light
  name: upto1ps

inputs:
  c7_file: inputs/DATA_upto1ps/dataPhyto_upto1ps_int_sortdelay_nS135041_nBrg62530.mat

output:
  directory: outputs/light_from_c7

pipeline:
  start_step: C8
  stop_step: C13
```

Run locally:

```bash
python driver.py --config configs/light_from_c7.yaml
```

Or submit to SLURM:

```bash
sbatch jobs/preprocess.sbatch configs/light_from_c7.yaml
```

### Dark: C8-C9 from existing C6/C7 products

Edit `configs/dark_from_c7.yaml`:

```yaml
dataset:
  mode: dark
  name: dark_restart

inputs:
  c6_file: outputs/dark_clean_2024/PARAMETERS_0/merged_snapshotInfo_dark_allInfo.hdf5
  c7_file: outputs/dark_clean_2024/dark-clean-2024_PreProcessed_Data_0/dark_Intensity_sortEvent_nS00000_nBrg00000.hdf5
  c7_directory: outputs/dark_clean_2024/dark-clean-2024_PreProcessed_Data_0

output:
  directory: outputs/dark_restart

pipeline:
  start_step: C8
  stop_step: C9
```

Replace the placeholder C7 filename with the actual output filename, then run:

```bash
python driver.py --config configs/dark_from_c7.yaml
```

or:

```bash
sbatch jobs/preprocess.sbatch configs/dark_from_c7.yaml
```

Do not reuse an intermediate file generated with different source data, symmetry settings, snapshot selections, or unit-cell parameters unless that difference is intentional and scientifically justified.

---

## Common problems

### Problem: input file not found

Check the configured input paths and confirm that the files exist:

Example: light data

```bash
ls -lh inputs/upto1ps.params
ls -lh inputs/upto1ps.stream
ls -lh inputs/tag_delay_all.xlsx
# or
ls -lh inputs/tag_delay_all.xlsx.zip
```

### Problem: C6 cannot find the Excel worksheet

For the supplied workbook, use:

```yaml
delay_input:
  sheet: in
```

To use the first worksheet regardless of its name, remove the `delay_input` block. If the configured name is not found, C6 reports the available worksheet names.

### Problem: job killed by memory limit

Check the end of the `.err` file and `sacct`:

```bash
tail -n 50 logs/*.err
sacct -j <JOBID> --format=JobID,State,Elapsed,ReqMem,MaxRSS,ExitCode
```

If C8 reaches close to the requested memory, increase memory allocation in sbatch file:

```bash
#SBATCH --mem=160G
```

### Problem: Light data C11 result differs from MATLAB or other reference data

Make sure the DRL mask settings match the MATLAB behavior. For current MATLAB-style pass-through behavior:

```yaml
make_drl_mask: false
use_drl_mask: false
```

For real DRL masking:

```yaml
make_drl_mask: true
use_drl_mask: true
```




