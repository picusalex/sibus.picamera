# import the necessary packages
from .webcamvideostream import WebcamVideoStream
import cv2

class VideoStream:
	def __init__(self, src=0, usePiCamera=False, resolution=(640, 480),
		framerate=32):
		# check to see if the picamera module should be used
		if usePiCamera:
			# only import the picamera packages unless we are
			# explicity told to do so -- this helps remove the
			# requirement of `picamera[array]` from desktops or
			# laptops that still want to use the `imutils` package
			from .pivideostream import PiVideoStream

			# initialize the picamera stream and allow the camera
			# sensor to warmup
			self.name = "raspcam"
			self.stream = PiVideoStream(resolution=resolution,
				framerate=framerate)

		# otherwise, we are using OpenCV so initialize the webcam
		# stream
		else:
			self.name = "webcam%d"%src
			self.stream = WebcamVideoStream(src=src)
		
		

	def start(self):
		# start the threaded video stream
		return self.stream.start()

	def update(self):
		# grab the next frame from the stream
		self.stream.update()

	def read(self):
		# return the current frame
		return self.stream.read()

	def stop(self):
		# stop the thread and release any resources
		self.stream.stop()
		
	def equalized_frame(self):
		img = self.read()
		ycrcb = cv2.cvtColor(img,cv2.COLOR_BGR2YCR_CB)
		channels = cv2.split(ycrcb)
		cv2.equalizeHist(channels[0],channels[0])
		cv2.merge(channels,ycrcb)
		cv2.cvtColor(ycrcb,cv2.COLOR_YCR_CB2BGR,img)
		return img
		
		
		
		