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


max_dataset_num = max([int(f[7:10]) for f in os.listdir(PATH_TO_NNUNET_RAW)])

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

exit(0)

os.makedirs(f"{adc_dataset_path}/imagesTr")
os.makedirs(f"{perfusion_dataset_path}/imagesTr")

# Paths to all modality files, including those in test set of the full dataset
t2_files_paths = [f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTr/{f}"
                    for f in os.listdir(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTr")
                    if "0000" in f] \
                + \
                    [f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTs/{f}"
                    for f in os.listdir(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTs")
                    if "0000" in f]

adc_files_paths = [f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTr/{f}"
                    for f in os.listdir(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTr")
                    if "0001" in f] \
                + \
                    [f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTs/{f}"
                    for f in os.listdir(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTs")
                    if "0001" in f]

perfusion_files_paths = [f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTr/{f}"
                    for f in os.listdir(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTr")
                    if "0002" in f] \
                + \
                    [f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTs/{f}"
                    for f in os.listdir(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/imagesTs")
                    if "0002" in f]

# Copy t2 files to both sets
for path in t2_files_paths:
    print(f"Copying\n{path} ...\n\n")
    shutil.copy(path,
                f"{adc_dataset_path}/imagesTr")
    shutil.copy(path,
                f"{perfusion_dataset_path}/imagesTr")
    
# Copy adc files to adc set
for path in adc_files_paths:
    print(f"Copying\n{path} ...\n\n")
    shutil.copy(path,
                f"{adc_dataset_path}/imagesTr")
    
# Copy perfusion files to perfusion set
# Rename them "0002" -> "0001"
for path in perfusion_files_paths:
    print(f"Copying perfusion file \n{path}...\n\n")
    shutil.copy(path,
                f"{perfusion_dataset_path}/imagesTr")
for file in os.listdir(f"{perfusion_dataset_path}/imagesTr"):
    if "0002" in file:
        new_name = file.replace("0002", "0001")
        os.rename(f"{perfusion_dataset_path}/imagesTr/{file}",
                    f"{perfusion_dataset_path}/imagesTr/{new_name}")

# ../data/nnUNet_raw/Dataset003_pcaperf/ImagesTR/MARPROCXXX_0002.nii.gz

# Copy full label directory to both sets
shutil.copytree(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/labelsTr",
                f"{adc_dataset_path}/labelsTr")
shutil.copytree(f"{PATH_TO_NNUNET_RAW}/{full_datasetname}/labelsTr",
                f"{perfusion_dataset_path}/labelsTr")

read_scans_utils.create_datasetjson(adc_dataset_path,
                                    ["AxialT2", "ADC"])
read_scans_utils.create_datasetjson(perfusion_dataset_path,
                                    ["AxialT2", "Perfusion"])

