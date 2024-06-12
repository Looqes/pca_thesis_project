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


# Function to row-wise normalize a confusion matrix and return a set of labels suitable for plotting
# The labels, for each cell (equal shape to input cm), are the normalized value and the original (integer) count
def normalize_and_create_annotations(cm):
    normalized_cm = normalize(cm, axis = 1, norm = 'l1').round(3)

    labels = np.empty(cm.shape, dtype = object)

    for i, row in enumerate(cm):
        for j, col in enumerate(cm):
            labels[i, j] = f"{normalized_cm[i][j]}\n ({int(cm[i][j])})"

    return normalized_cm, labels



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

print(f"Checking set {dataset}")



ground_truth_path = f"{datafolder}/{dataset}/ground_truth"
model_output_path = f"{datafolder}/{dataset}/model_output"

# Check if format of ground truth folder & model output folder is consistent
# Both must contain the same amount of files with the same names
# MARPROC[number].nii.gz
all_ids = set(os.listdir(ground_truth_path)) | set(os.listdir(model_output_path))
if len(os.listdir(ground_truth_path)) != len(all_ids) or \
   len(os.listdir(model_output_path)) != len(all_ids):
    print("Files in ground truth and model predictions do not match in filenames")


# Statistics to collect 
correct_gradings = 0
cribriform_predictions = {
    "True Positive": 0,
    "False Positive": 0,
    "True Negative": 0,
    "False Negative": 0
}
underestimations = 0
overestimations = 0
total_cases = len(all_ids)

# For Confusion matrix
gt_gleason_groups = []
mp_gleason_groups = []

gt_cribriform_predictions = []
mp_cribriform_predictions = []


# The actual comparing
for id in all_ids:
    print(id)
    print("----------")
    ground_truth = sitk.ReadImage(f"{ground_truth_path}/{id}")
    model_output = sitk.ReadImage(f"{model_output_path}/{id}")

    ground_truth_gleason_group, ground_truth_has_cribriform = read_scans_utils.determine_gleason_grade(ground_truth)
    model_output_gleason_group, model_output_has_cribriform = read_scans_utils.determine_gleason_grade(model_output)

    gt_gleason_groups.append(ground_truth_gleason_group)
    mp_gleason_groups.append(model_output_gleason_group)
    gt_cribriform_predictions.append(ground_truth_has_cribriform)
    mp_cribriform_predictions.append(model_output_has_cribriform)

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

    cribriform_prediction = "True Positive"  if ground_truth_has_cribriform == True  and model_output_has_cribriform == True  \
                       else "False Positive" if ground_truth_has_cribriform == False and model_output_has_cribriform == True  \
                       else "True Negative"  if ground_truth_has_cribriform == False and model_output_has_cribriform == False \
                       else "False Negative"
    cribriform_predictions[cribriform_prediction] += 1

print("The predicted classes:")
print("Ground truth/actual values: ")
print(gt_gleason_groups)
print()
print("Predicted values:")
print(mp_gleason_groups)
print()

print("Counts: ")
print(np.unique(gt_gleason_groups, return_counts=True))
print(np.unique(mp_gleason_groups, return_counts=True))
print()

print("Cohen kappa score: ")
print(cohen_kappa_score(gt_gleason_groups, mp_gleason_groups))
print()
    

print("\n\nSTATISTICS:")
print("############################################")
print("Total amount of compared cases: " + str(total_cases))
print("Correct gradings:    " + str(correct_gradings))
print("Underestimations:    " + str(underestimations))
print("Overestimations :    " + str(overestimations))
print("cribriform predictions: ")
[print(f"{outcome} {cribriform_predictions[outcome]}") for outcome in cribriform_predictions.keys()]
    

cm_gleason_groups = confusion_matrix(gt_gleason_groups,
                                     mp_gleason_groups,
                                     )

cm_cribriform = confusion_matrix(gt_cribriform_predictions,
                                 mp_cribriform_predictions)

print(cm_cribriform)


# sns.heatmap(cm_gleason_groups,
#             xticklabels = [0, 1, 2, 3, 4],
#             yticklabels = [0, 1, 2, 3, 4],
#             # annot = annotations,
#             linewidths = 1,
#             linecolor = "black",
#             annot = True,
#             # fmt = '',
#             cbar = False,
#             square = True,
#             cmap = "bone_r")

# plt.xlabel("Predicted Gleason Grade group")
# plt.ylabel("True Gleason Grade group")
# plt.title(f"{dataset} predicted Gleason Grade group vs ground truth")

# plt.savefig(f"{datafolder}/{dataset}/gleason_grade_group_predictions_cm_{dataset}.pdf")



# sns.heatmap(cm_cribriform,
#             xticklabels = ["False", "True"],
#             yticklabels = ["False", "True"],
#             annot = cm_cribriform,
#             linewidths = 1,
#             linecolor = "black",
#             # annot = True,
#             # fmt = '',
#             cbar = False,
#             square = True,
#             cmap = "bone_r")

# plt.xlabel("Predicted presence of cribriform")
# plt.ylabel("True presence of cribriform")
# plt.title(f"{dataset} predicted presence of cribriform vs ground truth")

# plt.savefig(f"{datafolder}/{dataset}/cribriform_presence_predictions_cm_{dataset}.pdf")