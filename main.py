# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal 
import  numpy
import device
import cv2, queue, threading, time
import time
from pynput.keyboard import Key, Controller
import math
device_list = device.getDeviceList()
index = 0

for name in device_list:
	print(str(index) + ': ' + name)
	index += 1

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye_tree_eyeglasses.xml')

class VideoCapture:
	def __init__(self, name):
		self.running = True
		self.cap = cv2.VideoCapture(name)
		codec = 0x47504A4D  # MJPG
		self.cap.set(cv2.CAP_PROP_FPS, 30.0)
		#self.cap.set(cv2.CAP_PROP_FOURCC, codec)
		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
		self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)    
			
		self.q = queue.Queue()
		t = threading.Thread(target=self._reader)
		t.daemon = True
		t.start()
		self.ret=True
		
	# read frames as soon as they are available, keeping only most recent one
	def _reader(self):
		while (self.running):
			ret, frame = self.cap.read()
			self.ret = ret
			if ret == False: break
			if not self.q.empty():
				try:
					self.q.get_nowait()   # discard previous (unprocessed) frame
				except queue.Empty:
					pass

			self.q.put(frame)
			#self.q.put(cv2.rotate(frame, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE) )

		self.ret=False

	def read(self):
		if(self.ret==False ):
			return self.ret, ""
		return self.ret, self.q.get()

	def close(self):
		print("close 1")
		self.cap.release()
		print("close 2")
		self.running =False
	def changeCap(self,indx):
		self.cap.release()
		name=indx
		self.cap=cv2.VideoCapture(name)

class Worker(QObject):
	finished = pyqtSignal()
	progress = pyqtSignal(numpy.ndarray,numpy.ndarray)
	
	def changeCap(self,cap,mw):
		self.cap=cap
		self.running = True
		self.ui = mw
	def done(self):
		self.running=False
		self.finished.emit()
	def run(self):
		"""Long-running task."""
		global face_cascade
		global profile_cascade
		while self.running:
			#time.sleep(1)
			ret, img = self.cap.read()
			if(not ret):
				self.running = False
			if(ret):
				if( self.ui.checkBox_flipImage.isChecked()):
					img = cv2.flip(img, 1)
				rot = self.ui.rotateIndx
				for i in range(rot):
					img = cv2.rotate(img, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)
				height, width, channel = img.shape

				maxPix = self.ui.spinbox_pixCount.value()*1000
				if ( height*width>maxPix):
					newWidth = math.sqrt(maxPix*width/height)
					newHeight = height*newWidth/width                       
					img = cv2.resize(img, ( int(newWidth), int(newHeight) ), interpolation = cv2.INTER_AREA) 
				faces = []    
				tempFaces = numpy.array([])    
				eyes = numpy.array([])   
				if( self.ui.checkBox_startTracking.isChecked() ):  
					gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
					#tresh = self.ui.spinbox_treshold.value()
					tresh=4
					tempFaces = face_cascade.detectMultiScale(gray, 1.1, tresh) 
					for face in tempFaces:
						try:			
							(x, y, w, h) = face
							if( w>h*1.3 or h>w*1.3):
								continue
							cond = self.ui.checkBox_eyes.isChecked()	
							if(cond):
								tempgray =gray[y:y+h, x:x+w]
								height, width = tempgray.shape
								tempgray = cv2.resize(tempgray, ( int(width/2), int(height/2) ), interpolation = cv2.INTER_AREA)
								eyes = eye_cascade.detectMultiScale(tempgray)
								print("eyes ",len(eyes))
							if(len(eyes)>0 or not cond):
								faces.append(face)
								print(faces)
								print(tempFaces)
						except:
							continue

				if( type(tempFaces)==tuple):
					faces = numpy.array([])   

				faces = numpy.asarray(faces)	
				self.progress.emit(img,faces)
		self.finished.emit()
		

