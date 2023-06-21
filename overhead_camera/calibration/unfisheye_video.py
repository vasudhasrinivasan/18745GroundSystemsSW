#referred to https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_calib3d/py_calibration/py_calibration.html
#callibration code using checkerboard set up from tutorial above.
 
#Attempt at improving quality of un-fisheyed video - used in Final Demo
#Current code computed callibration coefficients

#code currently opens video port, captures a frame at 480p, and processed according to 
#steps in tutorial linked above in order to obtain coefficients for 
#future processing. Coefficiencts x-map, y-map, and roi are stored in respective files
#to be referenced in un-fisheyeing code for live unwarping. 

import numpy as np
import cv2
import glob

#dimension of checkerboard image used for callibration
DIM = (6,9)

#define video parameters
video_path = "/dev/video0"
video = cv2.VideoCapture(video_path)
if not video.isOpened():
    raise ValueError("error opening video")
length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = video.get(cv2.CAP_PROP_FPS)

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((DIM[0]*DIM[1],3), np.float32)
objp[:,:2] = np.mgrid[0:DIM[0],0:DIM[1]].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

# Read video frame.
#default captured frame is 480p
ret, img = video.read()
if not ret:
    raise RuntimeError('Error fetching frame')

cv2.imwrite('rawresult.png',img)

gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
# Find the chess board corners
ret, corners = cv2.findChessboardCorners(gray, DIM,None)
# If found, add object points, image points (after refining them)
if ret == True:
    objpoints.append(objp)

    cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
    imgpoints.append(corners)

    # Draw and display the corners
    cv2.drawChessboardCorners(img, DIM, corners,ret)
    cv2.imshow('img',img)
    cv2.waitKey(500)

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
    h,  w = img.shape[:2]
    newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

    # undistort
    mapx,mapy = cv2.initUndistortRectifyMap(mtx,dist,None,newcameramtx,(w,h),5)
    dst = cv2.remap(img,mapx,mapy,cv2.INTER_LINEAR)

    # crop the image
    x,y,w,h = roi
    dst = dst[y:y+h, x:x+w]
    cv2.imwrite('calibresult.png',dst)

    #save coefficients
    np.save("calibration_mapx.npy", mapx, allow_pickle=True, fix_imports=True)
    np.save("calibration_mapy.npy", mapy, allow_pickle=True, fix_imports=True)
    np.save("calibration_roi.npy", roi, allow_pickle=True, fix_imports=True)

    cv2.destroyAllWindows()