import numpy as np
import math
from scipy.optimize import least_squares

"""
CONSTANTS
"""
ANCHOR_POINTS = [(0,0), (10,0), (10,10), (0,10)]    #Coordinates of anchor points (m)
ROUND_DIGITS = 5                                    #Number of digits to round to

"""
GLOBAL VARS
"""
prev_tag = [-1,-1]    # Keep track of previous tag position to calculate angle

"""
HELPER FUNCTIONS
"""

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
    points = [(round(res.x[0], ROUND_DIGITS), round(res.x[1], ROUND_DIGITS))]

    return points[0]
    
def get_tag_direction(tag):
    return math.degrees(math.atan((prev_tag[1] - tag[1])/(prev_tag[0] - tag[0])))

"""

FUNCTIONS

"""

def get_tag_info(distances):
    """
    Calculates tag position and degrees from previous position based on anchor point distances
    `distances`(list): Distance from each anchor point to the tag (m)
    
    Returns: ((x, y), deg)
    """
    tag = get_tag_coords(ANCHOR_POINTS, distances)
    deg = get_tag_direction(tag)
    prev_tag = tag  #update prev to new tag data
    return [tag, deg]

# Sample Usage
# distances = [0, 10, 10*math.sqrt(2), 10] # For a tag at position (0,0)
# print(get_tag_info(distances))