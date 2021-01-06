import numpy as np
import cv2

def load_image(path, mode):
    img = cv2.imread(path)
    # apply thresholding before greyscale to keep everything non-white
    if(mode):
        img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1]

def extract(img, eps):
    points = np.column_stack(np.where(img.transpose() != 0))
    # approximate polygon
    return np.squeeze(cv2.approxPolyDP(points, eps, True))
