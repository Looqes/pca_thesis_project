#!/bin/bash
#Set job requirements
#SBATCH -J predict_pca_002_LB
#SBATCH -p gpu
#SBATCH --gpus-per-node=4
#SBATCH -t 20:00:00


#Loading modules
module load 2022

#Copy input data to scratch and create output directory
cp -r $HOME/data "$TMPDIR"
mkdir "$TMPDIR"/output_dir_pred_002

#Run program
nnUNetv2_predict -i "$TMPDIR"/data/nnUNet_raw/Dataset002_pcaadc/imagesTs -o "$TMPDIR"/output_dir_pred_002 -d Dataset002_pcaadc -c 3d_fullres -f 0 -chk checkpoint_best.pth --verbose

#Copy output data f
cp -r "$TMPDIR"/output_dir_pred_002 $HOME/data/predictions