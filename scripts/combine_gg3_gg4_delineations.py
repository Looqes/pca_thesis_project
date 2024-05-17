
import os
import SimpleITK as sitk
import numpy as np




PATH_TO_NII_DELINEATIONS = "../data/Regions ground truth/delineations_nifti"
PATH_TO_MODIFIED_DELINEATIONS = "../data/Regions ground truth/gg3gg4_combined_delineations"



for nii_delineation_file in os.listdir(PATH_TO_NII_DELINEATIONS):
    patient_id = nii_delineation_file[:10]
    print("Reprocessing", nii_delineation_file, "...")

    delineation = sitk.ReadImage(f"{PATH_TO_NII_DELINEATIONS}/{nii_delineation_file}")
    data_array = sitk.GetArrayFromImage(delineation)
    
    data_array[data_array == 2] = 1
    data_array[data_array == 3] = 2

    new_image = sitk.GetImageFromArray(data_array)
    new_image.SetDirection(delineation.GetDirection())
    new_image.SetOrigin(delineation.GetOrigin())
    new_image.SetSpacing(delineation.GetSpacing())

    sitk.WriteImage(new_image,
                    f"{PATH_TO_MODIFIED_DELINEATIONS}/{patient_id}_gg3gg4combined.nii.gz")