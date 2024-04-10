
import numpy as np
import nilearn.image as ni_im
from nibabel.spatialimages import SpatialFirstSlicer
import nibabel as nb


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
        print(delineated_slices)
        slice_numbers = list(set(delineated_slices["gg3"]) |
                             set(delineated_slices["gg4"]) |
                             set(delineated_slices["cribriform"]))
        print(slice_numbers)

        print(self.axialt2.shape)

        print(SpatialFirstSlicer(self.axialt2)[:, :, slice_numbers].shape)

        # self.model_data = {"axialt2":      SpatialFirstSlicer(self.axialt2)     [:, :, slice_numbers],
        #                    "adcmap":       SpatialFirstSlicer(self.adcmap)      [:, :, slice_numbers],
        #                    "perfusionmap": SpatialFirstSlicer(self.perfusionmap)[:, :, slice_numbers],
        #                    "region_delineation": nb.Nifti1Image(self.region_delineation[:, :, slice_numbers],
        #                                                         self.model_data["axialt2"].affine)
                        #    }
        



        # t2_slices = [self.axialt2[:, :, i] for i in slice_numbers]
        # adc_slices = [self.adcmap[:, :, i] for i in slice_numbers]
        # perfusion_slices = [self.perfusionmap[:, :, i] for i in slice_numbers]

        # print(t2_slices.shape)
        # print(adc_slices.shape)
        # print(perfusion_slices.shape)
