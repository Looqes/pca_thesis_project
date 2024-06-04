from patient import Patient

from os import listdir
import os
import json
import nibabel as nb
import nrrd
import pandas as pd
import numpy as np
import pickle
import SimpleITK as sitk




SCANS_PATH = "../data/Scans/all_scans"
DELINEATIONS_PATH = "../data/Regions ground truth/Regions delineations/"
NIFTI_DELINEATIONS_PATH = "../data/Regions ground truth/delineations_nifti"

AXIALT2_INDICATORS = {"t2", "T2"}
ADC_INDICATORS = {"_adc.nii", "_ADC.nii"}
PERFUSION_INDICATORS = {"_perffrac.nii", "_perfFrac.nii"}


# Function to create a single patient according to an id and a given path to a folder
# containing T2 axial scans and DWI ADC and perfusion maps
# They are matched to predefined name indicators for the filenames, which are manually
# extracted by examining the data. They differ greatly across the data, introducing
# complexity to the selection of files to read.
def read_patient(folder_name, seriesnumbers_dict, print_errors=False, scans_path=SCANS_PATH):   
    patient_id = folder_name[:10] 
    patient = Patient(patient_id)
    seriesnumber, sequence = seriesnumbers_dict[patient_id] \
        if patient_id in seriesnumbers_dict \
        else (None, None)
    
    # Search patient scans folder
    path_to_patient_scans = f"{scans_path}/{folder_name}"
    if "nii" in os.listdir(path_to_patient_scans):
        path_to_patient_scans += "/nii"
    scans = [f for f in os.listdir(path_to_patient_scans)]

    for scan in scans:
        # Check if a series number was found for the patient
        # If so check if the series number appears in the filename & if
        # the file is a t2 scan (t2 or T2 appears in filename)
        # If not, check if the file is an exception & if *sequence
        # appears in its filename (usually "MARPROC....")
        if (seriesnumber, sequence) != (None, None) and \
            ((not pd.isna(seriesnumber) and seriesnumber in scan and \
              (any([indicator in scan for indicator in AXIALT2_INDICATORS])))
              or sequence in scan):
            axialt2_img = nb.load(f"{path_to_patient_scans}/{scan}")
            patient.set_axialt2(axialt2_img)
        elif any([part in scan for part in ADC_INDICATORS]):
            adcdwi_img = nb.load(f"{path_to_patient_scans}/{scan}")
            patient.set_adcdwi(adcdwi_img)
        elif any([part in scan for part in PERFUSION_INDICATORS]):
            perffracdwi_img = nb.load(f"{path_to_patient_scans}/{scan}")
            patient.set_perfusionmap(perffracdwi_img)

    # Some patient folder contain an additional folder called "Transformed"
    # This folder contains images that were manually registered to T2w scans
    # These have priority over the other scans in the folder
    if "Transformed" in scans:
        for scan in [f for f in listdir(f"{path_to_patient_scans}/Transformed")]:
            if any([part in scan for part in ADC_INDICATORS]):
                adcdwi_img = nb.load(f"{path_to_patient_scans}/{scan}")
                patient.set_adcdwi(adcdwi_img)
            elif any([part in scan for part in PERFUSION_INDICATORS]):
                perffracdwi_img = nb.load(f"{path_to_patient_scans}/{scan}")
                patient.set_perfusionmap(perffracdwi_img)
  
    couldntfind = False
    if patient.axialt2 == None:
        print_errors == True and print("Couldnt find axialt2")
        if seriesnumber == None:
            print("No entry for series number")
        couldntfind = True
    if patient.adcmap == None:
        print_errors == True and print("Couldnt find adcmap")
        couldntfind = True
    if patient.perfusionmap == None:
        print_errors == True and print("Couldnt find perfusionmap")
        couldntfind = True
    
    if couldntfind == True:
        print_errors == True and print(folder_name)
        print_errors == True and print([scan for scan in scans if "t2" in scan or "T2" in scan])
        print_errors == True and print("###############\n")
        return None
                
    return patient


