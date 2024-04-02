# from patient import Patient
import sys
import importlib
from patient import Patient
# importlib.reload(sys.modules["scripts.patient"])


from os import listdir
import nibabel as nb
import nrrd
import pandas as pd
from collections import defaultdict
import time
from tqdm import tqdm

from IPython.display import display_html
from itertools import chain, cycle

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
def read_patient(patient_id, scan_seriesnumbers, print_errors=False):    
    seriesnumber = scan_seriesnumbers[patient_id[:-4]] if patient_id[:-4] in scan_seriesnumbers \
        else None

    scans = [f for f in listdir(f"{IMAGE_PATH}{patient_id}")]
    patient = Patient(patient_id)

    for scan in scans:
        # Check if the indicators appear in the filenames within the scan folders
        # if any([part in scan for part in AXIALT2_INDICATORS]):
            # axialt2_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            # patient.set_axialt2(axialt2_img)
        if ("MARPROC" in scan and "T2a" in scan) or \
           (seriesnumber != None and seriesnumber in scan and ("t2" in scan or "T2" in scan)):
            axialt2_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_axialt2(axialt2_img)
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

    # Check for cases where t2scans aren't named by plane & thus arent read correctly
    if READ_BADLY_NAMED_SCANS == True and patient.axialt2 == None:
        # By experimentation it is learned that when 3 t2 scans are present in a patient file,
        # the middle one is the axial scan
        t2scans = [f for f in scans if "t2" in f or "T2" in f]
        if len(t2scans) == 3:
            axialt2_img = nb.load(f"{IMAGE_PATH}{patient_id}/{t2scans[1]}")
            patient.set_axialt2(axialt2_img)
    
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

def load_series_numbers_dict(filename):
    df = pd.read_excel(filename, dtype= {"SeriesNumber": str})[["Anonymization", "SeriesNumber"]]
    return {patient_id: series_number for patient_id, series_number in zip(df["Anonymization"], df["SeriesNumber"])}

# Function to read and load a dictionary mapping patient id's to patient imaging data
# The patient id's are read from the foldernames of the patients
# Additionally a dictionary mapping patient_id to a seriesnumber of that patient's axial t2 scan
# is included as by filename alone it is not certain which of the t2 scans is the axial one
def read_patients(scans_data_path, seriesnumber_info_path):
    patients = defaultdict(str)
    erroneous_data_patients = []
    scan_seriesnumbers = load_series_numbers_dict(seriesnumber_info_path)

    for folder in tqdm([f for f in listdir(scans_data_path)]):
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

    for folder in tqdm(listdir(delineations_path)):
        # print(folder)
        result[folder] = read_delineation(delineations_path + "/" + folder)
    
    return result

def read_delineation(delineations_folder_path):
    delineations = []

    for file in listdir(delineations_folder_path):
        delineation = nrrd.read(delineations_folder_path + "/" + file)
        delineations.append((file, delineation))
    
    return delineations


def combine_patients_delineations(patients, delineations):
    deleted_ids = []

    for patient_id, delineations_patient in tqdm(delineations.items()):
        # print(patient_id)
        # print(delineations_patient)
        delineation_shapes = {delineations_patient[i][1][0].shape for i in range(len(delineations_patient))}

        # Delineations are of a patient that has no loaded imaging data
        if patient_id not in patients:
            continue
        patient = patients[patient_id]
        # Shapes of delineations must be the same and shape of delineation must match shape of patient axial t2w
        if len(delineation_shapes) == 1 and \
           patient.get_axialt2_image_array().shape == next(iter(delineation_shapes)):
            # print(delineations_patient[0][0])
            patient.add_delineations(delineations_patient)
        else:
            print("Problem with delineations for ", patient_id, ". Shapes: ")
            print(next(iter(delineation_shapes)))
            print(patient.get_axialt2_image_array().shape)
            print()
            # print(patient.get_axialt2_image_array().shape == next(iter(delineation_shapes)))
            del patients[patient_id]
            deleted_ids.append(patient_id)
    
    return deleted_ids
            
           

# patient7 = read_patient("MARPROC017_nii")


# patient7.axialt2
# read_patient("MARPROC009_nii")
# read_patient("MARPROC012_nii")


# Function to display two dataframes next to eachother
def display_side_by_side(*args, titles=cycle([''])):
    html_str = ''
    for df, title in zip(args, chain(titles, cycle(['</br>']))):
        html_str += '<th style="text-align:center"><td style="vertical-align:top">'
        html_str += f'<h2 style="text-align: center;">{title}</h2>'
        html_str += df.to_html().replace('table', 'table style="display:inline"')
        html_str += '</td></th>'
    display_html(html_str, raw=True)
