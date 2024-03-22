


class Patient:
    def __init__(self, id):
        self.id = id
        self.axialt2 = None
        self.adcmap = None
        self.perfusionmap = None
        # self.region_delineation = defaultdict()

    # Set axial (also called transversal sometimes) scan image
    def set_axialt2(self, axialt2_img):
        self.axialt2 = axialt2_img

    def set_adcdwi(self, adcdwi):
        self.adcmap = adcdwi

    def set_perfusionmap(self, perfusionmap):
        self.perfusionmap = perfusionmap

    def get_axialt2_image_array(self):
        return np.asarray(self.axialt2.dataobj)
    
    def get_adc_image_array(self):
        return np.asarray(self.adcmap.dataobj)
    
    def get_perfusion_image_array(self):
        return np.asarray(self.perfusionmap.dataobj)
        

    
    # def plot_img(self, kind):
    #     plt.imshow(np.asanyarray(patient7.adcmap.dataobj[:, :, 0]))
        



    