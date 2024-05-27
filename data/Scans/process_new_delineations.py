import os
import SimpleITK as sitk
import nrrd
import numpy as np
from collections import defaultdict


# #############################################################################
# For new patient files with delineations
# These do not come in the format of files per Gleason pattern, but
# instead as a single segementation with individual labels. These need to be
# reformatted to the defined format as in patient objects, where the map
# contains 0's for background, 1's for GG3, 2's for GG4 and 3's for Cribriform
# voxels.
# #############################################################################

delineations_path = "./scans231_294/Delineations"
nii_delineations_path = "../Regions Ground Truth/delineations_nifti"

with open("patients_to_not_use.txt") as f:
    patients_to_not_use = set([line.strip() for line in f.readlines() if line != "\n"])

print("The following patients will be skipped: ")
print(patients_to_not_use)

for folder in os.listdir(delineations_path):
    found = False

    patient_id = folder[:10]
    if patient_id in patients_to_not_use:
        print(f"Skipping patient {patient_id}")
        continue

    for file in os.listdir(f"{delineations_path}/{folder}"):
        GG_markers_dict = {
            "GG3": set(),
            "GG4": set(),
            "Cribriform": set()
        }

        if "pGG" in file:
            found = True

            reader = sitk.ImageFileReader()
            reader.SetFileName(f"{delineations_path}/{folder}/{file}")
            reader.LoadPrivateTagsOn()

            raw_delineation = reader.Execute()
            raw_delineation_array = sitk.GetArrayFromImage(raw_delineation)
            output_delineation = np.zeros(raw_delineation_array.shape)

            # Identify which integer markers represent which pattern
            for i in range(6):
                try: 
                    segment_name = reader.GetMetaData(f"Segment{i}_Name")

                    if "GG3" in segment_name:
                        GG_markers_dict["GG3"].add(reader.GetMetaData(f"Segment{i}_LabelValue"))
                    if "GG4" in segment_name:
                        GG_markers_dict["GG4"].add(reader.GetMetaData(f"Segment{i}_LabelValue"))
                    if "Cribriform" in segment_name:
                        GG_markers_dict["Cribriform"].add(reader.GetMetaData(f"Segment{i}_LabelValue"))
                except:
                    break
            
            # Constructing the final delineation by relabelling markers
            # 1 for GG3, 2 for GG4 and 3 for Cribriform
            for pattern in GG_markers_dict:
                if pattern == "GG3":
                    new_marker = 1
                elif pattern == "GG4":
                    new_marker = 2
                elif pattern == "Cribriform":
                    new_marker = 3
                for marker in GG_markers_dict[pattern]:
                    output_delineation[raw_delineation_array == int(marker)] = new_marker
                        
            delineated_slices_gg3 = [i for i, slice 
                                 in enumerate(np.rollaxis(output_delineation, axis=0))
                                 if 1 in slice]
            delineated_slices_gg4 = [i for i, slice 
                                 in enumerate(np.rollaxis(output_delineation, axis=0))
                                 if 2 in slice]
            delineated_slices_crib = [i for i, slice 
                                 in enumerate(np.rollaxis(output_delineation, axis=0))
                                 if 3 in slice]

            combined_delineation = sitk.GetImageFromArray(output_delineation)
            combined_delineation.SetSpacing(raw_delineation.GetSpacing())
            combined_delineation.SetOrigin(raw_delineation.GetOrigin())
            combined_delineation.SetDirection(raw_delineation.GetDirection())

            sitk.WriteImage(combined_delineation,
                            f"{nii_delineations_path}/{patient_id}_combined_delineation.nii.gz")

            break
 
    if found == False:
        print(f"{folder} does not have a pGG file")