# from patient import Patient
import sys
import importlib
from patient import Patient
# importlib.reload(sys.modules["scripts.patient"])

from os import listdir
import os
import nibabel as nb
import nrrd
import pandas as pd
import numpy as np
from collections import defaultdict
import time
from tqdm import tqdm
import pickle

from IPython.display import display_html
from itertools import chain, cycle

import psutil


IMAGE_PATH = "../data/Scans/"
DELINEATIONS_PATH = "../data/Regions ground truth/Regions delineations/"
READ_BADLY_NAMED_SCANS = False
# READ_BADLY_NAMED_SCANS = True

AXIALT2_INDICATORS = {"ttset2", "tt2_tse.nii", "T2a.nii", "tT2 TSE"}
ADC_INDICATORS = {"_adc.nii", "_ADC.nii"}
PERFUSION_INDICATORS = {"_perffrac.nii", "_perfFrac.nii"}


# Function to create a single patient according to an id and a given path to a folder
# containing T2 axial scans and DWI ADC and perfusion maps
# They are matched to predefined name indicators for the filenames, which are manually
# extracted by examining the data. They differ greatly across the data, introducing
# complexity to the selection of files to read.
def read_patient(patient_id, seriesnumbers_dict, print_errors=False):    
    seriesnumber, sequence, number_of_slices = seriesnumbers_dict[patient_id[:-4]] \
        if patient_id[:-4] in seriesnumbers_dict \
        else (None, None, None)

    scans = [f for f in listdir(f"{IMAGE_PATH}{patient_id}")]
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
            axialt2_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_axialt2(axialt2_img)

            # Check if the shape of the image matches the manually extracted amount of slices from inspection
            patient_axial_shape = patient.get_axialt2_image_array().shape
            if patient_axial_shape[2] != number_of_slices:
                print("--------------------")
                print(patient_id)
                print("Shape ", patient_axial_shape, " doesnt match number of slices ", number_of_slices, "\n")
        elif any([part in scan for part in ADC_INDICATORS]):
            adcdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_adcdwi(adcdwi_img)
        elif any([part in scan for part in PERFUSION_INDICATORS]):
            perffracdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_perfusionmap(perffracdwi_img)

    # Some patient folder contain an additional folder called "Transformed"
    # This folder contains images that were manually registered to T2w scans
    # These have priority over the other scans in the folder
    if "Transformed" in scans:
        for scan in [f for f in listdir(f"{IMAGE_PATH}{patient_id}/Transformed")]:
            if any([part in scan for part in ADC_INDICATORS]):
                adcdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
                patient.set_adcdwi(adcdwi_img)
            elif any([part in scan for part in PERFUSION_INDICATORS]):
                perffracdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
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
        print_errors == True and print(patient_id)
        print_errors == True and print([scan for scan in scans if "t2" in scan or "T2" in scan])
        print_errors == True and print("###############\n")
        return None
                
    return patient


# Function that loads an excel sheet containing information that maps a patient id to the series number
# of that patient's axial scan, and to the name of that patient's axial scan if the normally named file
# is absent. 
# Also load the expected amount of slices to be found in the axial scan for error checking.
def load_series_numbers_dict(filename):
    df = pd.read_excel(filename, dtype= {"SeriesNumber": str, "NumberOfSlices": int})

    return {row["Anonymization"]: [row["SeriesNumber"], row["Sequence"], row["NumberOfSlices"]]
            for _, row in df.iterrows()}


# Function to read and load a dictionary mapping patient id's to patient imaging data
# The patient id's are read from the foldernames of the patients
# Additionally a dictionary mapping patient_id to a seriesnumber of that patient's axial t2 scan
# is included as by filename alone it is not certain which of the t2 scans is the axial one
def read_patients(scans_data_path, seriesnumber_info_path):
    patients = defaultdict(str)
    erroneous_data_patients = []
    scan_seriesnumbers = load_series_numbers_dict(seriesnumber_info_path)

    for folder in tqdm([f for f in listdir(scans_data_path)]):
    # print("Reading first 5 patients...")
    # for folder in tqdm([f for f in listdir(scans_data_path)][0:5]):
        patient_id = folder[:-4]
        patient = read_patient(folder, scan_seriesnumbers, print_errors=True)
        
        if patient != None:
            patients[patient_id] = patient
        else:
            erroneous_data_patients.append(patient_id)
    
    return patients, erroneous_data_patients


