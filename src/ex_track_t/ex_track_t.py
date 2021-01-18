import numpy as np
import cv2
from math import sqrt, pow
from scipy import interpolate

def load_image(path, mode):
    img = cv2.imread(path)
    # apply thresholding before greyscale to keep everything non-white
    if(mode):
        img = cv2.threshold(img, 230, 255, cv2.THRESH_BINARY)[1]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]
    return img

def contours(img):
    contours, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    outside = contours[0]

    max_area = cv2.contourArea(outside)
    for cont in contours:
        if cv2.contourArea(cont) > max_area:
            outside = cont
            max_area = cv2.contourArea(cont)

    min_area = max_area

    inside = contours[0]
    for cont in contours:
        # 0.5 boundaries to avoid single pixel/very small contours
        if cv2.contourArea(cont) < min_area and cv2.contourArea(cont) > 0.5 * max_area:
            inside = cont
            min_area = cv2.contourArea(cont)
    outside = np.squeeze(outside)
    inside = np.squeeze(inside)
    return outside, inside

def middle_lane(outside, inside):
    """
    compute the middle lane from the boundaries as mean of the closest point
    from both boundaries
    """
    def avg(q1, q2):
        return [((q1[0] + q2[0]) / 2), ((q1[1] + q2[1]) / 2)]

    def dist(q1, q2):
        return sqrt(pow(q1[0] - q2[0], 2) + pow(q1[1] - q2[1], 2))

    def closest_index(q, list_to):
        return min(range(len(list_to)), key = lambda i : dist(q, list_to[i]))

    middle = []
    for out in outside:
        closest = inside[closest_index(out, inside)]
        middle.append(avg(out, closest))
    return np.array(middle)

def simplify(points, max_points):
    if(len(points) > max_points):
        # generate enough non repeated numbers
        to_remove = np.random.choice(len(points) - 1, size = len(points) - max_points, replace=False)
        # remove from top to avoid out of rance
        to_remove = -np.sort(-to_remove)
        points = np.delete(points, to_remove, 0)
    return points
