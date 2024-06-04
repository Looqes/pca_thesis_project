import SimpleITK as sitk
import nibabel as nb
import nilearn.image as ni_im


import numpy as np
import pickle as pkl
import os
import sys
"../scripts" not in sys.path and sys.path.insert(0, '../scripts')

import read_scans_utils
from patient import Patient


PATH_TO_PKLS = "../data/pkl_preprocessed"
PATH_TO_NII_DELINEATIONS = "../data/Regions ground truth/delineations_nifti"


# Take errormap of patient, and rescale it to the size of patient's original t2
def upscale_errormap(patient_id, errormap, output_path):
    output_path = f"./contours_compare_validation/Dataset005_pca/upscaled_errormaps"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # full_patient = Patient.load_patient_from_pkl(patient_id)
    full_delineation = sitk.ReadImage(f"{PATH_TO_NII_DELINEATIONS}/{patient_id}_combined_delineation.nii.gz")
    full_delineation_array = sitk.GetArrayFromImage(full_delineation)

    # Gather which slices are delineated (have lesions)
    delineation_slices = []
    for i, slice in enumerate(np.rollaxis(full_delineation_array, axis = 0)):
        if len(np.unique(slice)) > 1:
            delineation_slices.append(i)

    # Overwrite the delineation slices in the original delineation with the error map slices
    output = np.ones_like(full_delineation_array)
    output[delineation_slices, :, :] = errormap

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
                    f"{output_path}/{patient_id}_errormap.nii.gz")
       

    




if len(sys.argv) == 2:
    if sys.argv[1] in {"test", "validation"}:
        path_to_sets = f"./contours_compare_{sys.argv[1]}"
       
        print("Available dataset predictions:")

        for dataset in os.listdir(path_to_sets):
            print(dataset)
        answer = input("Which set?: ")

        if answer in os.listdir(path_to_sets):
            path_to_model_output = f"./contours_compare_{sys.argv[1]}/{answer}/model_output"
            path_to_put_ground_truth = f"./contours_compare_{sys.argv[1]}/{answer}/ground_truth"

            path_to_errormaps_folder = f"./contours_compare_{sys.argv[1]}/{answer}/error_maps"
            if not os.path.exists(path_to_errormaps_folder):
                os.makedirs(path_to_errormaps_folder)
            path_to_upscaled_errormaps_folder = f"./contours_compare_{sys.argv[1]}/{answer}/upscaled_errormaps"
            if not os.path.exists(path_to_upscaled_errormaps_folder):
                os.makedirs(path_to_upscaled_errormaps_folder)
        else:
            print("Set not found\nAborting...")
            exit(1)

        all_ids = list(set(os.listdir(path_to_model_output)) | set(os.listdir(path_to_put_ground_truth)))
        if len(os.listdir(path_to_model_output)) != len(all_ids) or \
        len(os.listdir(path_to_put_ground_truth)) != len(all_ids):
            print("Files in ground truth and model predictions do not match in filenames")

        for file in all_ids:
            print(file)
            model_output = sitk.ReadImage(f"{path_to_model_output}/{file}")
            ground_truth = sitk.ReadImage(f"{path_to_put_ground_truth}/{file}")

            gt = sitk.GetArrayFromImage(ground_truth)
            mp = sitk.GetArrayFromImage(model_output)

            error_map = np.zeros_like(gt)
                     
            error_map = np.where((gt == 0) & (mp == 0), 1,
                        np.where((gt == 0) & (mp == 1), 2,
                        np.where((gt == 0) & (mp == 2), 3,
                        np.where((gt == 0) & (mp == 3), 4,
                        np.where((gt == 1) & (mp == 0), 5,
                        np.where((gt == 1) & (mp == 1), 6,
                        np.where((gt == 1) & (mp == 2), 7,
                        np.where((gt == 1) & (mp == 3), 8,
                        np.where((gt == 2) & (mp == 0), 9,
                        np.where((gt == 2) & (mp == 1), 10,
                        np.where((gt == 2) & (mp == 2), 11,
                        np.where((gt == 2) & (mp == 3), 12,
                        np.where((gt == 3) & (mp == 0), 13,
                        np.where((gt == 3) & (mp == 1), 14,
                        np.where((gt == 3) & (mp == 2), 15,
                        np.where((gt == 3) & (mp == 3), 16, 0))))))))))))))))
            
            print(np.unique(error_map, return_counts=True))
            
            error_map_image = sitk.GetImageFromArray(error_map)
            error_map_image.SetDirection(model_output.GetDirection())
            error_map_image.SetOrigin(model_output.GetOrigin())
            error_map_image.SetSpacing(model_output.GetSpacing())

            sitk.WriteImage(error_map_image,
                            f"{path_to_errormaps_folder}/{file}")
            
            upscale_errormap(file[:10], error_map, path_to_upscaled_errormaps_folder)
            
            print("----------\n")


else:
    print("arg test/validation missing")


    