# Function that loads an excel sheet containing information that maps a patient id to the series number
# of that patient's axial scan, and to the name of that patient's axial scan if the normally named file
# is absent. 
# Also load the expected amount of slices to be found in the axial scan for error checking.
def load_series_numbers_dict(filepath):
    df = pd.read_excel(filepath, dtype= {"SeriesNumber": str, "NumberOfSlices": int})

    return {row["Anonymization"]: [row["SeriesNumber"], row["Sequence"]]
            for _, row in df.iterrows()}


# Function that reads patients, prepocesses them and returns them one by one by generator
# A patient is read, forming a patient object with an id, and the scans:
#   axialt2
#   adcmap
#   perfusionmap
#   region_delineation
# The adcmap and perfusionmap are then scaled to the axialt2
# Modeling-relevant slices (those that have a delineation present in the region delineation)
# are extracted and saved in the model_data field
def read_preprocess_patients(scans_data_path, seriesnumber_info_path, patients_to_skip=set()):
    erroneous_data_patients = []
    scan_seriesnumbers = load_series_numbers_dict(seriesnumber_info_path)
    
    for folder in [f for f in listdir(scans_data_path)]:
        patient_id = folder[:10]
        
        if patient_id in patients_to_skip:
            continue

        # 1. Read the scans of patient & construct patient object
        patient = read_patient(folder, scan_seriesnumbers, print_errors=True)
        
        if patient == None:
            print("Error reading patient ", patient_id)
            erroneous_data_patients += patient_id
            continue
        
        # 2. Try to find & read delineation of patient
        try:
            delineation = read_combined_delineation(patient_id) 
        except FileNotFoundError:
            print(f"No delineation file found for {patient_id}")
            erroneous_data_patients += patient_id
            continue
        except:
            print(f"Unknown error for {patient_id}")
            erroneous_data_patients += patient_id
            continue

        # 3. Check if the delineation is correct
        if patient.get_axialt2_image_array().shape != delineation.get_fdata().shape:  
            print("Error reading delineation for ", patient_id)
            print("Shapes do not match")
            print(f"t2          :{patient.get_axialt2_image_array().shape}")
            print(f"delineation :{delineation.get_fdata().shape}\n")
            erroneous_data_patients += patient_id
            continue

        # 4. Add delineations to patient & apply required preprocessing
        patient.set_delineation(delineation)
        patient.scale_dwis_to_t2()
        patient.extract_slice_tuples()

        yield patient

    return erroneous_data_patients


# Function to load patient pkls and reprocess their delineations, essentially
# overwriting their delineation data
# Will follow up with required checking of consistency (e.g. comparing shape)
# and resetting the model_data field for the patients aswell, as it is dependent
# on delineation data
def reprocess_patients_delineations(patients):
    # First re-create the nii delineations from the raw data
    convert_delineations_to_nii()

    erroneous_data_patients = []

    # Reset the delineations & model data for each patient
    for patient in patients:
        patient_id = patient.id
        print(f"Reprocessing patient {patient_id}")

        # 1. Try to find & read delineation of patient
        try:
            delineation = read_combined_delineation(patient_id) 
        except FileNotFoundError:
            print(f"No delineation file found for {patient_id}")
            erroneous_data_patients += patient_id
            continue
        except:
            print(f"Unknown error for {patient_id}")
            erroneous_data_patients += patient_id
            continue

        # 2. Check if the delineation is correct
        if patient.get_axialt2_image_array().shape != delineation.get_fdata().shape:  
            print("Error reading delineation for ", patient_id)
            print("Shapes do not match")
            print(f"t2          :{patient.get_axialt2_image_array().shape}")
            print(f"delineation :{delineation.get_fdata().shape}\n")
            erroneous_data_patients += patient_id
            continue

        # 3. Reset the delineation & set model_data
        #    This time skip the rescaling step of DWIs, only delineations are reset
        patient.set_delineation(delineation)
        patient.extract_slice_tuples()
    
    return erroneous_data_patients


# Function that reads the combined delineation for a single patient
def read_combined_delineation(patient_id):
    path = f"../data/Regions ground truth/delineations_nifti/{patient_id}_combined_delineation.nii.gz"
    
    return nb.load(path)


