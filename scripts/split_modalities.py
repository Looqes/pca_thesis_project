import os
import shutil
import read_scans_utils

PATH_TO_NNUNET_RAW = "../data/nnUNet_raw"

print("This will take a dataset folder containing all modalities as input images\
       and create new dataset folders containing only T2 along with one other\
       modality (either ADC or perfusion images).")

datasets = os.listdir(PATH_TO_NNUNET_RAW)
print(datasets)
full_datasetname = input("Name of dataset folder with all data: ")
if full_datasetname not in datasets:
    print("dataset not found")
    exit(1)


max_dataset_num = max([int(f[7:10]) for f in os.listdir(PATH_TO_NNUNET_RAW) if "Dataset" in f])

# The number ids of the two new datasets that will be created
new_dataset_nums = (
    (str(max_dataset_num + 1)).zfill(3),
    (str(max_dataset_num + 2)).zfill(3)
)

adc_dataset_path = f"{PATH_TO_NNUNET_RAW}/Dataset{new_dataset_nums[0]}_pcaadc"
perfusion_dataset_path = f"{PATH_TO_NNUNET_RAW}/Dataset{new_dataset_nums[1]}_pcaperf"

shutil.copytree(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}",
                adc_dataset_path)
shutil.copytree(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}",
                perfusion_dataset_path)


# Restructure ADC dataset
#############################################################
for file in os.listdir(f"{adc_dataset_path}/imagesTr"):
    if "0002" in file:
        os.remove(f"{adc_dataset_path}/imagesTr/{file}")
for file in os.listdir(f"{adc_dataset_path}/imagesTs"):
    if "0002" in file:
        os.remove(f"{adc_dataset_path}/imagesTs/{file}")

# Restructure Perfusion dataset
#############################################################
for file in os.listdir(f"{perfusion_dataset_path}/imagesTr"):
    if "0001" in file:
        os.remove(f"{perfusion_dataset_path}/imagesTr/{file}")
for file in os.listdir(f"{perfusion_dataset_path}/imagesTs"):
    if "0001" in file:
        os.remove(f"{perfusion_dataset_path}/imagesTs/{file}")

# rename perfusion files to "0001"
for file in os.listdir(f"{perfusion_dataset_path}/imagesTr"):
    if "0002" in file:
        new_filename = file.replace("0002", "0001")
        os.rename(f"{perfusion_dataset_path}/imagesTs/{file}",
                  f"{perfusion_dataset_path}/imagesTr/{new_filename}")
for file in os.listdir(f"{perfusion_dataset_path}/imagesTs"):
    if "0002" in file:
        new_filename = file.replace("0002", "0001")
        os.rename(f"{perfusion_dataset_path}/imagesTs/{file}",
                  f"{perfusion_dataset_path}/imagesTs/{new_filename}")