# Pair of functions to read .nrrd delineation files and return a folder_name
# indexed dictionary pointing to the filenames with their data
def read_delineations(delineations_path = DELINEATIONS_PATH):
    result = defaultdict()

    # print("Reading first 5 patients' delineations...")
    # for folder in tqdm(listdir(delineations_path)[:5]):
    for folder in tqdm(listdir(delineations_path)):
        result[folder] = read_delineation(delineations_path + "/" + folder)
    
    return result

def read_delineation(delineations_folder_path):
    delineations = []

    for file in listdir(delineations_folder_path):
        delineation = nrrd.read(delineations_folder_path + "/" + file)
        delineations.append((file, delineation))
    
    return delineations


# Function to add delineations data to a dictionary of patient objects by
# patient_id as key
# Checks if the delineations have a consistent shape and if the shape matches
# that of the T2 scan of the patient to which the delineation is registered
def combine_patients_delineations(patients, delineations):
    deleted_ids = []

    for patient_id, delineations_patient in tqdm(delineations.items()):
    # for patient_id, delineations_patient in delineations.items():
        delineation_shapes = {delineations_patient[i][1][0].shape for i in range(len(delineations_patient))}

        # Delineations are of a patient that has no loaded imaging data
        if patient_id not in patients:
            continue
        patient = patients[patient_id]
        # Shapes of delineations must be the same and shape of delineation must match shape of patient axial t2w
        if len(delineation_shapes) == 1 and \
           patient.get_axialt2_image_array().shape == next(iter(delineation_shapes)):
            patient.add_delineations(delineations_patient)
        else:
            print("Problem with delineations for ", patient_id, ". Shapes: ")
            print("AxialT2:     ", patient.get_axialt2_image_array().shape)
            print("Delineation: ", next(iter(delineation_shapes)))
            print()
            del patients[patient_id]
            deleted_ids.append(patient_id)
    
    # Save memory usage
    del delineations
    
    return deleted_ids


# Will reshape the DWI images of all patients in given patients dict to match axial t2 images of patients
def resize_dwis(patients):
    with tqdm(total=100, desc='cpu%', position=1) as cpubar, tqdm(total=100, desc='ram%', position=0) as rambar:
        for patient_id in tqdm(patients):
            rambar.n=psutil.virtual_memory().percent
            cpubar.n=psutil.cpu_percent()
            rambar.refresh()
            cpubar.refresh()
            patient = patients[patient_id]        
            patient.scale_dwis_to_t2()


# For each patient in the given dict:
# create a subset of slices of each of the image modalities from patient
# select only slices that have a delineation associated with them
def extract_delineated_slices(patients):
    for patient_id in patients:
        patient = patients[patient_id]

        patient.extract_slice_tuples()


def write_patient_objects_to_pickle(patients, path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Folder '{path}' created successfully.")

    for patient_id in tqdm(patients):
        with open(path + patient_id + ".pkl", 'wb') as output:
            pickle.dump(patients[patient_id], output, pickle.HIGHEST_PROTOCOL)

def load_patient_objects_from_pickle(path):
    if not os.path.exists(path):
        print(path)
        print("Doesn't exist...")

    patients = defaultdict(str)
    print(os.listdir(path))
    for file in os.listdir(path):
        with open(path + file, 'rb') as input:
            patient = pickle.load(input)
            patients[file[:-4]] = patient
    
    return patients


            
# path = "../data"
def write_patient_model_data(patients, path):
    model_data_path = path + "/nnUNet_raw/Dataset001_pca"

    if not os.path.exists(model_data_path):
        os.makedirs(model_data_path)
        print(f"Folder '{model_data_path}' created successfully.")
    else:
        print(f"Folder '{model_data_path}' already exists.")


    # for patient_id in patients:
    #     patient = patients[patient_id]