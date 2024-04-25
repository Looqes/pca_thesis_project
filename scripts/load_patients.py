import sys
import importlib
import os
import pickle

from collections import defaultdict
import numpy as np
import pandas as pd
import pylab as plt
# import matplotlib as plt
# %matplotlib inline
import SimpleITK as sitk
from tqdm import tqdm
import nibabel as nb
import nrrd

# Custom objects included in scripts
# from scripts.patient import Patient
# from scripts import read_scans_utils
from patient import Patient
import read_scans_utils

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
            scans_data_path="../data/Scans",
            seriesnumber_info_path="../data/T2w_seriesnumber_info_Lucas.xlsx",
            patients_to_skip = current_patient_pkls
        )


        # Iterate over all patients and create a pkl for each
        for patient in preprocessed_patient_generator:
            print(patient.id, "processed")

            if DONT_OVERWRITE_PICKLES and patient.id in current_patient_pkls:
                print(patient.id, " already processed and present, skipping...")
                continue

            if patient != None:
                patient.write_to_pkl("../data/pkl_preprocessed")
            print("#################################\n")
        exit(0)


    elif sys.argv[1] in {"-rfp", "read_from_pickle"}:
    # #################################################################################
        patient = read_scans_utils.load_patient_from_pickle(patient_id = "MARPROC422")
        
        read_scans_utils.write_train_images(patient,
                                            f"../data/debuggingoutput/{patient.id}")
        
        read_scans_utils.write_label(patient,
                                            f"../data/debuggingoutput/{patient.id}")
            
        
        patient.show_patient_delineation_slices()

        exit(0)


    elif sys.argv[1] in {"-cnd", "create_nnunet_data"}:
    # #################################################################################
        print("Preparing data for nnUNet...")
        patient_loader = read_scans_utils.load_patients_from_pickle(
            path = "../data/pkl_preprocessed"
        )

        # patient_7 = read_scans_utils.load_patient_from_pickle(
        #     path = "../data/pkl_preprocessed",
        #     patient_id = "MARPROC007")
        
        read_scans_utils.write_patients_model_data(patient_loader,
                                                  "../data")
        exit(0)
print("usage: python3 load_patients.py")
print("           -rras     read_raw_and_save")
print("               Reads the raw scan data and creates pkl objects of\n \
              patients with loaded relevant data")
print("           -rfp      read_from_pickle")
print("               Reads patient objects from saved patients in pkl files")
print("           -cnd      create_nnunet_data")
print("               Reads patient objects from saved patients in pkl files\n \
              and takes relevant parts and saves them in the format\n \
              nnUNet expects")