# Read all patients from patient objects saved in pickle files in specified folder
def load_patients_from_pickle(pickles_path):
    if not os.path.exists(pickles_path):
        print(pickles_path)
        print("Doesn't exist...")
        return

    for patient_file in os.listdir(pickles_path):
        patient = Patient.load_patient_from_pkl(patient_file.replace(".pkl", ""))

        yield patient


def create_datasetjson(path, modalities):
    # Number of training cases is the total number of training patients
    # divided by the number of modalities (3)
    num_training_cases = int(len(os.listdir(f"{path}/ImagesTr"))/len(modalities))
    channel_names = {int(num): modality
                     for num, modality
                     in zip(range(len(modalities)), modalities)}

    dataset_dict = {
        "channel_names": channel_names,
        "labels": {
            "background": 0,
            "GG3": 1,
            "GG4": 2,
            "Cribriform": 3
        },
        "numTraining": num_training_cases,
        "file_ending": ".nii.gz"
    }

    with open(path + '/dataset.json', 'w', encoding='utf-8') as f:
        json.dump(dataset_dict, f, ensure_ascii=False, indent=4)


# Write data according to expected format for nnUNet usage
def write_train_images(patient, path):
    nb.save(patient.model_data["axialt2"], path + f"/{patient.id}_" + "0000.nii.gz")
    nb.save(patient.model_data["adcmap"], path + f"/{patient.id}_" + "0001.nii.gz")
    nb.save(patient.model_data["perfusionmap"], path + f"/{patient.id}_" + "0002.nii.gz")

def write_label(patient, path):
    nb.save(patient.model_data["region_delineation"], path + f"/{patient.id}" + ".nii.gz")



# path = "../data"
# Function that writes data of given iterable of patients in the format that is expected by nnUNet
def write_patients_model_data(dataset_nr, patients, path):
    model_data_path = path + "/nnUNet_raw/Dataset" + str(dataset_nr).zfill(3) + "_pca"
    train_data_path = model_data_path + "/imagesTr"
    labels_data_path = model_data_path + "/labelsTr"

    for folder in (model_data_path,
                 train_data_path,
                 labels_data_path):
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Folder '{folder}' created successfully.")
    
    for patient in patients:
        print(patient.id)
        print("---\n")
        write_train_images(patient,
                           train_data_path)
        write_label(patient,
                    labels_data_path)
        

# Function to collect various metadata about patients:
# A dict describing how many voxels in a segmentation are of each Gleason pattern
#   For the full images, sub images after processing, and individual slices
#   
def collect_patient_metadata(patients=None, read_from_files=False):
    if not os.path.exists("../data/patient_metadata"):
        os.makedirs("../data/patient_metadata")
        print(f"Folder ../data/patient_metadata created successfully.")

    if read_from_files == True or patients == None:
        with open("../data/patient_metadata/voxel_dists.pkl", 'rb') as f:
            voxel_dists = pickle.load(f)

        with open("../data/patient_metadata/patients_image_shapes.pkl", 'rb') as f:
            shapes = pickle.load(f)

        with open("../data/patient_metadata/slice_occupance_dist.pkl", 'rb') as f:
            slice_occupance_dist = pickle.load(f)
        
        return voxel_dists, shapes, slice_occupance_dist

    voxel_dists = {"full_image": [],
                   "sub_image": [],
                   "data_slices": []}

    shapes = []
    slice_occupance_dist = []

    for patient in patients:
        print(patient.id)
        shapes.append(patient.get_axialt2_image_array().shape)

        # Collecting voxel counts for the patient's full image
        unique, counts = np.unique(patient.region_delineation.get_fdata(), return_counts=True)
        gg_voxel_dist = dict(zip(unique.astype(int), counts))
        voxel_dists["full_image"].append((patient.id, gg_voxel_dist))

        # Collecting voxel counts for the patient from the image of slices that
        # have ground truth (that have a delineation)
        # These are the images that will be fed to the model and thus form the
        # input data
        unique, counts = np.unique(patient.model_data["region_delineation"].get_fdata(), return_counts=True)
        gg_voxel_dist = dict(zip(unique.astype(int), counts))
        voxel_dists["sub_image"].append((patient.id, gg_voxel_dist))

        # Checking the data per slice, as the model input will eventually consist of single
        # slice tuples
        for slice in np.rollaxis(patient.model_data["region_delineation"].get_fdata(), 2):
            unique, counts = np.unique(slice, return_counts=True)
            gg_voxel_dist = dict(zip(unique.astype(int), counts))
            voxel_dists["data_slices"].append((patient.id, gg_voxel_dist))

        slice_occupance_dist.append((patient.id, patient.get_patient_delineation_slices(), patient.region_delineation.shape[2]))

    with open("../data/patient_metadata/voxel_dists.pkl", 'wb') as f:
        pickle.dump(voxel_dists, f)

    with open("../data/patient_metadata/patients_image_shapes.pkl", 'wb') as f:
        pickle.dump(shapes, f)

    with open("../data/patient_metadata/slice_occupance_dist.pkl", 'wb') as f:
        pickle.dump(slice_occupance_dist, f)

    return voxel_dists, shapes, slice_occupance_dist





