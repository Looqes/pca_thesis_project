
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
            if "GG3" in delineation[0]:
                self.add_gg3_delineation(delineation[1][0])
            elif "GG4" in delineation:
                self.add_gg4_delineation(delineation[1][0])
            elif "Cribriform" in delineation:
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
    
        


        

    
    # def plot_img(self, kind):
    #     plt.imshow(np.asanyarray(patient7.adcmap.dataobj[:, :, 0]))
        



    