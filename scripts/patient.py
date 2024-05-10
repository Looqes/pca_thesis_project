
import numpy as np
import nilearn.image as ni_im
from nibabel.spatialimages import SpatialFirstSlicer
import nibabel as nb
import os
import pickle


class Patient:
    # Each of the image fields are expected to contain Nifti1Image objects with
    # the respective images
    def __init__(self, id):
        self.id = id

        self.axialt2 = None
        self.adcmap = None
        self.perfusionmap = None
        # The region delineation is expected to be a Nifti1Image containing data
        # that is registered to the patients' axialt2, and is thus of the same shape
        self.region_delineation = None
        
        # Contains the data with ground-truth matched slices of the images (see extract_slice_tuples)
        self.model_data = dict()

    # Set axial (also called transversal sometimes) scan image
    def set_axialt2(self, axialt2_img):
        self.axialt2 = axialt2_img
        self.region_delineation = np.zeros(axialt2_img.shape)

    def set_adcdwi(self, adcdwi):
        self.adcmap = adcdwi

    def set_perfusionmap(self, perfusionmap):
        self.perfusionmap = perfusionmap

    def set_delineation(self, delineation):
        self.region_delineation = delineation
        


    def get_axialt2_image_array(self):
        return np.asarray(self.axialt2.get_fdata())
    
    def get_adc_image_array(self):
        return np.asarray(self.adcmap.get_fdata())
    
    def get_perfusion_image_array(self):
        return np.asarray(self.perfusionmap.get_fdata())
    

    def get_patient_delineation_slices(self):
        delineated_slices_gg3 = []
        delineated_slices_gg4 = []
        delineated_slices_Cribriform = []

        for i, slice in enumerate(np.rollaxis(self.region_delineation.get_fdata(), axis = 2)):
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

    
    # Extract only the slices (for each delineation) that have a ground
    # truth associated with them in the region delineation
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

        delineation_subimg = nb.Nifti1Image(self.region_delineation.get_fdata()[:, :, slice_numbers], 
                                            self.region_delineation.affine)

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


    def load_patient_from_pkl(patient_id, path=None):
        if path == None:
            path = f"../data/pkl_preprocessed/{patient_id}.pkl"

        with open(path, 'rb') as input:
            patient = pickle.load(input)
                
        return patient
        

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