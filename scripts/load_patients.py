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

# If read raw and save is selected on running the program the raw scan data will be read
# and patient objects will be created
# MRI's and delineations will be loaded and combined,
# ADC and perfusion scans will be saved,
# and relevant slices will be extracted and save per patient
# These objects will be saved to pickle format files for faster reading later
print(len(sys.argv))
if len(sys.argv) == 2:
    if sys.argv[1] in {"-rras", "read_raw_and_save"}:
        print("Raw data will be read, processed and saved into pkls...")
        preprocessed_patient_generator = read_scans_utils.read_preprocess_patients(
            scans_data_path="../data/Scans",
            seriesnumber_info_path="../data/T2w_seriesnumber_info_Lucas.xlsx"
        )

        for patient in preprocessed_patient_generator:
            print(patient.id)
            # i.write_patient_model_data("../data/testformodeldata")
            if patient != None:
                patient.write_to_pkl("../data/pkl_preprocessed")
            print("#################################\n")
        exit(0)
    elif sys.argv[1] in {"-rfp", "read_from_pickle"}:
        patient_7 = read_scans_utils.load_patient_from_pickle(
            path = "../data/pkl_preprocessed",
            patient_id = "MARPROC007")
            
        
        patient_7.show_patient_delineation_slices()

        exit(0)
print("usage: python3 load_patients.py")
print("           -rras     read_raw_and_save")
print("           -rfp      read_from_pickle")