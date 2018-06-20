#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import cv2
import time, sys, os, datetime
import logging
logger = logging.getLogger("rasp-camera")
logger.setLevel(logging.DEBUG)
steam_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s|%(levelname)08s | %(message)s')
steam_handler.setFormatter(stream_formatter)
logger.addHandler(steam_handler)

CAMERA_IDX = 0
SNAPSHOT_ARCHIVES_DIR = "./output"
SNAPSHOT_TMP_DIR = "/tmp/"

class OpenCamera():
	def __init__(self, idx):
		self._idx = idx
		
		self.connect_camera()	

	def isOpened(self):
		return self.__capture_intf.isOpened()
		
	def connect_camera(self):
		self.__capture_intf = None
		logger.info("Connecting to camera %d"%self._idx)
		self.__capture_intf = cv2.VideoCapture(self._idx)
		time.sleep(1)
		
		if self.isOpened():
			logger.info("Connected to camera %d"%self._idx)
			return
		else:
			logger.error("!! Impossible to connect to camera %d"%self._idx)
			self.cap = None
	
	def check_filesystem(self):
		self.archive_folder = os.path.realpath(SNAPSHOT_ARCHIVES_DIR)
		logger.debug("SNAPSHOT: archive folder = %s"%self.archive_folder)
		if not os.path.isdir(self.archive_folder):
			os.makedirs(self.archive_folder)

		self.live_snapshot = os.path.join(os.path.realpath(SNAPSHOT_TMP_DIR), "rasp-camera-live.png")
		self.live_snapshot_md = os.path.join(os.path.realpath(SNAPSHOT_TMP_DIR), "rasp-camera-live.png.txt")
		logger.debug("SNAPSHOT: live snapshot = %s"%self.live_snapshot)
		logger.debug("SNAPSHOT: live snapshot metadata = %s"%self.live_snapshot_md)
		if not os.path.isdir(os.path.realpath(SNAPSHOT_TMP_DIR)):
			os.makedirs(os.path.realpath(SNAPSHOT_TMP_DIR))		

	def archive_snapshot(self, frame):
		pattern = "%Y-%m-%dT%H:%M:%S.%fZ"
		if not os.path.isfile(self.live_snapshot_md):
			with open(self.live_snapshot_md, "w") as file:
				file.write(str(datetime.datetime.now().strftime(pattern)))		
				time.sleep(2)

		with open(self.live_snapshot_md, "r") as file:
			t = file.readline()
			lastdate = datetime.datetime.strptime(t, pattern)
	
		currentdate = datetime.datetime.now()		
		logger.debug("SNAPSHOT ARCHIVE: last snapshot = %s"%(str(currentdate - lastdate)))
		
		if lastdate is None or (currentdate - lastdate) > datetime.timedelta(minutes=15):			
			archive_folder = os.path.join(self.archive_folder, 
									str(currentdate.year), 
									str(currentdate.month)) 
			if not os.path.isdir(archive_folder):
				os.makedirs(archive_folder)			
			
			archive_file = os.path.join(archive_folder,"%s-snapshot.png"%currentdate.strftime("%Y%m%d-%H%M%S-%f"))
			logger.info("SNAPSHOT ARCHIVE: archiving snapshot : %s"%archive_file)
			
			cv2.imwrite(archive_file,frame)
			with open(self.live_snapshot_md, "w") as file:
				file.write(str(currentdate.strftime(pattern)))
			
			
	def write_snapshot(self, frame):
		logger.info("SNAPSHOT: Saving frame to file %s"%self.live_snapshot)
		cv2.imwrite(self.live_snapshot,frame)
		
		self.archive_snapshot(frame)
		logger.debug("SNAPSHOT: done with success !")
	
	def take_snapshot(self):
		if not self.isOpened():
			raise "snapshot error : camera %d not opened !"%self._idx
		
		self.check_filesystem()
		
		logger.info("+++++++++++++++++++++++++++++++++++++++++++++++")
		logger.info("SNAPSHOT: Reading frame from camera %d"%self._idx)
		ret, frame = self.__capture_intf.read()
		logger.debug("SNAPSHOT: return from read camera = %s"%str(ret))
		
		if ret:
			self.write_snapshot(frame)
			return
		else:
			logger.error("SNAPSHOT: !! invalid frame from camera")
			logger.debug("SNAPSHOT: !! error during process !")
			raise "snapshot error : invalid frame from camera"


if __name__ == "__main__":
	logger.info("####################################################")
	logger.info("rasp-camera starting...")
	
	try:
		cap = OpenCamera(CAMERA_IDX)
		
		while(cap.isOpened()):
			cap.take_snapshot()
			time.sleep(0.5)
		
		logger.warning("Camera %d disconnected. Exiting."%CAMERA_IDX)
		logger.info("rasp-camera stopped")
		logger.info("####################################################")				
		cap.release()
		sys.exit(1)			
			
	except (KeyboardInterrupt):
		logger.info("Ctrl+C detected !")
		logger.info("rasp-camera stopped")
		logger.info("####################################################")				
		sys.exit(0)		
	except Exception as e:
		logger.exception("Exception in program detected ! \n" + str(e))
		logger.info("rasp-camera stopped")
		logger.info("####################################################")				
		sys.exit(1)
	
	cap.release()
	sys.exit(0)		
	
	

