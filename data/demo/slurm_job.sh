#!/bin/bash
#SBATCH --job-name=demo_train
#SBATCH --time=00:10:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=8G
module load cuda/12.2
python train.py --epochs 1 --batch-size 16