# Convert all nrrd delineations in the Regions ground truth map to .nii delineations
def convert_delineations_to_nii():
    delineations_path = "../data/Regions ground truth"
    nrrds_path= f"{delineations_path}/Regions delineations/"

    patients_with_nrrds = os.listdir(nrrds_path)

    for patient_id in patients_with_nrrds:
        print(f"Converting {patient_id} delineations to nii...")
        nrrd_delineation_to_nii(patient_id)


# Convert the .nrrd delineations of a single patient to .nii.gz while also combining
# them into a single file
# Patterns are distinguished by the label they are given in the resulting segmentation map
def nrrd_delineation_to_nii(patient_id):
    delineations_path = "../data/Regions ground truth"
    nrrds_of_patient_path = f"{delineations_path}/Regions delineations/{patient_id}"
    nii_delineations_path = f"{delineations_path}/delineations_nifti"

    if not os.path.exists(f"{nii_delineations_path}"):
            os.makedirs(f"{nii_delineations_path}")

    combined_delineation = None

    for file in os.listdir(nrrds_of_patient_path):
        if "Atrophy" in file:
            continue
        delineation = sitk.ReadImage(f"{nrrds_of_patient_path}/{file}")
        delineation_data_array = sitk.GetArrayFromImage(delineation)

        # Initialize resulting delineation image based upon resolution of delineations
        if combined_delineation is None:
            combined_delineation = np.zeros(delineation_data_array.shape)
            
        if "GG3" in file:
            combined_delineation[delineation_data_array != 0] = 1
        elif "GG4" in file:
            combined_delineation[delineation_data_array != 0] = 2
        elif "Cribriform" in file:
            combined_delineation[delineation_data_array != 0] = 3

    # Make back into an image object & set required header info
    # Use whatever delineation was last in var delineation, as the spatial info
    # is shared among all delineations for a single patient
    combined_delineation = sitk.GetImageFromArray(combined_delineation)
    combined_delineation.SetSpacing(delineation.GetSpacing())
    combined_delineation.SetOrigin(delineation.GetOrigin())
    combined_delineation.SetDirection(delineation.GetDirection())

    sitk.WriteImage(combined_delineation,
                    f"{nii_delineations_path}/{patient_id}_combined_delineation.nii.gz")



