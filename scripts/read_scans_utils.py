# from patient import Patient
from scripts.patient import Patient
from os import listdir
import nibabel as nb
from collections import defaultdict

from IPython.display import display_html
from itertools import chain, cycle

IMAGE_PATH = "Scans/"
DELINEATIONS_PATH = ""
READ_BADLY_NAMED_SCANS = True

def read_patient(patient_id, image_path=IMAGE_PATH):
    scans = [f for f in listdir(f"{IMAGE_PATH}{patient_id}")]
    patient = Patient(patient_id)
    file_has_transformed_imgs = "Transformed" in scans

    for scan in scans:
        # Different founc name formattings in dataset
        if "ttset2" in scan or \
           "tt2_tse.nii" in scan or \
           "T2a.nii" in scan or \
           "tT2 TSE" in scan:
            axialt2_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_axialt2(axialt2_img)
        elif "_adc.nii" in scan or "_ADC.nii" in scan:
            adcdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_adcdwi(adcdwi_img)
        elif "_perffrac.nii" in scan or "_perfFrac.nii" in scan:
            perffracdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
            patient.set_perfusionmap(perffracdwi_img)

    # Some patient folder contain an additional folder called "Transformed"
    # This folder contains images that were manually registered to T2w scans
    # These have priority over the other scans in the folder
    if "Transformed" in scans:
        for scan in [f for f in listdir(f"{IMAGE_PATH}{patient_id}/Transformed")]:
            if "_adc.nii" in scan or "_ADC.nii" in scan:
                adcdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
                patient.set_adcdwi(adcdwi_img)
            elif "_perffrac.nii" in scan or "_perfFrac.nii" in scan:
                perffracdwi_img = nb.load(f"{IMAGE_PATH}{patient_id}/{scan}")
                patient.set_perfusionmap(perffracdwi_img)

    # Check for cases where t2scans aren't named by plane & thus arent read correctly
    if READ_BADLY_NAMED_SCANS == True and patient.axialt2 == None:
        # By experimentation it is learned that when 3 t2 scans are present in a patient file,
        # the middle one is the axial scan
        t2scans = [f for f in scans if "t2_tse.nii" in f or "T2 TSE.nii" in f]
        if len(t2scans) == 3:
            axialt2_img = nb.load(f"{IMAGE_PATH}{patient_id}/{t2scans[1]}")
            patient.set_axialt2(axialt2_img)
    
    couldntfind = False
    if patient.axialt2 == None:
        print("Couldnt find axialt2")
        couldntfind = True
    if patient.adcmap == None:
        print("Couldnt find adcmap")
        couldntfind = True
    if patient.perfusionmap == None:
        print("Couldnt find perfusionmap")
        couldntfind = True
    
    if couldntfind == True:
        print(patient_id)
        print([scan for scan in scans if "t2_tse" in scan])
        print("###############\n")
        return None
            
    return patient

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
