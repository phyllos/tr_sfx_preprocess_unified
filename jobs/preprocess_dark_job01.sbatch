#!/bin/bash
#SBATCH --job-name=tr_sfx_preprocess_dark_job01
#SBATCH --partition=cxfel
#SBATCH --nodelist=execute-4003
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=160G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

echo "========================================"
echo "Job started at $(date)"
echo "Job ID: ${SLURM_JOB_ID:-NA}"
echo "Running on $(hostname)"
echo "========================================"

CONFIG_PATH="${1:?Usage: sbatch jobs/preprocess.sbatch configs/dark_full.yaml}"
PROJECT_ROOT="$HOME/Data-cxfel/tr_sfx_preprocess_unified"
cd "$PROJECT_ROOT"

source "$HOME/Data-cxfel/conda/etc/profile.d/conda.sh"
conda activate tr_sfx_preprocess


echo "Working directory: $(pwd)"
echo "Conda env: ${CONDA_DEFAULT_ENV:-NA}"
echo "Python: $(which python)"
echo "========================================"
echo

export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export MKL_NUM_THREADS="$SLURM_CPUS_PER_TASK"

python driver.py --config "$CONFIG_PATH"

echo
echo "========================================"
echo "Job finished at $(date)"
echo "========================================"