# Function to verify that for each patient in the model data, the direction matrix and origin
# of the t2 images match those of their registered delineations.
# If they are not the same, model preprocessing and training cannot start.
def verify_model_data_direction_and_origins():
    nnUNet_data_path = "../data/nnUNet_raw/Dataset005_pca"
    train_images_path = f"{nnUNet_data_path}/ImagesTr"
    test_images_path = f"{nnUNet_data_path}/ImagesTs" \
                       if os.path.exists(f"{nnUNet_data_path}/ImagesTs") \
                       else None
    labels_path = f"{nnUNet_data_path}/labelsTr"
    faulty_patients = set()

    # Checking train images
    ids = list(set([f[:10] for f in os.listdir(train_images_path)]))

    specific_patient = input("Want to check a specific patient? \"no\"\\\"id\": ")
    if "no" in specific_patient:
        specific_patient = None

    for id in ids:
        if specific_patient != None:
            if id != specific_patient:
                continue

        print(f"Checking patient {id}")
        t2 = sitk.ReadImage(f"{train_images_path}/{id}_0000.nii.gz")
        delineation = sitk.ReadImage(f"{labels_path}/{id}.nii.gz")

        # Check if Direction matrix matches
        if np.allclose(t2.GetDirection(), delineation.GetDirection(), rtol=0.001) == False:
            faulty_patients.add(id)
            print(f"Direction mismatch for {id}")
            print("\nt2 Direction matrix:   ")
            print(t2.GetDirection())
            print("\nDelineation Direction matrix:  ")
            print(delineation.GetDirection())
        
        if np.allclose(t2.GetOrigin(), delineation.GetOrigin(), rtol=0.001) == False:
            faulty_patients.add(id)
            print(f"Origin mismatch for patient {id}")
            print("\nt2 Origin:           ")
            print(t2.GetOrigin())
            print("\nDelineation Origin:  ")
            print(delineation.GetOrigin())
        
        print()

    # Checking test images
    if test_images_path:
        ids = list(set([f[:10] for f in os.listdir(test_images_path)]))

        for id in ids:
            if specific_patient != None:
                if id != specific_patient:
                    continue

            print(f"Checking patient {id}")
            t2 = sitk.ReadImage(f"{test_images_path}/{id}_0000.nii.gz")
            delineation = sitk.ReadImage(f"{labels_path}/{id}.nii.gz")

            # Check if Direction matrix matches
            if np.allclose(t2.GetDirection(), delineation.GetDirection(), rtol=0.001) == False:
                faulty_patients.add(id)
                print(f"Direction mismatch for {id}")
                print("\nt2 Direction matrix:   ")
                print(t2.GetDirection())
                print("\nDelineation Direction matrix:  ")
                print(delineation.GetDirection())
            
            if np.allclose(t2.GetOrigin(), delineation.GetOrigin(), rtol=0.001) == False:
                faulty_patients.add(id)
                print(f"Origin mismatch for patient {id}")
                print("\nt2 Origin:           ")
                print(t2.GetOrigin())
                print("\nDelineation Origin:  ")
                print(delineation.GetOrigin())

            print()

    faulty_patients = list(faulty_patients)
    faulty_patients.sort(key = lambda x: int(x[-3:]))

    return faulty_patients


# Function to verify that for each patient in the model data, the direction matrix and origin
# of the t2 images match those of their registered delineations.
# If they are not the same, model preprocessing and training cannot start.
def verify_raw_data_direction_and_origins(seriesnumber_info_path, exact_match=False):
    seriesnumbers_dict = load_series_numbers_dict(seriesnumber_info_path)

    scans_data_path = f"../data/Scans/all_scans"
    raw_delineations_path = f"../data/Regions ground truth/Regions delineations"

    patient_folders = [f for f in os.listdir(scans_data_path)]

    specific_patient = input("Want to check a specific patient? \"no\"\\\"id\": ")
    if "no" in specific_patient:
        specific_patient = None

    faulty_patients = set()
    for patient_folder in patient_folders:
        patient_id = patient_folder[:10]

        if specific_patient != None:
            if patient_id != specific_patient:
                continue

        seriesnumber, sequence = seriesnumbers_dict[patient_id] \
        if patient_id in seriesnumbers_dict \
        else (None, None)

        # Search patient scans folder
        path_to_patient_scans = f"{scans_data_path}/{patient_folder}"
        if "nii" in os.listdir(path_to_patient_scans):
            path_to_patient_scans += "/nii"
        scans = [f for f in os.listdir(path_to_patient_scans)]

        for scan in scans:
            if (seriesnumber, sequence) != (None, None) and \
                ((not pd.isna(seriesnumber) and seriesnumber in scan and \
                (any([indicator in scan for indicator in AXIALT2_INDICATORS])))
                ):
                t2 = sitk.ReadImage(f"{path_to_patient_scans}/{scan}")

                # find delineation
                for f in os.listdir(raw_delineations_path):
                    if patient_id in f:
                        # print(f"Found patient delineations folder: {f}")
                        path_to_patient_delineation_folder = f"{raw_delineations_path}/{f}"
                        print(path_to_patient_delineation_folder)
                        first_scan_in_folder = os.listdir(path_to_patient_delineation_folder)[0]
                        print(first_scan_in_folder)
                        delineation = sitk.ReadImage(f"{path_to_patient_delineation_folder}/{first_scan_in_folder}")

                        # Check if the direction & origins match between images
                        # Check with a margin if exact_match == False
                        if exact_match == False:
                            direction_match = np.allclose(t2.GetDirection(), delineation.GetDirection(), rtol=0.001)
                            origin_match = np.allclose(t2.GetOrigin(), delineation.GetOrigin(), rtol=0.001)
                        else:
                            direction_match = np.all(t2.GetDirection() == delineation.GetDirection())
                            origin_match = np.all(t2.GetOrigin() == delineation.GetOrigin())
                        if direction_match == False:
                            faulty_patients.add(patient_id)
                            print(f"Direction mismatch for {patient_id}")
                            print("\nt2 Direction matrix:   ")
                            print(t2.GetDirection())
                            print("\nDelineation Direction matrix:  ")
                            print(delineation.GetDirection())
                        if origin_match == False:
                            faulty_patients.add(patient_id)
                            print(f"Origin mismatch for patient {patient_id}")
                            print("\nt2 Origin:           ")
                            print(t2.GetOrigin())
                            print("\nDelineation Origin:  ")
                            print(delineation.GetOrigin())
                        break

        if specific_patient != None:
            if patient_id == specific_patient:
                print("\nt2 Direction matrix:   ")
                print(t2.GetDirection())
                print("\nDelineation Direction matrix:  ")
                print(delineation.GetDirection())
                return
        print("----\n\n")

    faulty_patients = list(faulty_patients)
    faulty_patients.sort(key = lambda x: int(x[-3:]))

    return faulty_patients


