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
mkdir "$TMPDIR"/output_dir_pred_006

#Run program
nnUNetv2_predict -i "$TMPDIR"/data/nnUNet_raw/Dataset006_pca_gg3gg4combined/imagesTs -o "$TMPDIR"/output_dir_pred_006 -d Dataset006_pca_gg3gg4combined -c 3d_fullres -f 0 -chk checkpoint_best.pth --verbose

#Copy output data f
cp -r "$TMPDIR"/output_dir_pred_006 $HOME/data/predictions