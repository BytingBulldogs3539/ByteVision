import time
import logging
from networktables import NetworkTables
import cv2
import numpy as np
import math
from array import *
import os


logging.basicConfig(level=logging.DEBUG)

video = 1
initCamera = 0
table = None
count = 0
counting = 0
setchangedcamera = 0

boilerHeight = 9.75
#boilerHeight = 10

gearWidth = 10.25

videoWidth      = 320
videoHeight     = 240

hFocalPointRatio = 1.030 #1.029 1.08511
hFocalPoint      = hFocalPointRatio * videoWidth
hFOV             = 49.5

vFocalPointRatio = 1.57 #1.26362 1.42926
vFocalPoint      = vFocalPointRatio * videoHeight
vFOV             = 38.6


#HSV_Low = np.array([50,0,134]) #[50,0,185]   correct 60,83,26
#HSV_High = np.array([107,255,255]) #[85,255,255]   correct  90,255,255

HSV_Low = np.array([60,33,65]) #[50,0,185]   correct 60,83,26
HSV_High = np.array([1005,255,255]) #[85,255,255]   correct  90,255,255


NWT = False

while True:
        time.sleep(.5)
        print NetworkTables.getRemoteAddress()
        if NetworkTables.getRemoteAddress() == None:
                        NWT = False
        else:
                NWT = True
        if NWT == True:
                break
        try:
                NetworkTables.shutdown()
                NetworkTables.initialize(server='10.35.39.2') #roboRIO-3538-FRC.local
                table = NetworkTables.getTable("Vision")
                table.putNumber('camera', initCamera)
                table.putNumberArray('HSV_High',HSV_High)
                table.putNumberArray('HSV_Low',HSV_Low)
                HSV_High = table.getNumberArray('HSVHighArray')
                HSV_Low = table.getNumberArray('HSVLowArray')
                NWT = True
        except:
                pass

Camcounter = 0


videoWidth      = 320
videoHeight     = 240

counter = 0

while True:
    vid = 0
    vidGear = 0
    vid = cv2.VideoCapture(1)
    vid.set(3,videoWidth)
    vid.set(4,videoHeight)
    vid.set(5,30) #FPS
    vid.set(10,0) #Brightness
    #vid.set(11, 1) #Contrast

    vidGear = cv2.VideoCapture(0)

    vidGear.set(3,videoWidth)
    vidGear.set(4,videoHeight)
    vidGear.set(5,30) #FPS
    vidGear.set(10,0) #Brightness
    ret, frame = vid.read()
    ret2, frame2 = vidGear.read()
    print ret,ret2
    if ret | ret2 == False:
            counter = counter +1
    if ret & ret2 == True:
            vid = 0
            vidGear = 0
            break

    if counter >= 30:
        print('reboot')
        os.system('reboot')

vid = cv2.VideoCapture(1)
vid.set(3,videoWidth)
vid.set(4,videoHeight)
vid.set(5,30) #FPS
vid.set(10,0) #Brightness
#vid.set(11, 1) #Contrast

vidGear = cv2.VideoCapture(0)

vidGear.set(3,videoWidth)
vidGear.set(4,videoHeight)
vidGear.set(5,30) #FPS
vidGear.set(10,0) #Brightness

cameralast = 1





def findContours(frame, blobs):
        contours, dummy = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        retCountours = []
        if len(contours) > blobs-1:
                count = 0
                areas = [cv2.contourArea(c) for c in contours]
                initCamera
                while count < blobs:
                        max_index = np.argmax(areas)
                        cnt=contours[max_index]
                        areas[max_index] = 0
                        retCountours.append(cnt)
                        count = count+1
       
        return retCountours

def calcMass(contours):
        if(len(contours) > 0):
                x = []
                y = []
                xw = []
                yh = []
                for c in contours:
                        xc,yc,wc,hc = cv2.boundingRect(c)
                        x.append(xc)
                        y.append(yc)
                        xw.append(xc + wc)
                        yh.append(yc + hc)

                min_x = np.argmin(x)
                min_y = np.argmin(y)
                max_w = np.argmax(xw)
                max_h = np.argmax(yh)

                return x[min_x], y[min_y], xw[max_w]-x[min_x], yh[max_h]-y[min_y]

        return videoWidth/2,0,1,1
        
def processFrame(frame, camera):
       # frame = cv2.GaussianBlur(frame, (7,7), 0)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, HSV_Low, HSV_High)
        
        res = cv2.bitwise_and(frame,frame,mask=mask)

        kernel = np.ones((3,3),np.uint8)
        res = cv2.morphologyEx(res,cv2.MORPH_OPEN, kernel)

        #res = cv2.dilate(res, (7,7), iterations = 0)

        contours = findContours(mask, 2)
        table.putNumberArray('HSV_High',HSV_High)
        table.putNumberArray('HSV_Low',HSV_Low)
        x=y=h=w= angle = distance = 0
        
        x,y,w,h = calcMass(contours)
        angle = math.atan((x+w/2-videoWidth/2)/hFocalPoint)
        if camera == cameralast:
                pass
        else:
                c=array('d',[0,0])
                setchangedcamera = True
        if camera == 0:
                distance = gearWidth*hFocalPoint/w
        else:
                distance = boilerHeight*vFocalPoint/h

        distance = distance / abs(math.cos(angle))
        angle = angle * 180/3.14
        
        if video == 1:
                cv2.rectangle(res,(w/2+x,0),(w/2+x,videoWidth),(0,255,0),1)
                cv2.rectangle(res,(x,y),(x+w,y+h),(255,0,0),2)
                cv2.imshow('hsv',frame)
                cv2.imshow('fff',res)
        camera = cameralast

   
        return res, angle, distance
        
#def onmouse(k,x,y,s,p):
#        global hsv
#        if k==1:
#                print y,x
#
#cv2.namedWindow("fff")
#cv2.setMouseCallback("fff",onmouse);

c=array('d',[0,0])

#Distance is the sub catagory for Visiontracking for turning Distance
while True:
        count = count + 1
        counting = counting + 1

        ret, frame = vid.read()
        table = NetworkTables.getTable("Vision")
        camera = table.getNumber('camera')
        if camera == 0:
                ret, frame = vidGear.read()

        res, angle, distance = processFrame(frame, camera)
        if setchangedcamera == 1:
                counting = 0
                name = "/home/pi/Desktop/visionpictures/count"+str(count)+".jpg"
                print name 
                cv2.imwrite(name,frame)
        

        
        print (int(distance), round(angle,2))

        
        table.putNumber('Angle',angle)
        #print ret
        c.pop(0)
        c.append(distance)
        h5=0
        for f in c:
                h5 = h5+f
        h5=h5/2
        #print f
        
        table.putNumber('Distance',h5)
        table.putNumber('Counter',count)

        if cv2.waitKey(1) & 0xFF == ord('q'):
                vid.release()
                cv2.destroyAllWindows()
                break
