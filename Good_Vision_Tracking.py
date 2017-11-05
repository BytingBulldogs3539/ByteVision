 
import cv2
from PIL import Image
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import StringIO
import time
import numpy as np
from array import *
from enum import Enum
from networktables import NetworkTables
import math
import os
 
 
class Camera(Enum):
        GEAR=0
        SHOOTER=1
 
initCamera = 1
 
boilerHeight = 9.75
 
gearWidth = 10.25
 
videoWidth      = 320
videoHeight     = 240
 
hFocalPointRatio = 1.030
hFocalPoint      = hFocalPointRatio * videoWidth
hFOV             = 49.5
 
vFocalPointRatio = 1.57
vFocalPoint      = vFocalPointRatio * videoHeight
vFOV             = 38.6
 
global cameraLast
cameraLast = None
visualize = False
global avgdist
avgdist = 0
 
#Gear Camera Ranges
MinGearW =10
MinGearASP =.15
MaxGearASP =.5
MaxGearYDIF =5
 
#Shooter Camera Ranges
MinShootW =10
MinShootASP =1.5
MaxShootASP =4.5
MaxShootXDIF = 5
 
 
 
capture=None
nextframe = None
HSV_Low_SHOOTER = np.array([30,90,20])
HSV_High_SHOOTER = np.array([60,255,255])
 
HSV_Low_GEAR = np.array([30,90,20])
HSV_High_GEAR = np.array([60,255,255])
 
 
videoWidth = 320
videoHeight = 240
 
 
 
 
def findContours(camera,frame,blobs):
        retCountours = []
        count = 0
        areas = []
        aspects=[]
        pos = 0 #used for identifing position on the array
       
        contours,_ = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
 
        if camera == Camera.GEAR:
                for c in contours:
                        xc,yc,wc,hc = cv2.boundingRect(c)
                        areas.append(wc*hc)
 
 
 
               
                if(len(contours) > blobs-1):
                        while count < blobs:
                                pos = pos+1
                                max_index = np.argmax(areas)
                                cnt=contours[max_index]
                                areas[max_index] = 0
                                xc,yc,wc,hc = cv2.boundingRect(cnt)
                                if wc/float(hc) > MinGearASP:
                                        if wc/float(hc) < MaxGearASP:
                                                retCountours.append(cnt)
                                                count = count+1
                                if pos >= len(contours):
                                        break
                return retCountours
 
       
        if camera == Camera.SHOOTER:
                for c in contours:
                        xc,yc,wc,hc = cv2.boundingRect(c)
                        areas.append(wc*hc)
 
 
               
                if(len(contours) > blobs-1):
                        while count < blobs:
                                pos = pos+1
                                max_index = np.argmax(areas)
                                cnt=contours[max_index]
                                areas[max_index] = 0
                                xc,yc,wc,hc = cv2.boundingRect(cnt)
                                if wc/hc > MinShootASP:
                                        if wc/hc < MaxShootASP:
                                                retCountours.append(cnt)
                                                count = count+1
                                if pos >= len(contours):
                                        break
                return retCountours
 
def filterContours(camera,contourlist, frame):
        xa = []
        ya = []
        xwa = []
        yha = []
        if camera == Camera.GEAR:
                for c in contourlist:
                        xc,yc,wc,hc = cv2.boundingRect(c)
                        contourlist.remove(c)
                        if wc >= MinGearW:
                                if wc/float(hc) > MinGearASP:
                                        if wc/float(hc) < MaxGearASP:
                                                for o in contourlist:
                                                        x,y,w,h=cv2.boundingRect(o)
                                                        if abs((yc+hc/2)-(y+h/2))< MaxGearYDIF:
                                                                if w >= MinGearW:
                                                                        if w/float(h) > MinGearASP:
                                                                                if w/float(h) < MaxGearASP:
                                                                                        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                                                                                        cv2.rectangle(frame,(xc,yc),(xc+wc,yc+hc),(0,255,0),2)
                                                                                        xa.append(xc)
                                                                                        ya.append(yc)
                                                                                        xwa.append(xc + wc)
                                                                                        yha.append(yc + hc)
                                                                                        xa.append(x)
                                                                                        ya.append(y)
                                                                                        xwa.append(x + w)
                                                                                        yha.append(y + h)
                                                                                        min_x = np.argmin(xa)
                                                                                        min_y = np.argmin(ya)
                                                                                        max_w = np.argmax(xwa)
                                                                                        max_h = np.argmax(yha)
                                                                                                       
                                                                                        return xa[min_x], ya[min_y], xwa[max_w]-xa[min_x], yha[max_h]-ya[min_y]
 
 
        if camera == Camera.SHOOTER:
                for c in contourlist:
                        xc,yc,wc,hc = cv2.boundingRect(c)
                        contourlist.remove(c)
                        if wc > MinShootW:
                                if wc/hc > MinShootASP:
                                        if wc/hc < MaxShootASP:
                                                for o in contourlist:
                                                        x,y,w,h=cv2.boundingRect(o)
                                                        if abs((xc+wc/2)-(x+w/2))<MaxShootXDIF:
                                                                if w >=MinShootW:
                                                                        if w/h > MinShootASP:
                                                                                if w/h < MaxShootASP:
                                                                                        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                                                                                        cv2.rectangle(frame,(xc,yc),(xc+wc,yc+hc),(0,255,0),2)
                                                                                        xa.append(xc)
                                                                                        ya.append(yc)
                                                                                        xwa.append(xc + wc)
                                                                                        yha.append(yc + hc)
                                                                                        xa.append(x)
                                                                                        ya.append(y)
                                                                                        xwa.append(x + w)
                                                                                        yha.append(y + h)
                                                                                        min_x = np.argmin(xa)
                                                                                        min_y = np.argmin(ya)
                                                                                        max_w = np.argmax(xwa)
                                                                                        max_h = np.argmax(yha)
                                                                                                       
                                                                                        return xa[min_x], ya[min_y], xwa[max_w]-xa[min_x], yha[max_h]-ya[min_y]
        return videoWidth/2,0,1,1
 
