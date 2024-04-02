import sys
import importlib
from os import listdir

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


# Loading the patients
print("Loading MRI scans...")
patients, erroneous_patient_ids = read_scans_utils.read_patients(scans_data_path="../data/Scans",
                                          seriesnumber_info_path="../data/T2w_seriesnumber_info_Lucas.xlsx")

print("Amount of patient successfully read:")
print(len(patients))
print()


# Loading the delineations
print("Loading delineations...")
delineations = read_scans_utils.read_delineations()

print("Amount of delineations successfully read: ")
print(len(delineations))
print()


# Adding the delineations to their patients
print("Adding delineations to patients...")
read_scans_utils.combine_patients_delineations(patients, delineations)
Patient.show_patient_delineation_slices(patients["MARPROC007"])
Patient.show_patient_delineation_slices(patients["MARPROC204"])
print()

