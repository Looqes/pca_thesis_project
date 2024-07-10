#!/bin/bash
#Set job requirements
#SBATCH -J train_pca_adc_LB
#SBATCH -p gpu
#SBATCH --gpus-per-node=4
#SBATCH -t 60:00:00


#Loading modules
module load 2022

#Copy input data to scratch and create output directory
cp -r $HOME/data/nnUNet_preprocessed "$TMPDIR"
mkdir "$TMPDIR"/output_dir

#Run program
nnUNetv2_train Dataset002_pcaadc 3d_fullres 0 

#Copy output data f
cp -r "$TMPDIR"/output_dir $HOME/data/nnUNet_results