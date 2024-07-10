
import os
import shutil
import sys
import SimpleITK as sitk

# "./scripts" not in sys.path and sys.path.insert(0, '../scripts')
import read_scans_utils
import image_scaling


############################################
# Script that fetches ground truth delineations of a folder containing model predicted segmentations
# It is expected that the target folder "../evaluation/contours_compare_{test/validation}" already
# contains the model output files, with the naming of the files corresponding to the naming
# of the ground truth delineations.
# 
############################################

test_or_val = input("Test or validation data? t/v: ")
if test_or_val not in {"t", "v"}:
    print("t/v")
    exit(1)
test_or_val = "validation" if test_or_val == "v" else "test"
datafolder = f"../evaluation/contours_compare_{test_or_val}"

root, dirs, files = next(os.walk(f"{datafolder}"))

print("Which set?")
for i, dir in enumerate(dirs):
    print(f"    {i + 1}: {dir}")
try:
    answer = int(input("")) - 1
except:
    print("Not a number")
    exit(1)
if answer not in range(len(dirs)):
    print(f"No set {answer}")
    exit(1)

dataset = dirs[answer]
model_output_path = f"{datafolder}/{dataset}/model_output"

print(f"Fetching ground truth files for {dataset}...")

if len(os.listdir(model_output_path)) == 0:
    print("No model output delineations found")
    print("Please put the model predictions of the validation data in the following folder:")
    print(model_output_path)
    exit(1)



# The fetching
###########################################################################
# The raw data paths
PATH_TO_MODEL_GROUND_TRUTH = f"../data/nnUNet_raw/{dataset}/labelsTr"
PATH_TO_PROSTATE_DELINEATIONS = f"../data/prostate delineations"

path_to_put_prostate_delineations = f"../evaluation/contours_compare_{test_or_val}/{dataset}/prostate_delineations"
ground_truth_path = f"{datafolder}/{dataset}/ground_truth"

for output_path in [ground_truth_path,
                    path_to_put_prostate_delineations]:
    if not os.path.exists(output_path):
        os.makedirs(output_path)


# The ground truth delineations, or labels, from the chosen model will be copied to the specified path to put them
# Also, matching prostate delineations will be copied
for model_delineation_file in os.listdir(model_output_path):
    print(model_delineation_file)

    if ".nii.gz" in model_delineation_file:
        patient_id = model_delineation_file[:10]

        # move region delineation
        for ground_truth_delineation_file in os.listdir(PATH_TO_MODEL_GROUND_TRUTH):
            if patient_id in ground_truth_delineation_file:
                # move file from groundtruth delineations & rename to same as model output
                shutil.copy(f"{PATH_TO_MODEL_GROUND_TRUTH}/{ground_truth_delineation_file}",
                            f"{ground_truth_path}/{model_delineation_file}")
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
        f"../evaluation/contours_compare_{test_or_val}/{dataset}/downscaled_prostate_delineations"
    )
    

