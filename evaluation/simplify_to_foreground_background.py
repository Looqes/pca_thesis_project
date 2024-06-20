import SimpleITK as sitk
from sklearn.metrics import confusion_matrix, cohen_kappa_score
from sklearn.preprocessing import normalize
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


import os
import sys
"../scripts" not in sys.path and sys.path.insert(0, '../scripts')

import read_scans_utils

# This script takes the delineations of the model_output folder & ground_truth folder
# & simplifies them by changing all nonzero labels to 1, to create a foreground/background
# comparison.
##########################################################


test_or_val = input("Test or validation data? t/v: ")
if test_or_val not in {"t", "v"}:
    print("t/v")
    exit(1)
test_or_val = "validation" if test_or_val == "v" else "test"
datafolder = f"./contours_compare_{test_or_val}"

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

print(f"Simplifying set {dataset}")



ground_truth_path = f"{datafolder}/{dataset}/ground_truth"
model_output_path = f"{datafolder}/{dataset}/model_output"

new_folder_path = f"{datafolder}/{dataset}_simplified"
new_ground_truth_path = f"{new_folder_path}/ground_truth"
new_model_output_path = f"{new_folder_path}/model_output"

for new_folder in [new_ground_truth_path,
                   new_model_output_path]:
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)

for delineation_file_name in os.listdir(ground_truth_path):
    ground_truth_delineation = sitk.ReadImage(f"{ground_truth_path}/{delineation_file_name}")
    model_output_delineation = sitk.ReadImage(f"{model_output_path}/{delineation_file_name}")

    ground_truth_delineation_array = sitk.GetArrayFromImage(ground_truth_delineation)
    model_output_delineation_array = sitk.GetArrayFromImage(model_output_delineation)

    ground_truth_delineation_array[ground_truth_delineation_array != 0] = 1
    model_output_delineation_array[model_output_delineation_array != 0] = 1

    simplified_ground_truth_delineation = sitk.GetImageFromArray(ground_truth_delineation_array)
    simplified_model_output_delineation = sitk.GetImageFromArray(model_output_delineation_array)


    simplified_ground_truth_delineation.SetDirection(ground_truth_delineation.GetDirection())
    simplified_model_output_delineation.SetDirection(model_output_delineation.GetDirection())

    simplified_ground_truth_delineation.SetOrigin(ground_truth_delineation.GetOrigin())
    simplified_model_output_delineation.SetOrigin(model_output_delineation.GetOrigin())

    simplified_ground_truth_delineation.SetSpacing(ground_truth_delineation.GetSpacing())
    simplified_model_output_delineation.SetSpacing(model_output_delineation.GetSpacing())

    sitk.WriteImage(simplified_ground_truth_delineation,
                    f"{new_ground_truth_path}/{delineation_file_name}")
    sitk.WriteImage(simplified_model_output_delineation,
                    f"{new_model_output_path}/{delineation_file_name}")