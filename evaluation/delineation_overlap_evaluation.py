import SimpleITK as sitk
import numpy as np
import os
import sys
"../scripts" not in sys.path and sys.path.insert(0, '../scripts')

import read_scans_utils


test_or_val = input("Test or validation data? t/v: ")
if test_or_val not in {"t", "v"}:
    print("t/v")
    exit(1)
test_or_val = "validation" if test_or_val == "v" else "test"
datafolder = f"./contours_compare_{test_or_val}"

root, dirs, files = next(os.walk("./"))

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

print(f"Checking set {dataset}")

print(os.listdir(f"./{dataset}"))

ground_truth_path = f"./contours_compare_{test_or_val}/{dataset}/ground_truth"
model_output_path = f"./contours_compare_{test_or_val}/{dataset}/model_output"

all_ids = set(os.listdir(ground_truth_path)) | set(os.listdir(model_output_path))
if len(os.listdir(ground_truth_path)) != len(all_ids) or \
   len(os.listdir(model_output_path)) != len(all_ids):
    print("Files in ground truth and model predictions do not match in filenames")


for id in all_ids:
    print(id)
    print("----------")
    ground_truth = sitk.ReadImage(f"{ground_truth_path}/{id}")
    model_output = sitk.ReadImage(f"{model_output_path}/{id}")

    gt_array = sitk.GetArrayFromImage(ground_truth)
    mo_array = sitk.GetArrayFromImage(model_output)

    gt_flat_map = np.zeros_like(gt_array)
    gt_flat_map[gt_array != 0] = 1
    mo_flat_map = np.zeros_like(mo_array)
    mo_flat_map[mo_array != 0] = 1

    