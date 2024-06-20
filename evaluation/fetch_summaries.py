import sys
import os
import shutil



path_to_validation_evaluation = "./contours_compare_validation"
path_to_test_evaluation = "./contours_compare_test"

path_to_models = "../nnUNet_results/models"


for model in os.listdir(path_to_models):
    path_to_model_validation_results_summary = \
        f"{path_to_models}/{model}/nnUNetTrainer__nnUNetPlans__3d_fullres/fold_0/validation/summary.json"
    
    if os.path.exists(f"{path_to_validation_evaluation}/{model}"):
        print(f"Moving summary of {model} to evaluation folder")
        shutil.copy(path_to_model_validation_results_summary,
                    f"{path_to_validation_evaluation}/{model}")
    else:
        print(f"{model} evaluation folder not found")

    
