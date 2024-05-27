
import os
import SimpleITK as sitk
import numpy as np
import shutil

PATH_TO_NNUNET_RAW = "../data/nnUNet_raw"



datasets = os.listdir(PATH_TO_NNUNET_RAW)
print(datasets)
full_datasetname = input("Name of dataset folder to use as reference: ")
if full_datasetname not in datasets:
    print("dataset not found")
    exit(1)


max_dataset_num = max([int(f[7:10]) for f in os.listdir(PATH_TO_NNUNET_RAW)])

# The number ids of the two new datasets that will be created
new_dataset_num = str(max_dataset_num + 1).zfill(3)

new_dataset_path = f"{PATH_TO_NNUNET_RAW}/Dataset{new_dataset_num}_pca_gg3gg4combined"

shutil.copytree(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}",
                new_dataset_path)

path_to_new_set_delineations = f"{new_dataset_path}/labelsTr"

print(f"Combining gleason labels in {path_to_new_set_delineations}...\n")
for nii_delineation_file in os.listdir(path_to_new_set_delineations):
    patient_id = nii_delineation_file[:10]
    print("Reprocessing", nii_delineation_file, "...")

    delineation = sitk.ReadImage(f"{path_to_new_set_delineations}/{nii_delineation_file}")
    data_array = sitk.GetArrayFromImage(delineation)
    
    data_array[data_array == 2] = 1
    data_array[data_array == 3] = 2

    new_image = sitk.GetImageFromArray(data_array)
    new_image.SetDirection(delineation.GetDirection())
    new_image.SetOrigin(delineation.GetOrigin())
    new_image.SetSpacing(delineation.GetSpacing())

    sitk.WriteImage(new_image,
                    f"{path_to_new_set_delineations}/{patient_id}.nii.gz")