


class Patient:
    def __init__(self, id):
        self.id = id
        self.axialt2 = None
        self.adcmap = None
        self.perfusionmap = None

    # Set axial (also called transversal sometimes) scan image
    def set_axialt2(self, axialt2_img):
        self.axialt2 = axialt2_img

    def set_adcdwi(self, adcdwi):
        self.adcmap = adcdwi

    def set_perfusionmap(self, perfusionmap):
        self.perfusionmap = perfusionmap

    
    # def plot_img(self, kind):
    #     plt.imshow(np.asanyarray(patient7.adcmap.dataobj[:, :, 0]))
        



    