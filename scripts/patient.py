
import numpy as np


class Patient:
    def __init__(self, id):
        self.id = id
        self.axialt2 = None
        self.adcmap = None
        self.perfusionmap = None
        self.region_delineation = None

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
    

    def show_patient_delineation_slices(self):
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

        if any([delineated_slices_gg3 != [],
                    delineated_slices_gg4 != [],
                    delineated_slices_Cribriform != []]):
            print("Patient ", self.id, "has the following delineated GG tissues in the listed slices:")
            delineated_slices_gg3 != [] and print("GG3: ", delineated_slices_gg3)
            delineated_slices_gg4 != [] and print("GG4: ", delineated_slices_gg4)
            delineated_slices_Cribriform != [] and print("Cribriform: ", delineated_slices_Cribriform)
        else:
            print("Patient has no registered delineations")


    
        


        

    
    # def plot_img(self, kind):
    #     plt.imshow(np.asanyarray(patient7.adcmap.dataobj[:, :, 0]))
        



    