# Prompt user to select a nnUNet dataset by set id (the integer identifier)
def prompt_select_set():
    print("From which set?")
    set_nrs = set()
    for dataset in os.listdir("../data/nnUNet_raw"):
        set_nr = int(dataset[7:10])
        set_nrs.add(set_nr)
        print(f"    {set_nr}: {dataset}")
    answer = input("")
    if int(answer) not in set_nrs:
        print(f"Set {answer} not found")
        return None
    else:
        return answer


# Function to remove files of model data of a given iterable of patient_id's
# from a single nnUNet-preprocessed dataset
def remove_patients_from_modeldata(dataset_nr,
                                   patients_to_remove):
    path_to_dataset = None
    removed_successfully = []

    for dataset in os.listdir("../data/nnUNet_raw"):
        if str(dataset_nr).zfill(3) in dataset:
            path_to_dataset = f"../data/nnUNet_raw/{dataset}"
            break
    
    if path_to_dataset == None:
        print(f"Dataset {dataset_nr} not found...")

    # Deleting files in the training folder
    for patient_file in os.listdir(f"{path_to_dataset}/imagesTr"):
        patient_id = patient_file[:10]

        if patient_id in patients_to_remove:
            os.remove(f"{path_to_dataset}/imagesTr/{patient_file}")
            removed_successfully.append(patient_file)
    # Deleting files in the labels folder
    for patient_file in os.listdir(f"{path_to_dataset}/labelsTr"):
        patient_id = patient_file[:10]

        if patient_id in patients_to_remove:
            os.remove(f"{path_to_dataset}/labelsTr/{patient_file}")
            removed_successfully.append(patient_file)
    # Deleting files in the test folder if it exists
    if os.path.exists(f"{path_to_dataset}/imagesTs"):
        for patient_file in os.listdir(f"{path_to_dataset}/imagesTs"):
            patient_id = patient_file[:10]

            if patient_id in patients_to_remove:
                os.remove(f"{path_to_dataset}/imagesTs/{patient_file}")
                removed_successfully.append(patient_id)

    print("Removed")
    print(f"{removed_successfully}")
    print("Successfully")


