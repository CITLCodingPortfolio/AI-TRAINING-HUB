#!/bin/bash
#SBATCH --job-name={{PROJECT_NAME}}
#SBATCH --output=slurm_out_%j.txt
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
echo "Running {{PROJECT_NAME}} batch demo"
python -c "print('Hello from SLURM template')"
