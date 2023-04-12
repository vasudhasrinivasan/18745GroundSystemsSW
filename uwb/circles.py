import numpy as np
import math
from scipy.optimize import least_squares
import time
import random

ANCHOR_POINTS = [(0,0), (10,0), (10,10), (0,10)]    #Coordinates of anchor points (m)

prev_tag = [0,0]

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def get_distances(tag, anchor_points):

  distances = []
  distances.append(calculate_distance(tag[0], tag[1], anchor_points[0][0], anchor_points[0][1]))
  distances.append(calculate_distance(tag[0], tag[1], anchor_points[1][0], anchor_points[1][1]))
  distances.append(calculate_distance(tag[0], tag[1], anchor_points[2][0], anchor_points[2][1]))
  distances.append(calculate_distance(tag[0], tag[1], anchor_points[3][0], anchor_points[3][1]))
  return distances

def residual(x, circles):
    err = []
    for (x0, y0), r in circles:
        err.append((x[0] - x0)**2 + (x[1] - y0)**2 - r**2)
    return err

def get_tag_coords(anchor_points, distances):
    # Define four circles
    circles = [(anchor_points[0], distances[0]), (anchor_points[1], distances[1]), (anchor_points[2], distances[2]), (anchor_points[3], distances[3])]

    # Find the intersection points using least squares method
    res = least_squares(residual, [0, 0], args=(circles,))
    points = [(res.x[0], res.x[1])]

    return points[0]
    
def get_tag_direction(tag):
    return math.degrees(math.atan((prev_tag[1] - tag[1])/(prev_tag[0] - tag[0])))

def get_tag_info(distances):
    tag = get_tag_coords(ANCHOR_POINTS, distances)
    deg = get_tag_direction(tag)
    prev_tag = tag  #update prev to new tag data
    return [tag, deg]


#Test
test_tag = [1.0, 1.0]
while(1):
    test_tag[0] += random.random()
    test_tag[1] += random.random()
    distances = get_distances(test_tag, ANCHOR_POINTS)
    tag_info = get_tag_info(distances)
    print(f"Actual:[{test_tag}, Calculated:{tag_info}]")

    time.sleep(1)

