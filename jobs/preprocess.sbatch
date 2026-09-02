#!/bin/bash
#SBATCH --job-name=tr_sfx_preprocess
#SBATCH --partition=cxfel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=160G
#SBATCH --nodelist=execute-4005
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
CONFIG_PATH="${1:?Usage: sbatch jobs/preprocess.sbatch configs/dark_full.yaml}"
PROJECT_ROOT="${PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
cd "$PROJECT_ROOT"

source "$HOME/Data-cxfel/conda/etc/profile.d/conda.sh"
conda activate tr_sfx_preprocess

export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export MKL_NUM_THREADS="$SLURM_CPUS_PER_TASK"

python driver.py --config "$CONFIG_PATH"
