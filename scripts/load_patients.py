import sys
import os

# Custom objects included in scripts
# from scripts.patient import Patient
# from scripts import read_scans_utils
import read_scans_utils
import data_split
# import patient
from patient import Patient

# Controls if pkls that are already present will be newly made and overwritten
DONT_OVERWRITE_PICKLES = True

# If read raw and save is selected on running the program the raw scan data will be read
# and patient objects will be created
# MRI's and delineations will be loaded and combined,
# ADC and perfusion scans will be saved,
# and relevant slices will be extracted and save per patient
# These objects will be saved to pickle format files for faster reading later
if len(sys.argv) == 2:
    if sys.argv[1] in {"-rras", "read_raw_and_save"}:
    # #################################################################################
        print("Raw data will be read, processed and saved into pkls...")

        current_patient_pkls = set()
        if DONT_OVERWRITE_PICKLES:
            print("Skipping patients that already have pkl's...")
            current_patient_pkls = set([patient_pickle.replace(".pkl", "")
                                    for patient_pickle in os.listdir("../data/pkl_preprocessed")])
            

        preprocessed_patient_generator = read_scans_utils.read_preprocess_patients(
            scans_data_path="../data/Scans/all_scans",
            seriesnumber_info_path="../data/Scans/T2w_seriesnumber_info_Lucas.xlsx",
            patients_to_skip = current_patient_pkls
        )

        if not os.path.exists("../data/pkl_preprocessed"):
            os.makedirs("../data/pkl_preprocessed")
        # Iterate over all patients and create a pkl for each
        for patient in preprocessed_patient_generator:
            print(patient.id, "processed")

            if DONT_OVERWRITE_PICKLES and patient.id in current_patient_pkls:
                print(patient.id, " already processed and present, skipping...")
                continue

            if patient != None:
                patient.write_to_pkl("../data/pkl_preprocessed")
            print("#################################\n")
        
        answer = input("Want to create new metadata for patients? type \"yes\"\n")
        if answer == "yes":
            patient_loader = read_scans_utils.load_patients_from_pickle(
                pickles_path = "../data/pkl_preprocessed"
            )
            print("Creating new metadata for patients...")
            read_scans_utils.collect_patient_metadata(patient_loader,
                                                      read_from_files = False)
        exit(0)


    elif sys.argv[1] in {"-rfp", "read_from_pickle"}:
    # Read a patient from pickle
    # For display and debugging purposes mostly
    # #################################################################################
        try:
            number = input("Which patient would you like to load? ")
        except:
            print("Wrong input, please input an integer")
            exit(0)

        try:
            patient = Patient.load_patient_from_pkl(patient_id = "MARPROC" + number.zfill(3))
        except:
            print(f"Patient {number} can't be found")
            exit(0)

        print("Outputting patient data to /data/debuggingoutput ...")
        if not os.path.exists(f"../data/debuggingoutput/{patient.id}"):
            os.makedirs(f"../data/debuggingoutput/{patient.id}")
            print(f"Folder ../data/debuggingoutput/{patient.id} created successfully.")
        read_scans_utils.write_train_images(patient,
                                            f"../data/debuggingoutput/{patient.id}")
        
        read_scans_utils.write_label(patient,
                                            f"../data/debuggingoutput/{patient.id}")
            
        patient.show_patient_delineation_slices()
        print(patient.axialt2.shape)
        print(patient.model_data["axialt2"].shape)
        exit(0)


    elif sys.argv[1] in {"-cnd", "create_nnunet_data"}:
    # Process the patient pkl files into nnUNet format
    # #################################################################################
        print("Preparing data for nnUNet...")
        patient_loader = read_scans_utils.load_patients_from_pickle(
            pickles_path = "../data/pkl_preprocessed"
        )
        
        new_dataset_nr = input("New dataset number: ")

        read_scans_utils.write_patients_model_data(new_dataset_nr,
                                                   patient_loader,
                                                   "../data")
        
        answer = "none"
        while answer not in {"y", "n"}:
            answer = input("Do you want to split the data? y/n\n")
        if answer == "y":
            split_data_ = "none"
            while answer not in {"y", "n"}:
                answer = input("Do you want to create a static validation split? y/n\n")
            if answer == "y":
                data_split.create_train_val_test_split(new_dataset_nr,
                                                       save_train_validation_json=True)
            else:
                data_split.create_train_val_test_split(new_dataset_nr,
                                                       save_train_validation_json=None)
        exit(0)


    elif sys.argv[1] in {"-s", "split"}:
    # Create a datasplit & optionally create a validation set
    # If no validation set is given and no split_final.json is made, nnUNet will dynamically
    # create train validation split(s) when called to train
    # #################################################################################
        print("Which dataset would you like to create a train/test split for?")
        print("Datasets:")
        dataset_nrs = set()
        for dataset in os.listdir("../data/nnUNet_raw"):
            dataset_nr = int(dataset[7:10])
            dataset_nrs.add(dataset_nr)

            print(f"    {dataset_nr}: {dataset}")

        dataset_nr = input("")
        if int(dataset_nr) not in dataset_nrs:
            print(f"{dataset_nr} not found")
            exit()
        print()

        answer = "none"
        while answer not in {"y", "n"}:
            answer = input("Do you want to create a static validation split? y/n\n")
        if answer == "y":
            data_split.create_train_val_test_split(dataset_nr,
                                                   save_train_validation_json=True)
        else:
            data_split.create_train_val_test_split(dataset_nr,
                                                   save_train_validation_json=None)
        exit(0)
    
    
    elif sys.argv[1] in {"-rd", "reprocess_delineations"}:
    # Reprocess delineations of patients, saves some time compared to reprocessing all
    # patients entirely when only debugging delineations for example
    # #################################################################################
        patient_loader = read_scans_utils.load_patients_from_pickle(
            pickles_path = "../data/pkl_preprocessed"
        )
        read_scans_utils.reprocess_patients_delineations(patient_loader)
        exit(0)

    
    elif(sys.argv[1] in {"-vm", "verify_matching"}):
    # Verify the matching of Direction matrix and origin of t2 images and their delineations
    # #################################################################################
        answer = input("Verify raw data or nnUNet data? (raw/model)\n")

        if answer == "raw":
            nonmatching_patients = read_scans_utils.verify_raw_data_direction_and_origins(
                seriesnumber_info_path="../data/Scans/T2w_seriesnumber_info_Lucas.xlsx",
                exact_match=False
            )
        elif answer == "model":
            nonmatching_patients = read_scans_utils.verify_model_data_direction_and_origins()
        else:
            print("Expected (raw/model)")
            exit(1)
        print("Patients with errors in direction and/or origin:")
        print(nonmatching_patients)
        exit(0)

    
    elif(sys.argv[1] in {"-rm", "remove_patients"}):
    # Remove a list of patients from model data in given set in patients_to_remove.txt
    # #################################################################################
        try:
            patients_to_remove = [line.strip() 
                                  for line in open("./patients_to_remove.txt").readlines()
                                  if line]
        except:
            print("patients_to_remove.txt not found...")
            exit(0)
        
        set_number = read_scans_utils.prompt_select_set()
        if set_number != None:
            read_scans_utils.remove_patients_from_modeldata(set_number,
                                                            patients_to_remove)
        exit(0)
    
print("usage: python3 load_patients.py")
print("           -rras     read_raw_and_save")
print("               Reads the raw scan data and creates pkl objects of\n\
               patients with loaded relevant data")
print("           -rfp      read_from_pickle")
print("               Reads patient objects from saved patients in pkl files")
print("           -cnd      create_nnunet_data")
print("               Reads patient objects from saved patients in pkl files\n\
               and takes relevant parts and saves them in the format\n\
               nnUNet expects")
print("           -s        split")
print("               Creates a data split using the data present in the \n\
               nnUNet_raw folder. Will use this split & move a part of the full\n\
               set to \\ImagesTs")
print("           -rd       reprocess_delineations")
print("               Will recreate .nii delineations from the raw nrrd files\n\
               and use them to reset the region_delineation fields of patients\n\
               pkl files. Will also reset their model_data fields accordingly.")
print("           -vm       verify_matching")
print("               Verify the matching of Direction matrix and origin of t2\n\
                images and their delineations")
print("           -rm       remove_patients")
print("               Remove patients listed in patients_to_remove.txt from a\n\
                nnUNet preprocessed dataset")