# Function to determine the gleason grade of a patient's delineation by
# counting the amount of voxels per pattern
# The two most common classes of voxels determine the grade
def determine_gleason_grade(delineation):
    data_array = sitk.GetArrayFromImage(delineation)

    label_to_gleasonscore = {
        1: 3,
        2: 4,
        3: 4
    }

    gleasonscores_to_gleasongroup = {
        # if only pattern 3 is found, the lesion is treated as 3 + 3, giving
        # gleason grade group 1
        (3,): 1,
        (3, 4): 2,
        (4, 3): 3,
        # if only pattern 4 is found, the lesion is treated as 4 + 4, giving
        # gleason grade group 4
        (4,): 4,
        (4, 4): 4
    }

    unique, counts = np.unique(data_array, return_counts=True)
    dct = dict(zip(unique, counts))
    del dct[0]
    if not dct:
        print("No delineated voxels, no regions\n")
        return 0, False
    
    sorted_region_occurrences = sorted(dct.items(),
                                       key = lambda x: x[1], 
                                       reverse = True)

    has_cribriform = any([item[0] == 3 for item in sorted_region_occurrences])
    gleason_scores = tuple([label_to_gleasonscore[label] for label, _ in sorted_region_occurrences][:2])

    print(gleason_scores, " giving gleason grade group: ", gleasonscores_to_gleasongroup[gleason_scores])
    return gleasonscores_to_gleasongroup[gleason_scores], has_cribriform



# Function that gives the indexes (in depth) of the slices that have delineations in them
# it is assumed that the given delineation is an image opened with sitk, in which the first
# index represents the z direction or depth (z, x, y)
def get_delineated_slice_indexes_from_delineation(delineation):
    if isinstance(delineation, np.ndarray):
        delineation_array = delineation
    else:
        delineation_array = sitk.GetArrayFromImage(delineation)

    delineation_slices = []
    for i, slice in enumerate(np.rollaxis(delineation_array, axis = 0)):
        if len(np.unique(slice)) > 1:
            delineation_slices.append(i)
    
    return delineation_slices






# TESTING FUNCTION!
def read_and_save_delineation(patient_number):
    path_to_patient_folder = DELINEATIONS_PATH + "MARPROC" + str(patient_number).zfill(3)
    print(path_to_patient_folder)
    delineation_files = os.listdir(path_to_patient_folder)
    # print(delineation_files)
    output_delineation = None
    test_path = "../data/debuggingoutput"


    patient = read_patient("MARPROC" + str(patient_number).zfill(3) + "_nii",
                                 load_series_numbers_dict("../data/Scans/T2w_seriesnumber_info_Lucas.xlsx"))
    if not os.path.exists(test_path + "/MARPROC" + str(patient_number).zfill(3)):
            os.makedirs(test_path + "/MARPROC" + str(patient_number).zfill(3))

    output_delineation = np.zeros(patient.axialt2.shape)

    for file in os.listdir(path_to_patient_folder):
        if "Atrophy" in file:
            continue
        delineation = nrrd.read(path_to_patient_folder + "/" + file)
            
        if "GG3" in file:
            output_delineation[delineation[0] != 0] = 1
        elif "GG4" in file:
            output_delineation[delineation[0] != 0] = 2
        elif "Cribriform" in file:
            output_delineation[delineation[0] != 0] = 3
        
        # Save as nifti with t2 affine, and save back as nrrd
        delin_before = nb.Nifti1Image(delineation[0],
                                      patient.axialt2.affine)
        
        nb.save(delin_before, test_path + f"/{patient.id}/{patient.id}_delineation_nii_{file[:-5]}" + ".nii.gz")

        nrrd.write(test_path + f"/{patient.id}/{patient.id}_delineation_raw_{file[:-5]}" + ".nrrd", 
                   data = delineation[0], 
                   header = delineation[1])
                

    t2 = nb.Nifti1Image(patient.axialt2.get_fdata(), 
                        patient.axialt2.affine)
    
    nifti_delineation = nb.Nifti1Image(output_delineation,
                                       None)
                                    #    patient.axialt2.affine)
    
    nifti_delineation.header.set_data_dtype(delineation[0].dtype)
    nifti_delineation.header.set_zooms([delineation[1]['space directions'][0, 0],
                                        delineation[1]['space directions'][1, 1],
                                        delineation[1]['space directions'][2, 2]])
        
    nb.save(t2, test_path + f"/{patient.id}/{patient.id}_t2" + ".nii.gz")
    nb.save(nifti_delineation, test_path + f"/{patient.id}/{patient.id}_delineation_combined" + ".nii.gz")



