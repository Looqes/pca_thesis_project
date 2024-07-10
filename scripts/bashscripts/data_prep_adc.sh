#!/bin/bash
#Set job requirements
#SBATCH -J data_prep_pca_LB
#SBATCH -p gpu
#SBATCH --gpus-per-node=4
#SBATCH -t 10:00:00

#Loading modules
module load 2023

#Copy input data to scratch and create output directory
cp -r $HOME/data/nnUNet_raw "$TMPDIR"
mkdir "$TMPDIR"/output_dir

#Run program
nnUNetv2_plan_and_preprocess -d 002 --verify_dataset_integrity

#Copy output data from scratch to home
cp -r "$TMPDIR"/output_dir $HOME/data/nnUNet_preprocessed