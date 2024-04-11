
import numpy as np
import nilearn.image as ni_im
from nibabel.spatialimages import SpatialFirstSlicer
import nibabel as nb
import os
import pickle


class Patient:
    def __init__(self, id):
        self.id = id

        self.axialt2 = None
        self.adcmap = None
        self.perfusionmap = None
        self.region_delineation = None
        
        self.model_data = dict()

    # Set axial (also called transversal sometimes) scan image
    def set_axialt2(self, axialt2_img):
        self.axialt2 = axialt2_img
        self.region_delineation = np.zeros(axialt2_img.shape)

    def set_adcdwi(self, adcdwi):
        self.adcmap = adcdwi

    def set_perfusionmap(self, perfusionmap):
        self.perfusionmap = perfusionmap

    # Add delineations
    def add_delineations(self, delineations):
        for delineation in delineations:
            # print(delineation[0])
            if "GG3" in delineation[0]:
                # print("Adding GG3 delineation...")
                self.add_gg3_delineation(delineation[1][0])
            elif "GG4" in delineation[0]:
                # print("Adding GG4 delineation...")
                self.add_gg4_delineation(delineation[1][0])
            elif "Cribriform" in delineation[0]:
                # print("Adding Cribriform delineation...")
                self.add_cribriform_delineation(delineation[1][0])

    # Function to add a GG3 delineation map to the total delineation
    # map of this patient. All non-zero values in the delineation will
    # map a 1 to the total delineation map of the patient on that same
    # position
    # 1 will signify a voxel being classified as GG3
    def add_gg3_delineation(self, delineation):
        self.region_delineation[delineation != 0] = 1

    # gg4 voxels will have value 2
    def add_gg4_delineation(self, delineation):
        self.region_delineation[delineation != 0] = 2

    # Cribriform voxels will have value 3
    def add_cribriform_delineation(self, delineation):
        self.region_delineation[delineation != 0] = 3


    def get_axialt2_image_array(self):
        return np.asarray(self.axialt2.dataobj)
    
    def get_adc_image_array(self):
        return np.asarray(self.adcmap.dataobj)
    
    def get_perfusion_image_array(self):
        return np.asarray(self.perfusionmap.dataobj)
    

    def get_patient_delineation_slices(self):
        delineated_slices_gg3 = []
        delineated_slices_gg4 = []
        delineated_slices_Cribriform = []

        for i, slice in enumerate(np.rollaxis(self.region_delineation, 2)):
            if 1 in slice:
                delineated_slices_gg3.append(i)
            if 2 in slice:
                delineated_slices_gg4.append(i)
            if 3 in slice:
                delineated_slices_Cribriform.append(i)

        return {
            "gg3": delineated_slices_gg3,
            "gg4": delineated_slices_gg4,
            "cribriform": delineated_slices_Cribriform
        }


    # Display function to visualize which slices of patient have delineations for
    # the different Gleason pattern types
    def show_patient_delineation_slices(self):
        if not self:
            print("Patient not found...")
            return

        delineated_slices = self.get_patient_delineation_slices()

        if any([delineated_slices["gg3"] != [],
                delineated_slices["gg4"] != [],
                delineated_slices["cribriform"] != []]):
            print("Patient ", self.id, "has the following delineated GG tissues in the listed slices:")
            delineated_slices["gg3"] != [] and print("GG3: ", delineated_slices["gg3"])
            delineated_slices["gg4"] != [] and print("GG4: ", delineated_slices["gg4"])
            delineated_slices["cribriform"] != [] and print("Cribriform: ", delineated_slices["cribriform"])
        else:
            print("Patient has no registered delineations")


    # Function to scale the smaller DWI images to the shape of the t2 image of the patient to make
    # the shape of the patient imaging modalities consistent
    def scale_dwis_to_t2(self):
        if self.adcmap == None or self.perfusionmap == None or self.axialt2 == None:
            print(self.id, ": Missing data")
        else:
            self.adcmap = \
                ni_im.resample_to_img(self.adcmap, self.axialt2)
            self.perfusionmap = \
                ni_im.resample_to_img(self.perfusionmap, self.axialt2)
    
    # Check if patient DWI's are already reshaped
    def dwis_reshaped(self):
        return self.axialt2.shape == \
               self.adcmap.shape == \
               self.perfusionmap.shape

            
    def extract_slice_tuples(self):
        if not self.dwis_reshaped():
            print(self.id, "DWI's are not reshaped")
            return
        
        delineated_slices = self.get_patient_delineation_slices()
        slice_numbers = sorted(list(set(delineated_slices["gg3"]) |
                                    set(delineated_slices["gg4"]) |
                                    set(delineated_slices["cribriform"])))

        # Slicing
        t2_affine = self.axialt2.affine
        t2_slices = self.axialt2.get_fdata()[:, :, slice_numbers]
        t2_subimg = nb.Nifti1Image(t2_slices, t2_affine)

        adc_affine = self.adcmap.affine
        adc_slices = self.adcmap.get_fdata()[:, :, slice_numbers]
        adc_subimg = nb.Nifti1Image(adc_slices, adc_affine)

        perfusion_affine = self.perfusionmap.affine
        perfusion_slices = self.perfusionmap.get_fdata()[:, :, slice_numbers]
        perfusion_subimg = nb.Nifti1Image(perfusion_slices, perfusion_affine)

        delineation_slices = np.flip(self.region_delineation[:, :, slice_numbers], axis = 1)
        # Use t2 affine as the delineation is mapped to the t2
        delineation_subimg = nb.Nifti1Image(delineation_slices, t2_affine)

        self.model_data = {"axialt2":      t2_subimg,
                           "adcmap":       adc_subimg,
                           "perfusionmap": perfusion_subimg,
                           "region_delineation": delineation_subimg
                           }
        

    def write_to_pkl(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Folder '{path}' created successfully.")

        with open(path + "/" + self.id + ".pkl", 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
        

    def write_patient_model_data(self, path):
        path = path + "/" + self.id
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Folder '{path}' created successfully.")
        else:
            print(f"Folder '{path}' already exists.")

        nb.save(self.model_data["axialt2"], path + "/t2.nii")
        nb.save(self.model_data["adcmap"], path + "/adc.nii")
        nb.save(self.model_data["perfusionmap"], path + "/perf.nii")
        nb.save(self.model_data["region_delineation"], path + "/delineation.nii")