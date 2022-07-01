
import numpy as np
import pandas as pd
from matplotlib import pylab as plt
import cv2
from keras.models import load_model
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1"


def predicted_num(filepath):
    image =cv2.imread(filepath,cv2.IMREAD_GRAYSCALE)
    image = image.reshape(1,784)
    image = image.astype('float32')/255
    mymodel =  load_model('/home/imr/users/liweihao/testweb/models/mnist_model.h5')

    predict = mymodel.predict(image)
    predict = np.argmax(predict)  # 取最大值的位置

    return predict