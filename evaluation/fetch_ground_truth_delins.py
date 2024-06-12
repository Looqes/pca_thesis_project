
import os
import shutil
import sys
import SimpleITK as sitk

"../scripts" not in sys.path and sys.path.insert(0, '../scripts')
import read_scans_utils
import image_scaling




# Checking which set the fetching should be applied to
if len(sys.argv) == 2:
    if sys.argv[1] in {"test", "validation"}:
        path_to_sets = f"./contours_compare_{sys.argv[1]}"
       
        print("Available dataset predictions:")

        for set in os.listdir(path_to_sets):
            print(set)
        dataset_name = input("Which set?: ")

        if dataset_name in os.listdir(path_to_sets):
            path_to_model_output = f"./contours_compare_{sys.argv[1]}/{dataset_name}/model_output"
            if not os.path.exists(path_to_model_output):
                os.makedirs(path_to_model_output)
            if len(os.listdir(path_to_model_output)) == 0:
                print("Please put the model predictions of the validation data in the following folder:")
                print(path_to_model_output)
                exit(1)

            PATH_TO_MODEL_GROUND_TRUTH = f"../data/nnUNet_raw/{dataset_name}/labelsTr"
            PATH_TO_PROSTATE_DELINEATIONS = f"../data/prostate delineations"

            path_to_put_ground_truth = f"./contours_compare_{sys.argv[1]}/{dataset_name}/ground_truth"
            path_to_put_prostate_delineations = f"./contours_compare_{sys.argv[1]}/{dataset_name}/prostate_delineations"

            for output_path in [path_to_put_ground_truth,
                                path_to_put_prostate_delineations]:
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
        else:
            print("Set not found\nAborting...")
            exit(1)

# The fetching
# The ground truth delineations, or labels, from the chosen model will be copied to the specified path to put them
# Also, matching prostate delineations will be copied
        for model_delineation_file in os.listdir(path_to_model_output):
            print(model_delineation_file)

            if ".nii.gz" in model_delineation_file:
                patient_id = model_delineation_file[:10]

                # move region delineation
                for ground_truth_delineation_file in os.listdir(PATH_TO_MODEL_GROUND_TRUTH):
                    if patient_id in ground_truth_delineation_file:
                        # move file from groundtruth delineations & rename to same as model output
                        shutil.copy(f"{PATH_TO_MODEL_GROUND_TRUTH}/{ground_truth_delineation_file}",
                                    f"{path_to_put_ground_truth}/{model_delineation_file}")
                        break
                
                # move prostate delineatoins
                for prostate_delineation_file in os.listdir(PATH_TO_PROSTATE_DELINEATIONS):
                    if patient_id in prostate_delineation_file:
                        shutil.copy(f"{PATH_TO_PROSTATE_DELINEATIONS}/{prostate_delineation_file}",
                                    f"{path_to_put_prostate_delineations}/{prostate_delineation_file}")
                        break
        
        downscale = input("Do you wish to downscale the fetched prostate delineations to match delineated " + \
                          "slices in region delineations? yes/no: ")
        if downscale == "yes":
            image_scaling.downscale_prostate_delineations_to_region_delineations(
                path_to_put_prostate_delineations,
                f"./contours_compare_{sys.argv[1]}/{dataset_name}/downscaled_prostate_delineations"
            )
            
        exit(0)


print("fetch_ground_truth_delins.py [test/validation]")