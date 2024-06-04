import os
import read_scans_utils
import SimpleITK as sitk
import numpy as np
import nilearn.image as ni_im
import nibabel as nb
from nibabel.processing import conform



SCANS_PATH = "../data/Scans/all_scans"
DELINEATIONS_PATH = "../data/Regions ground truth/Regions delineations/"
NIFTI_DELINEATIONS_PATH = "../data/Regions ground truth/delineations_nifti"


# Upscale given delineation to resolution of patients' original delineation
# This function assumes that the given small delineation spans the same amount of
# slices, and is in the same location of the delineation slices as the original delineation
# meaning if the small delineation is 3 slices, it will be assumed that the original delineation
# also has 3 delineated slices which will then be replaced with the small delineation
def upscale_delineation(patient_id, 
                        delineation_to_upscale, 
                        output_path):
    if not os.path.exists(output_path):
        print(f"Creating {output_path}")
        os.makedirs(output_path)

    # full_patient = Patient.load_patient_from_pkl(patient_id)
    full_delineation = sitk.ReadImage(f"{NIFTI_DELINEATIONS_PATH}/{patient_id}_combined_delineation.nii.gz")
    full_delineation_array = sitk.GetArrayFromImage(full_delineation)

    delineation_slices = read_scans_utils.get_delineated_slice_indexes_from_delineation(full_delineation)

    # Overwrite the delineation slices in the original delineation with the smaller delineation
    output = np.ones_like(full_delineation_array)
    output[delineation_slices, :, :] = delineation_to_upscale

    output_img = sitk.GetImageFromArray(output)

    output_img.SetDirection(full_delineation.GetDirection())
    output_img.SetOrigin(full_delineation.GetOrigin())
    output_img.SetSpacing(full_delineation.GetSpacing())

    slices_with_errormap = []
    for i, slice in enumerate(np.rollaxis(output, axis = 0)):
        if len(np.unique(slice)) > 1:
            slices_with_errormap.append(i)
    
    print(f"Slices with an errormap for patient {patient_id}: {slices_with_errormap}")

    sitk.WriteImage(output_img,
                    f"{output_path}/{patient_id}_upscaled.nii.gz")
    

# HELPER FUNCTION (see below)
def downscale_prostate_delineation_to_region_delineation(prostate_delineation,
                                                         patient_id):
    region_delineation = sitk.ReadImage(f"{NIFTI_DELINEATIONS_PATH}/{patient_id}_combined_delineation.nii.gz")
    delineated_slices = read_scans_utils.get_delineated_slice_indexes_from_delineation(region_delineation)

    # Resample prostate image to match resolution for region delineations before trimming it of slices
    prostate_delineation = sitk.Resample(prostate_delineation, region_delineation, sitk.Transform(), sitk.sitkNearestNeighbor, 0.0, sitk.sitkUInt8)
    sitk.WriteImage(prostate_delineation, "../evaluation/test_prostatedelineation029resampled.nii.gz")
    prostate_delineation_array = sitk.GetArrayFromImage(prostate_delineation)

    downscaled_prostate_delineation_array = prostate_delineation_array[delineated_slices, :, :]

    downscaled_prostate_delineation = sitk.GetImageFromArray(downscaled_prostate_delineation_array)
    downscaled_prostate_delineation.SetDirection(
        region_delineation.GetDirection()
        )
    downscaled_prostate_delineation.SetOrigin(
        region_delineation.GetOrigin()
        )
    downscaled_prostate_delineation.SetSpacing(
        region_delineation.GetSpacing()
        )
    
    return downscaled_prostate_delineation
    
# Downscale a prostate delineation to match a delineation file for same patient
# Slices in the prostate delineation that do not contain delineations in their respective
# region delineation are removed
def downscale_prostate_delineations_to_region_delineations(folder_path,
                                                           output_path):
    if not os.path.exists(folder_path):
        print(f"{folder_path} does not exist. No delineations to resample. Aborting...")
        return
    if not os.path.exists(output_path):
        print(f"{output_path} does not exist. Creating...")
        os.makedirs(output_path)

    for prostate_delineation_file in os.listdir(folder_path):
        patient_id = prostate_delineation_file[:10]

        prostate_delineation = sitk.ReadImage(f"{folder_path}/{prostate_delineation_file}")

        downscaled_prostate_delineation = downscale_prostate_delineation_to_region_delineation(prostate_delineation,
                                                                                               patient_id)
        
        sitk.WriteImage(downscaled_prostate_delineation,
                        f"{output_path}/{patient_id}.nii.gz")
        

# Resample all delineations in folder to match the resolution of a reference delineation, which is the first
# file found in the folder
def resample_delineations_to_same_resolution(folder_path,
                                             output_path):
    if not os.path.exists(folder_path):
        print(f"{folder_path} does not exist. No delineations to resample. Aborting...")
        return
    if not os.path.exists(output_path):
        print(f"{output_path} does not exist. Creating...")
        os.makedirs(output_path)

    delineation_files = os.listdir(folder_path)
    reference_delineation = sitk.ReadImage(f"{folder_path}/{delineation_files[0]}")

    for other_delineation_file in delineation_files[1:]:
        patient_id = other_delineation_file[:10]

        other_delineation = sitk.ReadImage(f"{folder_path}/{other_delineation_file}")

        other_delineation.SetDirection(reference_delineation.GetDirection())
        other_delineation.SetOrigin(reference_delineation.GetOrigin())
        other_delineation.SetSpacing(reference_delineation.GetSpacing())

        resampled_delineation = sitk.Resample(other_delineation, reference_delineation, sitk.Transform(), sitk.sitkNearestNeighbor, 0.0, sitk.sitkUInt8)

        sitk.WriteImage(resampled_delineation,
                        f"{output_path}/{patient_id}.nii.gz")
        
        break
