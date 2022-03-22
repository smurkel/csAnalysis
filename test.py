from pystackreg import StackReg
from Core import *
import Reconstruction
import AnalysisMethods as am
from skimage import transform
import matplotlib.pyplot as plt

imga = 'C:/Users/mgflast/Desktop/imgA.tif'
imgb = 'C:/Users/mgflast/Desktop/imgB.tif'

def RegisterTranslation(imgA, imgB):
    sr = StackReg(StackReg.TRANSLATION)
    transform = sr.register(imgA, imgB)
    return transform

ref = Load(imga)
img = Load(imgb)

sr = StackReg(StackReg.TRANSLATION)
tf = sr.register(ref, img)
print(tf)
skimg_tf = transform.AffineTransform(np.array(tf))
print(skimg_tf)
plt.subplot(1,2,1)
img = transform.warp(img, skimg_tf, preserve_range = True).astype(np.uint16)
print(img)