def processFrame(camera,frame,blobs):
 
 
        global distarray
        global avgdist
 
        count = 0
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if camera == Camera.GEAR:
                mask = cv2.inRange(hsv, HSV_Low_GEAR, HSV_High_GEAR)
        else:
                mask = cv2.inRange(hsv, HSV_Low_SHOOTER, HSV_High_SHOOTER)
        res = cv2.bitwise_and(frame,frame,mask=mask)
        edges = cv2.Canny(res,30,250)
       
 
       
        contours = findContours(camera,edges,blobs)
 
        x,y,w,h = filterContours(camera,contours,res)
 
        TargetFound = False
 
        angle = math.atan((x+w/2-videoWidth/2)/hFocalPoint)
 
        distance = 0
        global  cameraLast
        if camera != cameraLast:
                distarray=array('d',[0,0])
 
        if camera == Camera.GEAR:
                distance = gearWidth*hFocalPoint/w
        else:
                distance = boilerHeight*vFocalPoint/h
       
        if w != 1:
                if h !=1:
                        TargetFound = True
 
                        distarray.pop(0)
                        distarray.append(distance)
                        for f in distarray:
                                avgdist = avgdist+f
                        avgdist = avgdist/2
                       
                        table.putNumber('Angle',angle)
                        table.putNumber('Distance',avgdist)
        if visualize == True:
                cv2.imshow('Edges',edges)
                cv2.rectangle(res,(x,y),(x+w,y+h),(255,0,0),2)
                cv2.imshow('Res',res)
                cv2.imshow('fun',frame)
        cameraLast = camera
 
 
def StartVision():
        global distarray
        distarray=array('d',[0,0])
        while True:     ##MAIN LOOP
                global table
                table = NetworkTables.getTable("Vision")
                camera = table.getNumber('camera')
               
                _,frame = Shooter.read()
                if camera == 0:
                        _,frame = Gear.read()
                        processFrame(Camera.GEAR,frame,2)
                else:
                        processFrame(Camera.SHOOTER,frame,2)  
 
               
 
               
                if cv2.waitKey(1) & 0xFF == ord('q'):
                        capture.release()
                        cv2.destroyAllWindows()
                        break
 
 
 
 
 
 
class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                try:
                    rc,img = Gear.read()
                    imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                    jpg = Image.fromarray(imgRGB)
                    tmpFile = StringIO.StringIO()
                    jpg.save(tmpFile,'JPEG')
                    self.wfile.write("--jpgboundary")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(tmpFile.len))
                    self.end_headers()
                    jpg.save(self.wfile,'JPEG')
                    time.sleep(0.005)
                except KeyboardInterrupt:
                    break
            return
        if self.path.endswith('.html'):
            self.send_response(1)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="http://192.168.2.21:3539/cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return
 
 
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
 
def main():
        global Gear
        global Shooter
        while True:
               NWT = False
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
                       NWT = True
               except:
                       pass
 
        counter = 0
        while True:
                Gear = 0
                Shooter = 0
                Gear = cv2.VideoCapture(0)
                Gear.set(3,videoWidth)
                Gear.set(4,videoHeight)
                Shooter = cv2.VideoCapture(1)
                Shooter.set(3,videoWidth)
                Shooter.set(4,videoHeight)
 
                ret, frame = Gear.read()
                ret2, frame2 = Shooter.read()
                print ret,ret2
                if ret | ret2 == False:
                    counter = counter +1
                if ret & ret2 == True:
                    Gear = 0
                    Shooter = 0
                    break
 
                if counter >= 30:
                        print('reboot')
                        os.system('reboot')
 
 
        os.system('v4l2-ctl -d 0 --set-ctrl exposure_auto=1')
        os.system('v4l2-ctl -d 1 --set-ctrl exposure_auto=1')
 
        os.system('v4l2-ctl -d 0 --set-ctrl exposure_absolute=1')
        os.system('v4l2-ctl -d 1 --set-ctrl exposure_absolute=1')
 
        os.system('v4l2-ctl -d 0 --set-ctrl brightness=1')
        os.system('v4l2-ctl -d 1 --set-ctrl brightness=1')
 
       
        Gear = cv2.VideoCapture(0)
        Gear.set(3,videoWidth)
        Gear.set(4,videoHeight)
        Shooter = cv2.VideoCapture(1)
        Shooter.set(3,videoWidth)
        Shooter.set(4,videoHeight)
        global img
        try:
                server = ThreadedHTTPServer(('192.168.2.21', 3539), CamHandler)
                print "server started"
                start = threading.Thread(target=StartVision)
                start.start()
                server.serve_forever()
        except KeyboardInterrupt:
                capture.release()
                server.socket.close()
 
if __name__ == '__main__':
    main()
