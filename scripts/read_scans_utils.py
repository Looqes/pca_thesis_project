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
def load_series_numbers_dict(filename):
    df = pd.read_excel(filename, dtype= {"SeriesNumber": str, "NumberOfSlices": int})

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
def read_preprocess_patients(scans_data_path, seriesnumber_info_path, delineations_path=DELINEATIONS_PATH):
    erroneous_data_patients = []
    scan_seriesnumbers = load_series_numbers_dict(seriesnumber_info_path)
    
    # for folder in [f for f in listdir(scans_data_path)][0:5]:
    for folder in [f for f in listdir(scans_data_path)]:
        patient_id = folder[:-4]
        patient = read_patient(folder, scan_seriesnumbers, print_errors=True)
        
        if patient == None:
            print("Error reading patient ", patient_id)
            erroneous_data_patients += patient_id
            continue
        
        try:
            delineations = read_delineations(delineations_path + "/" + patient_id)   
        except:
            print("Error reading delineation for ", patient_id)
            erroneous_data_patients += patient_id
            continue

        add_delineations_to_patient(patient, delineations)
        patient.scale_dwis_to_t2()
        patient.extract_slice_tuples()

        yield patient

    return erroneous_data_patients


# Function that reads delineations for a single patients
def read_delineations(delineations_folder_path):
    delineations = []

    for file in listdir(delineations_folder_path):
        delineation = nrrd.read(delineations_folder_path + "/" + file)
        delineations.append((file, delineation))
    
    return delineations


# Function to add delineations to single patient
def add_delineations_to_patient(patient, delineations):
    delineation_shapes = {delineations[i][1][0].shape for i in range(len(delineations))}

    if len(delineation_shapes) == 1 and \
           patient.get_axialt2_image_array().shape == next(iter(delineation_shapes)):
            patient.add_delineations(delineations)
    else:
        print("Problem with delineations for ", patient.id, ". Shapes: ")
        print("AxialT2:     ", patient.get_axialt2_image_array().shape)
        print("Delineation: ", delineation_shapes)
        print()


# Read patient objects from pickles in specified folder
def load_patient_from_pickle(path, patient_id):
    if not os.path.exists(path):
        print(path)
        print("Doesn't exist...")

    print(os.listdir(path))
    
    with open(path + "/" + patient_id + ".pkl", 'rb') as input:
        patient = pickle.load(input)
            
    return patient


# path = "../data"
# TODO
def write_patient_model_data(patient, path):
    model_data_path = path + "/nnUNet_raw/Dataset001_pca"

    if not os.path.exists(model_data_path):
        os.makedirs(model_data_path)
        print(f"Folder '{model_data_path}' created successfully.")
    else:
        print(f"Folder '{model_data_path}' already exists.")


    # for patient_id in patients:
    #     patient = patients[patient_id]