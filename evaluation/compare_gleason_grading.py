import SimpleITK as sitk
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


# Statistics to collect 
correct_gradings = 0
correct_cribriform_predictions = {
    "absence": 0,
    "presence": 0
}
underestimations = 0
overestimations = 0
total_cases = len(all_ids)



# The actual comparing
for id in all_ids:
    print(id)
    print("----------")
    ground_truth = sitk.ReadImage(f"{ground_truth_path}/{id}")
    model_output = sitk.ReadImage(f"{model_output_path}/{id}")

    ground_truth_gleason_group, ground_truth_has_cribriform = read_scans_utils.determine_gleason_grade(ground_truth)
    model_output_gleason_group, model_output_has_cribriform = read_scans_utils.determine_gleason_grade(model_output)

    print("Ground truth gleason grade group: ", ground_truth_gleason_group)
    print("Model output gleason grade group: ", model_output_gleason_group)
    print()

    if model_output_gleason_group == 0:
        underestimations += 1

    if ground_truth_gleason_group == model_output_gleason_group and \
       ground_truth_has_cribriform == model_output_has_cribriform:
        correct_gradings += 1
    if model_output_gleason_group > ground_truth_gleason_group:
        overestimations += 1
    elif model_output_gleason_group < ground_truth_gleason_group:
        underestimations += 1


    if ground_truth_has_cribriform == False and \
       model_output_has_cribriform == False:
        correct_cribriform_predictions["absence"] += 1
    elif ground_truth_has_cribriform == True and \
         model_output_has_cribriform == True:
        correct_cribriform_predictions["presence"] += 1
    

print("\n\nSTATISTICS:")
print("############################################")
print("Total amount of compared cases: " + str(total_cases))
print("Correct gradings:    " + str(correct_gradings))
print("Underestimations:    " + str(underestimations))
print("Overestimations :    " + str(overestimations))
print("Correct cribriform predictions: ")
print("    absence:  ", correct_cribriform_predictions["absence"])
print("    presence: ", correct_cribriform_predictions["presence"])
    
    
