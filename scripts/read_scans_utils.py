# from patient import Patient
import sys
import importlib
from patient import Patient
# importlib.reload(sys.modules["scripts.patient"])

from os import listdir
import os
import json
import nibabel as nb
import nrrd
import pandas as pd
import numpy as np
from collections import defaultdict
import time
from tqdm import tqdm
import pickle
import SimpleITK as sitk

from IPython.display import display_html
from itertools import chain, cycle

import psutil


IMAGE_PATH = "../data/Scans/"
DELINEATIONS_PATH = "../data/Regions ground truth/Regions delineations/"

AXIALT2_INDICATORS = {"ttset2", "tt2_tse.nii", "T2a.nii", "tT2 TSE"}
ADC_INDICATORS = {"_adc.nii", "_ADC.nii"}
PERFUSION_INDICATORS = {"_perffrac.nii", "_perfFrac.nii"}


# Function to create a single patient according to an id and a given path to a folder
# containing T2 axial scans and DWI ADC and perfusion maps
# They are matched to predefined name indicators for the filenames, which are manually
# extracted by examining the data. They differ greatly across the data, introducing
# complexity to the selection of files to read.
def read_patient(folder_name, seriesnumbers_dict, print_errors=False):   
    patient_id = folder_name[:-4] 
    seriesnumber, sequence, number_of_slices = seriesnumbers_dict[patient_id] \
        if patient_id in seriesnumbers_dict \
        else (None, None, None)

    scans = [f for f in listdir(f"{IMAGE_PATH}{folder_name}")]
    patient = Patient(patient_id)

    for scan in scans:
        # Check if a series number was found for the patient
        # If so check if the series number appears in the filename & if
        # the file is a t2 scan (t2 or T2 appears in filename)
        # If not, check if the file is an exception & if *sequence
        # appears in its filename (usually "MARPROC....")
        if (seriesnumber, sequence, number_of_slices) != (None, None, None) and \
            ((not pd.isna(seriesnumber) and seriesnumber in scan and ("t2" in scan or "T2" in scan))
              or sequence in scan):
            axialt2_img = nb.load(f"{IMAGE_PATH}{folder_name}/{scan}")
            patient.set_axialt2(axialt2_img)

            # Check if the shape of the image matches the manually extracted amount of slices from inspection
            patient_axial_shape = patient.get_axialt2_image_array().shape
            if patient_axial_shape[2] != number_of_slices:
                print("--------------------")
                print(folder_name)
                print("Shape ", patient_axial_shape, " doesnt match number of slices ", number_of_slices, "\n")
        elif any([part in scan for part in ADC_INDICATORS]):
            adcdwi_img = nb.load(f"{IMAGE_PATH}{folder_name}/{scan}")
            patient.set_adcdwi(adcdwi_img)
        elif any([part in scan for part in PERFUSION_INDICATORS]):
            perffracdwi_img = nb.load(f"{IMAGE_PATH}{folder_name}/{scan}")
            patient.set_perfusionmap(perffracdwi_img)

    # Some patient folder contain an additional folder called "Transformed"
    # This folder contains images that were manually registered to T2w scans
    # These have priority over the other scans in the folder
    if "Transformed" in scans:
        for scan in [f for f in listdir(f"{IMAGE_PATH}{folder_name}/Transformed")]:
            if any([part in scan for part in ADC_INDICATORS]):
                adcdwi_img = nb.load(f"{IMAGE_PATH}{folder_name}/{scan}")
                patient.set_adcdwi(adcdwi_img)
            elif any([part in scan for part in PERFUSION_INDICATORS]):
                perffracdwi_img = nb.load(f"{IMAGE_PATH}{folder_name}/{scan}")
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

    return {row["Anonymization"]: [row["SeriesNumber"], row["Sequence"], row["NumberOfSlices"]]
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
    
    # for folder in [f for f in listdir(scans_data_path)][0:5]:
    for folder in [f for f in listdir(scans_data_path)]:
        patient_id = folder[:-4]
        
        if patient_id in patients_to_skip:
            continue

        patient = read_patient(folder, scan_seriesnumbers, print_errors=True)
        
        if patient == None:
            print("Error reading patient ", patient_id)
            erroneous_data_patients += patient_id
            continue
        
        delineation = read_combined_delineation(patient_id) 
        if patient.get_axialt2_image_array().shape != delineation.get_fdata().shape:  
            print("Error reading delineation for ", patient_id)
            print("Shapes do not match")
            print(f"t2          :{patient.get_axialt2_image_array().shape}")
            print(f"delineation :{delineation.get_fdata().shape}\n")
            erroneous_data_patients += patient_id
            continue

        patient.set_delineation(delineation)
        patient.scale_dwis_to_t2()
        patient.extract_slice_tuples()

        yield patient

    return erroneous_data_patients


# Function that reads the combined delineation for a single patient
def read_combined_delineation(patient_id):
    path = f"../data/Regions ground truth/delineations_nifti/{patient_id}_combined_delineation.nii.gz"
    
    return nb.load(path)


def load_patient_from_pickle(patient_id):
    path = f"../data/pkl_preprocessed/{patient_id}.pkl"
    with open(path, 'rb') as input:
        patient = pickle.load(input)
            
    return patient

# Read all patients from patient objects saved in pickle files in specified folder
def load_patients_from_pickle(pickles_path):
    if not os.path.exists(pickles_path):
        print(pickles_path)
        print("Doesn't exist...")
        return

    for patient_file in os.listdir(pickles_path):
        patient = load_patient_from_pickle(patient_file.replace(".pkl", ""))

        yield patient


def create_datasetjson(path):
    with open("../data/nnUNet_raw/Dataset001_pca/splits_final.json", 'r', encoding='utf-8') as f:
        split = json.load(f)
        num_training_cases = len(split[0]["train"])

    dataset_dict = {
        "channel_names": {
            "0": "AxialT2",
            "1": "ADC",
            "2": "Perfusion"
        },
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
def write_patients_model_data(patients, path):
    model_data_path = path + "/nnUNet_raw/Dataset001_pca"
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

    if read_from_files == True or patient == None:
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
        unique, counts = np.unique(patient.region_delineation, return_counts=True)
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
        nrrd_delineation_to_nii(patient_id)


def nrrd_delineation_to_nii(patient_id):
    delineations_path = "../data/Regions ground truth"
    nrrds_of_patient_path = f"{delineations_path}/Regions delineations/{patient_id}"
    nii_delineations_path = f"{delineations_path}/delineations_nifti"

    if not os.path.exists(f"{nii_delineations_path}"):
            os.makedirs(f"{nii_delineations_path}")

    combined_delineation = None

    # Reading pre-combined delineations from new patients
    if "combined" in os.listdir(nrrds_of_patient_path):
        delineation = sitk.ReadImage(f"{nrrds_of_patient_path}/{file}")
        combined_delineation = sitk.GetArrayFromImage(delineation)

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





# Read the patient t2
# series_numbers_dict = load_series_numbers_dict("../data/T2w_seriesnumber_info_Lucas.xlsx")
# patient_t2 = read_patient_t2_sitk("MARPROC" + str(patient_number).zfill(3), series_numbers_dict)

# Unused
def read_patient_t2_sitk(patient_id, series_numbers_dict):
    seriesnumber, sequence, number_of_slices = series_numbers_dict[patient_id] \
        if patient_id in series_numbers_dict \
        else (None, None, None)

    patient_folder = f"../data/Scans/{patient_id}_nii"

    scans = [f for f in listdir(patient_folder)]

    for scan in scans:
        # Check if a series number was found for the patient
        # If so check if the series number appears in the filename & if
        # the file is a t2 scan (t2 or T2 appears in filename)
        # If not, check if the file is an exception & if *sequence
        # appears in its filename (usually "MARPROC....")
        if (seriesnumber, sequence, number_of_slices) != (None, None, None) and \
            ((not pd.isna(seriesnumber) and seriesnumber in scan and ("t2" in scan or "T2" in scan))
            or sequence in scan):
            print("Loading ", scan)
            t2 = sitk.ReadImage(f"{patient_folder}/{scan}")

            # Check if the shape of the image matches the manually extracted amount of slices from inspection
            print(t2.GetSize())
            if t2.GetSize()[2] != number_of_slices:
                print("--------------------")
                print(patient_id)
                print("Shape ", t2.GetSize(), " doesnt match number of slices ", number_of_slices, "\n")

            return t2
    
    return None

# TESTING FUNCTION!
def read_and_save_delineation(patient_number):
    path_to_patient_folder = DELINEATIONS_PATH + "MARPROC" + str(patient_number).zfill(3)
    print(path_to_patient_folder)
    delineation_files = os.listdir(path_to_patient_folder)
    # print(delineation_files)
    output_delineation = None
    test_path = "../data/debuggingoutput"


    patient = read_patient("MARPROC" + str(patient_number).zfill(3) + "_nii",
                                 load_series_numbers_dict("../data/T2w_seriesnumber_info_Lucas.xlsx"))
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