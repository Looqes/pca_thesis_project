
import os
import shutil
import sys

"../scripts" not in sys.path and sys.path.insert(0, '../scripts')
import read_scans_utils





if len(sys.argv) == 2:
    if sys.argv[1] in {"test", "validation"}:
        path_to_sets = f"./contours_compare_{sys.argv[1]}"
       
        print("Available dataset predictions:")

        for set in os.listdir(path_to_sets):
            print(set)
        answer = input("Which set?: ")

        if answer in os.listdir(path_to_sets):
            PATH_TO_RAW_GROUND_TRUTH = f"../data/nnUNet_raw/{answer}/labelsTr"
            PATH_TO_PROSTATE_DELINEATIONS = f"../data/prostate delineations"

            path_to_model_output = f"./contours_compare_{sys.argv[1]}/{answer}/model_output"
            path_to_put_ground_truth = f"./contours_compare_{sys.argv[1]}/{answer}/ground_truth"
        else:
            print("Set not found\nAborting...")
            exit(1)

        for model_delineation_file in os.listdir(path_to_model_output):
            print(model_delineation_file)

            if ".nii.gz" in model_delineation_file:
                patient_id = model_delineation_file[:10]

                for ground_truth_delineation_file in os.listdir(PATH_TO_RAW_GROUND_TRUTH):
                    if patient_id in ground_truth_delineation_file:
                        # move file from groundtruth delineations & rename to same as model output
                        shutil.copy(f"{PATH_TO_RAW_GROUND_TRUTH}/{ground_truth_delineation_file}",
                                    f"{path_to_put_ground_truth}/{model_delineation_file}")
                
                for prostate_delineation_file in os.listdir():
                    if patient_id in prostate_delineation_file:
                        
            
        exit(0)                

print("fetch_ground_truth_delins.py [test/validation]")