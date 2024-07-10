# pca_thesis_project
repo for the code for the pca project for the UvA data science master thesis

## scripts

Contains all scripts made for the project. Mainly for data manipulation and preprocessing/preparing the data for use by nnU-Net. Most of the functionality for data manipulation is contained in the '''read_scans_utils.py''' script. This script contains code for reading scans, file conversion, patient characteristics calculation (e.g. for Gleason Grade group) and more.

The functions in this script are called by '''load_patients.py'''.
This script calls functions from '''read_scans_utils.py''' to perform various tasks. Flags can be passed to this script to determine what tasks it has to perform. Which flags, and what functionalities are associated with them, are shown to the user when calling the script *without* flags.
