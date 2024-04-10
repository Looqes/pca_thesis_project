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
if sys.argv[1] in {"-rras", "read_raw_and_save"}:
    print("Raw data will be read, processed and saved...") 

    # Loading the patients from the raw data
    #####################################################
    print("Loading MRI scans...")
    patients, erroneous_patient_ids = read_scans_utils.read_patients(
        scans_data_path="../data/Scans",
        seriesnumber_info_path="../data/T2w_seriesnumber_info_Lucas.xlsx")

    print("Amount of patient successfully read:",len(patients))
    print()


    # Loading the delineations
    #####################################################
    print("Loading delineations...")
    delineations = read_scans_utils.read_delineations()

    print("Amount of delineations successfully read: ", len(delineations))
    print()


    # Adding the delineations to their patients
    #####################################################
    print("Adding delineations to patients...")
    read_scans_utils.combine_patients_delineations(patients, delineations)

    print("Amount of read patients with loaded images & delineations: ", len(patients))

    # Patient.show_patient_delineation_slices(patients["MARPROC007"])
    # Patient.show_patient_delineation_slices(patients["MARPROC204"])
    print()


    # Resizing the DWI's of the patients
    #####################################################
    print("Resizing DWI's...")
    read_scans_utils.resize_dwis(patients)
    print()

    # Extracting slices that have a delineation
    #####################################################
    # read_scans_utils.extract_delineated_slices(patients)

    # from nibabel.spatialimages import SpatialFirstSlicer
    # patients["MARPROC007"].extract_slice_tuples()


    # Saving patient objects to pickle files
    #####################################################
    print("Saving objects to pickle files...")
    read_scans_utils.write_patient_objects_to_pickle(
        patients, 
        path="../data/pkl_preprocessed/")


    # Saving the slices & delineations as nifti files
    # according to the required structure for the nnUnet
    #####################################################
    # read_scans_utils.write_patient_model_data(patients, "../data")
elif sys.argv[1] in {"-rfp", "read_from_pickle"}:
    patients = read_scans_utils.load_patient_objects_from_pickle(
        path = "../data/pkl_preprocessed/")
    
    print(patients)
    print(patients["MARPROC007"])
    patients["MARPROC007"].show_patient_delineation_slices()
else:
    print("usage: python3 load_patients.py")
    print("           -rras     read_raw_and_save")
    print("           -rfp      read_from_pickle")