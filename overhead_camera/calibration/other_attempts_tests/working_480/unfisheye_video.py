#referred to https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_calib3d/py_calibration/py_calibration.html
#Initial attempt at improving quality of un-fisheyed video by setting up to use 480p. 
#Current code computed callibration coefficients

#code currently opens video port, captures a frame, and processed according to 
#steps in tutorial linked above in order to obtain coefficients for 
#future processing. Coefficiencts x-map, y-map, and roi are stored in respective files
#to be referenced in un-fisheyeing code for live unwarping. 

import numpy as np
import cv2
import glob


DIM = (6,9)

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
ret, img = video.read()
if not ret:
    raise RuntimeError('Error fetching frame')
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
    #cv2.imshow('img2', dst)
    cv2.imwrite('calibresult.png',dst)

    np.save("calibration_mapx.npy", mapx, allow_pickle=True, fix_imports=True)
    np.save("calibration_mapy.npy", mapy, allow_pickle=True, fix_imports=True)
    np.save("calibration_roi.npy", roi, allow_pickle=True, fix_imports=True)
    # np.savetxt("calibration_mapx.txt", mapx, fmt='%.18e', delimiter=' ', newline='\n', header='', footer='', comments='# ', encoding=None)
    # np.savetxt("calibration_mapy.txt", mapy, fmt='%.18e', delimiter=' ', newline='\n', header='', footer='', comments='# ', encoding=None)
    # count = 1
    # while True:
    #     # Restart video on last frame.
    #     if count == length:
    #         count = 0
    #         video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    #     # Read video frame.
    #     ret, img = video.read()
    #     if not ret:
    #         raise RuntimeError('Error fetching frame')

    #     dst = cv2.remap(img,mapx,mapy,cv2.INTER_LINEAR)

    #     # crop the image
    #     x,y,w,h = roi
    #     dst = dst[y:y+h, x:x+w]

    #     cv2.imshow('img2', dst)
    #     cv2.imwrite('result.png',dst)


    #     count += 1

    cv2.destroyAllWindows()