
import os
import shutil
import sys

"../scripts" not in sys.path and sys.path.insert(0, '../scripts')
import read_scans_utils


PATH_TO_GROUND_TRUTH = "../data/nnUNet_raw/Dataset001_pca/labelsTr"


if len(sys.argv) == 3:
    if sys.argv[1] in {"test", "validation"} and \
       sys.argv[2] in {"t2_adc", "t2_perfusion", "all_modalities"}:
        path_to_model_output = f"./contours_compare_{sys.argv[1]}/{sys.argv[2]}/model_output"
        path_to_output = f"./contours_compare_{sys.argv[1]}/{sys.argv[2]}/ground_truth"
    
        for model_delineation_file in os.listdir(path_to_model_output):
            print(model_delineation_file)
            patient_id = model_delineation_file[:10]

            for ground_truth_delineation_file in os.listdir(PATH_TO_GROUND_TRUTH):
                if patient_id in ground_truth_delineation_file:
                    # move file from groundtruth delineations & rename to same as model output
                    shutil.copy(f"{PATH_TO_GROUND_TRUTH}/{ground_truth_delineation_file}",
                                f"{path_to_output}/{model_delineation_file}")
        
        exit(0)                

print("fetch_ground_truth_delins.py [test/validation] [t2_adc/t2_perfusion/all_modalities]")
exit(1)