
import read_scans_utils
from sklearn.model_selection import train_test_split
from collections import Counter
import os
import json

# Hyperparameter to decide threshold of what is considered a large and small lesion
# top K largest and smallest lesions for each pattern are considered large and small
# respectively
K = 10

def create_train_val_test_split(dataset_nr,
                                save_train_validation_json=False):
    # Underrepresented characterstics will be split evenly across splits
    # They consist of:
    #   - Lesion size (small & large lesions)
    #   - Presence of cribriform pattern
    try:
        dataset_path = f"../data/nnUNet_raw/" + \
                        [f for f in os.listdir("../data/nnUNet_raw")
                         if str(dataset_nr).zfill(3) in f][0]
    except:
        print(f"Problem trying to find set {dataset_nr}, aborting...")
        return
    
    test_data_path = f"{dataset_path}/imagesTs"
    train_data_path = f"{dataset_path}/imagesTr"

    # Check if folder with test split already exists
    if not os.path.exists(test_data_path):
        os.makedirs(test_data_path)
        print(f"Folder {test_data_path} created successfully.")
    else:
        print("There is already a split present. Aborting...")
        return

    # Read the dictionaries containing region-grouped voxel count per Gleason pattern
    if os.path.exists("../data/patient_metadata"):
        voxel_dists, _, _ = read_scans_utils.collect_patient_metadata(read_from_files=True)
    else:
        print("Patient metadata files not found... \
               metadata is created after pkls are constructed by load_patients.py")
        return

    all_patients_ids = sorted(list(set([patient_file[:10]
                        for patient_file in os.listdir(f"{dataset_path}/imagesTr")])),
                        key = lambda x: int(x[-3:]))

    cribriform_patients = set()
    # Add empty voxel counts for sorting
    for patient_id, dct in voxel_dists["full_image"]:
        if 1 not in dct:
            dct[1] = 0
        if 2 not in dct:
            dct[2] = 0
        if 3 not in dct:
            dct[3] = 0
        else:
            cribriform_patients.add(patient_id)

    sorted_by_crib_lesion_size = [patient[0] for patient in sorted([dist for dist in voxel_dists["full_image"] if dist[1][3] != 0], key = lambda x: x[1][3])]
    large_crib_lesions = set(sorted_by_crib_lesion_size[-K:])
    small_crib_lesions = set(sorted_by_crib_lesion_size[:K])

    sorted_by_GG4_lesion_size = [patient[0] for patient in sorted([dist for dist in voxel_dists["full_image"] if dist[1][2] != 0], key = lambda x: x[1][2])]
    large_gg4_lesions = set(sorted_by_GG4_lesion_size[-K:])
    small_gg4_lesions = set(sorted_by_GG4_lesion_size[:K])

    sorted_by_GG3_lesion_size = [patient[0] for patient in sorted([dist for dist in voxel_dists["full_image"] if dist[1][1] != 0], key = lambda x: x[1][1])]
    large_gg3_lesions = set(sorted_by_GG3_lesion_size[-K:])
    small_gg3_lesions = set(sorted_by_GG3_lesion_size[:K])

    # patient class:
    #   Cribriform & large lesion   7
    #   Cribriform & small lesion   6
    #   GG4 & large                 5
    #   GG4 & small                 4
    #   GG3 & large                 3
    #   GG3 & small                 2
    #   Crib                        1
    #   anything else               0
    # These will be the sets on which the split will be performed, patient_id and its class number in x and y respectively
    X = []
    Y = []
    for patient_id, dct in voxel_dists["full_image"]:
        if patient_id not in all_patients_ids:
            continue
        class_nr = 7 if patient_id in large_crib_lesions \
            else 6 if patient_id in small_crib_lesions \
            else 5 if patient_id in large_gg4_lesions \
            else 4 if patient_id in small_gg4_lesions \
            else 3 if patient_id in large_gg3_lesions \
            else 2 if patient_id in small_gg3_lesions \
            else 1 if patient_id in cribriform_patients \
            else 0
        
        X.append(patient_id)
        Y.append(class_nr)

    X_train_val, X_test, Y_train_val, Y_test = train_test_split(X, Y,
                                                            stratify = Y,
                                                            test_size = 0.20)

    X_train, X_val, Y_train, Y_val = train_test_split(X_train_val, Y_train_val,
                                                    stratify = Y_train_val,
                                                    test_size = 0.25)

    splits_final = [{
        "train" : X_train,
        "val"   : X_val,
    }]

    # Extracting modalities...
    modalities = list(set([case[11:15] for case in os.listdir(train_data_path)]))
    
    organize_dataset_by_split(train_data_path,
                              test_data_path,
                              modalities,
                              X_test)
    print("Amount of train/validation patients: ", len(X_train_val))
    print("Amount of test patients: ", len(X_test))
    print("test patients/trainval patients ratio: ", len(X_test)/len(X_train_val))

    if save_train_validation_json == True:
        with open(f"{dataset_path}/splits_final.json", 'w', encoding='utf-8') as f:
            json.dump(splits_final, f, ensure_ascii=False, indent=4)

    # Create dataset.json; it is reliant on the amount of training cases
    read_scans_utils.create_datasetjson(dataset_path,
                                        ["AxialT2", "ADC", "Perfusion"])


def organize_dataset_by_split(train_data_path,
                              test_data_path,
                              modalities,
                              test_set_ids):
    
    # Move the files from the test set ids to the test set folder, 
    # taking into account each modality for an id
    for test_set_id in test_set_ids:
        for modality in modalities:
            os.rename(f"{train_data_path}/{test_set_id}_{modality}.nii.gz", 
                      f"{test_data_path}/{test_set_id}_{modality}.nii.gz")

    
