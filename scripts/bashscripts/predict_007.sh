#!/bin/bash
#Set job requirements
#SBATCH -J predict_pca_006_LB
#SBATCH -p gpu
#SBATCH --gpus-per-node=4
#SBATCH -t 20:00:00


#Loading modules
module load 2023

#Copy input data to scratch and create output directory
cp -r $HOME/data "$TMPDIR"
mkdir "$TMPDIR"/output_dir_pred_007

#Run program
nnUNetv2_predict -i "$TMPDIR"/data/nnUNet_raw/Dataset007_pca_cribriform_only/imagesTs -o "$TMPDIR"/output_dir_pred_007 -d Dataset007_pca_cribriform_only -c 3d_fullres -f 0 -chk checkpoint_best.pth --verbose

#Copy output data f
cp -r "$TMPDIR"/output_dir_pred_007 $HOME/data/predictions