#!/bin/bash
#Set job requirements
#SBATCH -p gpu
#SBATCH --gpus-per-node=4
#SBATCH -t 80:00:00

#Loading modules
module load 2022

#Copy input data to scratch and create output directory
cp -r $HOME/data "$TMPDIR"
mkdir "$TMPDIR"/out_dir_485

#Run program

nnUNetv2_predict -i "$TMPDIR"/data/nnUnet_raw/Dataset485_priorrectumGTV/imagesTs/ -o "$TMPDIR"/out_dir_485 -d Dataset485_priorrectumGTV -f 0 -c 3d_fullres -chk checkpoint_best.pth  



#Copy output data from scratch to home
cp -r "$TMPDIR"/out_dir_485 $HOME