class Ui_MainWindow(QtWidgets.QMainWindow):
	def setupUi(self):
		global device_list
		self.rotateIndx = 0
		self.keyboard = Controller()
		self.space = False
		self.right = False
		self.left = False
		self.image=[[["","",""]]]
		self.cap =VideoCapture(0)
		self.width=320
		self.height = 350
		self.device_list = device_list
		self.camIndex =0

		self.setObjectName("MainWindow")
		self.resize(self.width, self.height)
		self.centralwidget = QtWidgets.QWidget(self)

		self.centralwidget.setObjectName("centralwidget")
		self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
		self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, self.width, self.height))
		self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
		self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self.verticalLayout.setObjectName("verticalLayout")
		self.label_usedCam = QtWidgets.QLabel(self.verticalLayoutWidget)
		self.label_usedCam.setObjectName("label_usedCam")
		self.label_usedCam.setMaximumHeight(15)
		self.label_usedCam.setMinimumHeight(15)
		self.label_usedCam.setAlignment(QtCore.Qt.AlignCenter)
		self.verticalLayout.addWidget(self.label_usedCam)
		self.dropDown_camera = QtWidgets.QComboBox(self.verticalLayoutWidget)
		self.dropDown_camera.setObjectName("dropDown_camera")
		self.verticalLayout.addWidget(self.dropDown_camera)
		for ele in self.device_list:
			self.dropDown_camera.addItem(ele)
		#self.dropDown_camera.addItem("IP Cam")    
		self.dropDown_camera.currentIndexChanged.connect(self.camChanged)

		# self.ipframe = QtWidgets.QFrame()
		# self.horizontalLayout = QtWidgets.QHBoxLayout()
		# self.horizontalLayout.setObjectName("horizontalLayout")
		# self.label_ipcam = QtWidgets.QLabel(self.verticalLayoutWidget)
		# self.label_ipcam.setObjectName("label_ipcam")
		# self.horizontalLayout.addWidget(self.label_ipcam)
		# self.lineEdit_ipCam = QtWidgets.QLineEdit(self.verticalLayoutWidget)
		# self.lineEdit_ipCam.setObjectName("lineEdit_ipCam")
		# self.horizontalLayout.addWidget(self.lineEdit_ipCam)
		# self.pushButton_ip =  QtWidgets.QPushButton("Ok")
		# self.pushButton_ip.clicked.connect(self.startIPCam)
		# self.horizontalLayout.addWidget(self.pushButton_ip)
		# self.ipframe.setLayout(self.horizontalLayout)
		# self.verticalLayout.addWidget(self.ipframe)

		self.horizontalLayout_checkBoxes = QtWidgets.QHBoxLayout()
		self.horizontalLayout_checkBoxes.setObjectName("horizontalLayout_3")
		self.checkBox_flipImage = QtWidgets.QCheckBox(self.verticalLayoutWidget)
		self.checkBox_flipImage.setObjectName("checkBox")
		self.horizontalLayout_checkBoxes.addWidget(self.checkBox_flipImage)
		self.checkBox_showBox = QtWidgets.QCheckBox(self.verticalLayoutWidget)
		self.checkBox_showBox.setObjectName("checkBox_showBox")
		self.horizontalLayout_checkBoxes.addWidget(self.checkBox_showBox)
		self.checkBox_showText = QtWidgets.QCheckBox(self.verticalLayoutWidget)
		self.checkBox_showText.setObjectName("checkBox_showText")
		self.horizontalLayout_checkBoxes.addWidget(self.checkBox_showText)

		self.checkBox_startTracking = QtWidgets.QCheckBox(self.verticalLayoutWidget)
		self.checkBox_startTracking.setObjectName("checkBox_startTracking")
		self.horizontalLayout_checkBoxes.addWidget(self.checkBox_startTracking)
		self.verticalLayout.addLayout(self.horizontalLayout_checkBoxes)

		self.horizontalLayout_checkBoxes2 = QtWidgets.QHBoxLayout()
		self.horizontalLayout_checkBoxes2.setObjectName("horizontalLayout_4")
		self.pushButton_rotate = QtWidgets.QPushButton(self.verticalLayoutWidget)
		self.pushButton_rotate.setObjectName("pushButton_rotate")
		self.pushButton_rotate.setText("Rotate 90 Deg")
		self.pushButton_rotate.clicked.connect(self.rotate)
		self.horizontalLayout_checkBoxes2.addWidget(self.pushButton_rotate)
		self.label_pixCount = QtWidgets.QLabel(self.verticalLayoutWidget)
		self.label_pixCount.setObjectName("label_pixCount")
		self.label_pixCount.setText("Pixel count:")
		self.label_pixCount.setAlignment(QtCore.Qt.AlignRight)
		self.horizontalLayout_checkBoxes2.addWidget(self.label_pixCount)
		self.spinbox_pixCount = QtWidgets.QSpinBox(self.verticalLayoutWidget)
		self.spinbox_pixCount.setRange(1,9999)
		self.spinbox_pixCount.setValue(70)
		self.horizontalLayout_checkBoxes2.addWidget(self.spinbox_pixCount)
		self.verticalLayout.addLayout(self.horizontalLayout_checkBoxes2)

		# self.horizontalLayout_checkBoxes3 = QtWidgets.QHBoxLayout()
		# self.horizontalLayout_checkBoxes3.setObjectName("horizontalLayout_5")
		# self.verticalLayout.addLayout(self.horizontalLayout_checkBoxes3)
		self.checkBox_eyes = QtWidgets.QCheckBox(self.verticalLayoutWidget)
		self.checkBox_eyes.setObjectName("checkBox_eyes")
		self.horizontalLayout_checkBoxes2.addWidget(self.checkBox_eyes)
		# self.label_treshold = QtWidgets.QLabel(self.verticalLayoutWidget)
		# self.label_treshold.setObjectName("label_treshold")
		# self.label_treshold.setText("Set Treshold")
		# self.label_treshold.setAlignment(QtCore.Qt.AlignRight)
		# self.horizontalLayout_checkBoxes3.addWidget(self.label_treshold)
		# self.spinbox_treshold = QtWidgets.QSpinBox(self.verticalLayoutWidget)
		# self.spinbox_treshold.setRange(1,15)
		# self.spinbox_treshold.setValue(4)
		# self.horizontalLayout_checkBoxes3.addWidget(self.spinbox_treshold)

		self.centerHolder = QtWidgets.QWidget(self.verticalLayoutWidget)
		self.centerHolder.setMinimumHeight(40)
		self.centerHolder.setMaximumHeight(40)

		self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centerHolder)
		self.horizontalLayout_2.setObjectName("horizontalLayout_2")
		self.label_center = QtWidgets.QLabel(self.verticalLayoutWidget)
		self.label_center.setObjectName("label_center")
		self.horizontalLayout_2.addWidget(self.label_center)
		self.slider_y = QtWidgets.QSpinBox(self.verticalLayoutWidget)
		self.slider_y.setObjectName("slider_y")
		self.slider_y.setRange(1,100)
		self.slider_y.setValue(50)
		self.horizontalLayout_2.addWidget(self.slider_y)
		self.slider_x = QtWidgets.QSpinBox(self.verticalLayoutWidget)
		self.slider_x.setObjectName("slider_x")
		self.slider_x.setRange(1,100)
		self.slider_x.setValue(50)
		self.horizontalLayout_2.addWidget(self.slider_x)
		self.label_size = QtWidgets.QLabel(self.verticalLayoutWidget)
		self.label_size.setObjectName("label_size")
		self.horizontalLayout_2.addWidget(self.label_size)
		self.sldier_size = QtWidgets.QSpinBox(self.verticalLayoutWidget)
		self.sldier_size.setObjectName("sldier_size")
		self.sldier_size.setRange(1,100)
		self.sldier_size.setValue(10)        
		self.horizontalLayout_2.addWidget(self.sldier_size)
		spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.horizontalLayout_2.addItem(spacerItem)
		self.verticalLayout.addWidget(self.centerHolder)


		self.shameless = QtWidgets.QHBoxLayout()
		self.shamelessLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
		self.shamelessLabel.setText(" Made By ZiedYT")
		self.shamelessYT = QtWidgets.QPushButton(self.verticalLayoutWidget)
		self.shamelessYT.setText(" Youtube")
		self.shamelessYT.setIcon(QtGui.QIcon('youtube.png'))
		#self.shamelessYT.clicked.connect(lambda: { webbrowser.open('http://youtube.com/ziedyt')  } )
		self.shamelessTwitt = QtWidgets.QPushButton(self.verticalLayoutWidget)
		self.shamelessTwitt.setText(" Twitter")
		#self.shamelessTwitt.clicked.connect(lambda: { webbrowser.open('https://twitter.com/ZiedYT')  } )
		self.shamelessTwitt.setIcon(QtGui.QIcon('twitter.png'))

		#self.shameless.setAlignment(QtCore.Qt.AlignCenter)
		#self.shameless.setMaximumHeight(25)
		self.shameless.addWidget(self.shamelessLabel)
		self.shameless.addWidget(self.shamelessYT)
		self.shameless.addWidget(self.shamelessTwitt)
		self.verticalLayout.addLayout(self.shameless)

		self.display = QtWidgets.QLabel(self.verticalLayoutWidget)
		self.display.setObjectName("display")
		self.verticalLayout.addWidget(self.display)
		self.display.setAlignment(QtCore.Qt.AlignCenter)
		self.display.setScaledContents(False)
		self.setCentralWidget(self.centralwidget)
		self.menubar = QtWidgets.QMenuBar(self)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 326, 21))
		self.menubar.setObjectName("menubar")
		self.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(self)
		self.statusbar.setObjectName("statusbar")
		self.setStatusBar(self.statusbar)

		self.retranslateUi()
		QtCore.QMetaObject.connectSlotsByName(self)
		
		# if(self.dropDown_camera.count()>1):
		#     self.ipframe.setHidden(True)
		self.thread = QThread()    
		self.worker = Worker()
		self.worker.changeCap(self.cap,self)
		self.worker.moveToThread(self.thread)
		self.thread.started.connect(self.worker.run)
		self.worker.finished.connect(self.thread.quit)
		self.worker.finished.connect(self.worker.deleteLater)
		self.thread.finished.connect(self.thread.deleteLater)
		self.worker.progress.connect(self.reportProgress)
		# Step 6: Start the thread
		self.thread.start()

	def retranslateUi(self):
		_translate = QtCore.QCoreApplication.translate
		self.setWindowTitle(_translate("MainWindow", "Jump(Squat)King"))
		self.label_usedCam.setText(_translate("MainWindow", "Select camera to use:"))
		#self.label_ipcam.setText(_translate("MainWindow", "IP cam:"))
		self.checkBox_showBox.setText(_translate("MainWindow", "Boxes"))
		self.checkBox_showText.setText(_translate("MainWindow", "Text"))
		self.checkBox_eyes.setText(_translate("MainWindow", "Use eyes position as backup"))
		self.checkBox_startTracking.setText(_translate("MainWindow", "Start tracking"))
		self.checkBox_flipImage.setText(_translate("MainWindow", "Flip image"))
		self.label_center.setText(_translate("MainWindow", "Idle box center:"))
		self.label_size.setText(_translate("MainWindow", "Idle box size:"))

		self.found = False
		self.centerX=-1
		self.centerY=-1
		self.count = 0



	def resizeEvent(self, event):
		print("resize")
		self.width = event.size().width() 
		self.height=event.size().height() 
		QtWidgets.QMainWindow.resizeEvent(self, event)
		self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, self.width, self.height))
		self.fitImage()
	def rotate(self):
		self.rotateIndx =  (self.rotateIndx+1)%4

	def camChanged(self):
		try:
			if(self.camIndex!=self.dropDown_camera.currentIndex()):
				print("1")
				#
				self.worker.running = False
				camIndex = self.dropDown_camera.currentIndex()

				print("2")
				self.worker.running= False
				self.worker.done()
				self.thread.exit()
				self.thread.terminate()
				self.thread.wait()
				print("2.5")
				self.cap.close()
				self.cap = VideoCapture(camIndex)

				self.thread = QThread()    
				self.worker = Worker()
				self.worker.changeCap(self.cap,self)
				self.worker.moveToThread(self.thread)
				self.thread.started.connect(self.worker.run)
				self.worker.finished.connect(self.thread.quit)
				self.worker.finished.connect(self.worker.deleteLater)
				self.thread.finished.connect(self.thread.deleteLater)
				self.worker.progress.connect(self.reportProgress)
				self.thread.start()
				print("3")
				# self.ipframe.setHidden(True)
				print("4")
				self.camIndex = camIndex


					#self.cap =VideoCapture(self.camIndex)
		except:
			self.dropDown_camera.setCurrentIndex(self.camIndex)
			print()

	# def startIPCam(self):
	#     print(self.lineEdit_ipCam.text())
	#     self.cap =VideoCapture(self.lineEdit_ipCam.text())
	#     self.worker.changeCap(self.cap,self)

	def reportProgress(self,ele,faces):
		#print()
		self.image=ele
		self.raw = ele
		self.drawBox()
		self.trackCommand(faces)
		self.fitImage()

	def fitImage(self):
		if(self.image==[[["","",""]]]):
			return
		height, width, channel = self.image.shape
		
		fitwidth = self.display.height()*width/height
		#print("display.width()",self.display.width(),"fitwidth",fitwidth)
		if( self.display.width()<fitwidth ):
			fitwidth = self.display.width()
		
		bytesPerLine = 3 * width
		qImg = QtGui.QImage(self.image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()

		pix = QtGui.QPixmap(qImg)
		pix = pix.scaled(fitwidth,fitwidth*height/width,QtCore.Qt.KeepAspectRatio)

		self.display.setPixmap(pix)
		self.display.show()

	def drawBox(self):


		height, width, channel = self.image.shape
		self.boxX = (int) (width*self.slider_x.value()/100)
		self.boxY = (int) (height*self.slider_y.value()/100)
		self.boxA =(int)  (width*self.sldier_size.value()/100)

		if( not self.checkBox_showBox.isChecked()):
			return
		start_point=(self.boxX-self.boxA,self.boxY-self.boxA)
		end_point=(self.boxX+self.boxA,self.boxY+self.boxA)
		self.image = cv2.rectangle(self.image, start_point, end_point, (255,0,0), 2)

		leftLineStart =  ( self.boxX-self.boxA,0 )
		leftLineEnd =  ( self.boxX-self.boxA,self.boxY+self.boxA )
		self.image = cv2.line(self.image, leftLineStart, leftLineEnd, (255,255,0), 2) #left if self.boxX-self.boxA>X

		rightLineStart =  ( self.boxX+self.boxA,0 )
		rightLineEnd =  ( self.boxX+self.boxA,self.boxY+self.boxA )
		self.image = cv2.line(self.image, rightLineStart, rightLineEnd, (255,255,0), 2) #right if self.boxX+self.boxA<X

		bottomLineStart =  ( 0,self.boxY+self.boxA )
		bottomLineEnd =  ( width,self.boxY+self.boxA )
		self.image = cv2.line(self.image, bottomLineStart, bottomLineEnd, (255,255,0), 2) #bot if self.boxY+self.boxA<Y  

		font = cv2.FONT_HERSHEY_SIMPLEX
		scale=0.04
		fontScale =  scale*min(width,height)/25
		texts = ['Press Right Arrow','Press Left Arrow','Release All keys','Press Spacebar']
		coords=[ [int( (width+self.boxX+self.boxA)/2 ),15] ,[int( (self.boxX-self.boxA)/2), 15],[int(width/2),max ( self.boxY-self.boxA-15,15) ],[int(width/2),self.boxY+self.boxA+15] ]
		if(self.checkBox_showText.isChecked()):
			for i in [1,0]:
				for j in [0,1,2,3]:
					text = texts[j]
					textsize = cv2.getTextSize(text, font, fontScale, 1)[0]
					textX = coords[j][0] - int(textsize[0]/2)
					textY = coords[j][1]
					cv2.putText(self.image, text, ( textX,textY ) , font, fontScale, (0, 255-255*i, 0), 1+i*3, cv2.LINE_8)

	def trackCommand(self,faces):
		if(not self.checkBox_startTracking.isChecked() ):
			return

		if( len(faces)!=0):
			#return
			# for face in faces:
			# 	(x, y, w, h) = face
			# 	self.image= cv2.rectangle(self.image, (x, y), (x+w, y+h), (0, 0, 0), 2)	
			indx =-1
			curr=-1
			minsize=999999
			for (x, y, w, h) in faces:
				indx+=1
				if(w*h<minsize  ):
					minsize = w*h
					curr = indx
			(x, y, w, h) = faces[curr]    
			self.image= cv2.rectangle(self.image, (x, y), (x+w, y+h), (255, 0, 0), 2)
			self.centerX = int( (x+x+w)/2 )
			self.centerY = int( (y+y+h)/2 )
			self.found = True
			self.count = 0

		elif( self.checkBox_eyes.isChecked() ):
			#return
			#self.counter +=1 	
			#self.counter = self.counter %3 
			if( self.centerY>0 and self.centerX>0 or not self.found ):
				try:
					gray = cv2.cvtColor(self.raw, cv2.COLOR_BGR2GRAY) [self.centerY-self.boxA:self.centerY+self.boxA, self.centerX-self.boxA:self.centerX+self.boxA]
					roi_color = self.image[self.centerY-self.boxA:self.centerY+self.boxA, self.centerX-self.boxA:self.centerX+self.boxA]

					if( not self.found  ):
						print("finding backup eyes")
						gray = cv2.cvtColor(self.raw, cv2.COLOR_BGR2GRAY)
						roi_color =self.image
						self.count +=1
						self.count=self.count%5
						if(self.count!=1):
							return


					height, width = gray.shape
					gray = cv2.resize(gray, ( int(width/2), int(height/2) ), interpolation = cv2.INTER_AREA)
					eyes = eye_cascade.detectMultiScale(gray)

					tempX=0
					tempY=0
					for (ex,ey,ew,eh) in eyes: 
						if( self.found):
							cv2.rectangle(roi_color,(ex*2,ey*2),(ex*2+ew*2,ey*2+eh*2),(0,127,255),2) 
							tempX += self.centerX-self.boxA+ex*2+ew*2
							tempY += self.centerY-self.boxA+ey*2+eh*2
						else:
							cv2.rectangle(roi_color,(ex*2,ey*2),(ex*2+ew*2,ey*2+eh*2),(0,127,255),2) 
							tempX += ex*2+ew*2
							tempY += ey*2+eh*2							
					
					if( len(eyes)>0):
						print("eyes",len(eyes))
						self.centerX=int(tempX/len(eyes))
						self.centerY= int(tempY/len(eyes))
						self.found=True
						self.count=0
					else:
						self.found = False
				except:
					self.found = False
					return
		
		else:
			self.found = False
			self.count = 0


		if ( self.boxY+self.boxA<self.centerY ):
			if( self.space==False):
				self.space=True
				self.keyboard.press(Key.space)
				print("press space")
				#keyboard hold space
		elif( self.space):
			print("release space")
			self.keyboard.release(Key.space)
			self.space=False

		if( self.boxX+self.boxA<self.centerX ):
			if( self.right==False):
				self.right=True
				self.keyboard.press(Key.right)         
		elif( self.right):
			self.right=False
			self.keyboard.release(Key.right)

		if( self.boxX-self.boxA>self.centerX ):
			if( self.left==False):
				self.left=True
				self.keyboard.press(Key.left)      
		elif( self.left):
			self.left=False
			self.keyboard.release(Key.left)         

if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	#MainWindow = QtWidgets.QMainWindow()
	MW = Ui_MainWindow()
	MW.setupUi()
	MW.show()
	sys.exit(app.exec_())
