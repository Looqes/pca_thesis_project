# pca_thesis_project
repo for the code for the pca project for the UvA data science master thesis

## scripts

### Core functionality
Contains all scripts made for the project. Mainly for data manipulation and preprocessing/preparing the data for use by nnU-Net. Most of the functionality for data manipulation is contained in the `read_scans_utils.py` script. This script contains code for reading scans, file conversion, patient characteristics calculation (e.g. for Gleason Grade group) and more.

The functions in this script are called by `load_patients.py`.
This script calls functions from `read_scans_utils.py` to perform various tasks. Flags can be passed to determine what tasks it has to perform. Which flags, and what functionalities are associated with them, are shown to the user when calling the script *without* flags.

The handling of data in this project is performed using an object-oriented approach, in which the main objects are `patients`, implemented in patient.py. A patient contains all relevant input data (MRIs and delineations) for a single anonymized patient, identified by a patient id. In the preprocessing pipeline, after relevant data is gathered and preprocessed per patient, these objects are saved into pickle files, serving as a sort of checkpoint from which relevant data can be loaded faster. Saving into, and reading from, pickle files is handled by the aforementioned `load_patients.py`.

### Other scripts
The rest of the scripts in the `scripts` folder handle various other optional preprocessing tasks, for example creating error maps from comparing model output and ground truth delineations, combining gg3 and gg4 labels from a set of delineations, simplifying delineations to foreground/background by binarizing labels and more. 

The only non-optional script, other than the three mentioned above, are the `process_new_delineations.py` and `process_old_delineations.py` scripts. These read delineations from nrrd files in the given data and save them as nii-files. The reason this task is split into two scripts is because the newest patch of patients in the input data had a different structure of delineation files where delineations of different Gleason patterns were saved into individual .nrrd files. The `new` script combines these and saves the result as a .nii.

Lastly, a folder called `bash_scripts` is included containing the bash scripts used to perform nnU-Net preprocessing, training and prediction using trained models on the snellius supercomputer.


## Notebooks
The notebooks folder contains notebooks for both Exploratory Data Analysis (EDA) on the data before model training, and notebooks for evaluation using various approaches on the model outputs (comparing to the ground truth delineations).


## Pipeline

Before preprocessing can start, scans must be collected in `data/Scans/all_scans`, and delineations in `data/Regions ground truth/Regions delineations`.

+ Step 1 is to process .nrrd delineations into .nii files using `process_new_delineations.py` and `process_old_delineations.py`.
+ Step 2 is to read the scan and delineation files and create the patient objects, on which preprocessing is also performed by `load_patients.py` with the `-rras` (read raw and save) flag.
+ Step 3 is to format the patient data into the format nnU-Net expects, by calling `load_patients.py` with the `-cnd` flag.

Note: The input data in this project contained some inconsistencies for which the above scripts perform checking. This is mainly some missing delineations and some delinations of the wrong size (size differs from T2 while it should be the same since they are registered to the T2 scans). However a problematic bug has persisted causing the spatial data (in SimpleITK terms, the direction and origin header data) of some delineations to change when loaded and then saved as a .nii, even when they are already converted to a .nii. `load_patients.py` has a verification function if called with the `-vm` flag, that can check either the nnU-Net prepared data, or the raw data. Problematic patient ids are collected and can be put in a `patients_to_remove.txt` file in the `scripts` folder. If `load_patients.py` is called with the `-rm` flag, these patients will be removed from nnU-Net prepared data.


