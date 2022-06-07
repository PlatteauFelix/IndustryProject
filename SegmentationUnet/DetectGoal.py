from typing_extensions import Self
from tensorflow import keras
import tensorflow as tf
from skimage.transform import resize
import numpy as np
import matplotlib.pyplot as plt 
import cv2
from shapely.geometry import Point, Polygon



class FindGoalCoords():
    def __init__(self,frame,path):
        self.frame = frame
        self.path = path
        self.poly = self.run()

    def loadModel(self):
        model = keras.models.load_model(f"{self.path}" + r"\Unet_Segment_Model.h5")
        return model

    def loadImg(self):
        img = self.frame
        img = keras.utils.img_to_array(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    def proccesImg(self,img):
        processedImg = resize(img, (256,256), mode = 'constant', preserve_range = True)
        processedImg = processedImg/255.0
        return processedImg

    def predict(self,img,model):
        predictedImg = model.predict(img.reshape(1,256,256,1))
        predictedImg = predictedImg.reshape(256,256,1)
        predictedImg = resize(predictedImg, (1080,1920,1), mode = 'constant', preserve_range = True)
        predictedImg = predictedImg - predictedImg.min() 
        predictedImg = predictedImg / predictedImg.max() * 255
        predictedImg = predictedImg.astype(np.uint8)
        return predictedImg

    def CreatePoly(self,img):
        ret,img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if len(contours) > 1:
            return ""
        else:
            contours = np.squeeze(contours)
            poly = Polygon(contours)
            return poly


    def run(self):
        model = self.loadModel()
        img = self.loadImg()
        img = self.proccesImg(img)
        img = self.predict(img,model)
        return self.CreatePoly(img)

    #----------------Test functions--------------------#
    def show(self,img):
        plt.axis('off')
        plt.imshow(img)
        plt.show()

    def showContours(self,contours):
        img = self.loadImg()
        cv2.drawContours(img, contours, -1, (0, 255, 255), 10)
        plt.axis('off')
        plt.imshow(img)
        plt.show()
    #--------------------------------------------------#


 





