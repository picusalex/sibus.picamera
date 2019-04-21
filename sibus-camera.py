#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, Response, jsonify, send_file, abort

import numpy as np
import cv2
import time, sys, os, datetime
import threading 
import glob

import logging
logger = logging.getLogger("rasp-camera")
logger.setLevel(logging.DEBUG)
steam_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s|%(levelname)08s | %(message)s')
steam_handler.setFormatter(stream_formatter)
logger.addHandler(steam_handler)

from VideoStream.videostream import VideoStream

SNAPSHOT_ARCHIVES_DIR = "./output"
SNAPSHOT_TMP_DIR = "/tmp"

class OpenCamera():
	def __init__(self, stream):
		self._stream = stream		
		self._name = stream.name
		self.check_filesystem()
		
		self.start_stream()
		
	def start_stream(self):
		logger.info("OpenCamera: starting %s"%self._name)
		self._stream.start()

	def stop_stream(self):
		logger.info("OpenCamera: stoping %s"%self._name)
		self._stream.stop()
		
	def get_frame(self):
		frame = self._stream.read()
		frame = cv2.flip( frame, -1 )
		datetime_now = str(datetime.datetime.now())
		
		cv2.putText(img = frame, 
                        text = datetime_now,
                        org = (10,20), 
                        fontFace = cv2.FONT_HERSHEY_DUPLEX, 
                        fontScale = 0.5, 
                        color = (230,230,230),
                        thickness = 1, 
                        lineType = cv2.CV_AA)

		return frame
	
	def get_jpeg(self):
		frame = self.get_frame()
		if frame is not None:
			ret, jpeg = cv2.imencode('.jpg', frame)
			self._current_jpeg = jpeg
			return jpeg   
		else:
			return None

	def check_filesystem(self):
		self.archive_folder = os.path.join(os.path.realpath(SNAPSHOT_ARCHIVES_DIR), self._name)
		logger.debug("FILESYSTEM %s: archive folder = %s"%(self._name, self.archive_folder))
		if not os.path.isdir(self.archive_folder):
			os.makedirs(self.archive_folder)

		self.live_snapshot = os.path.join(os.path.realpath(SNAPSHOT_TMP_DIR), "%s-live.jpg"%str(self._name))
		self.live_snapshot_md = os.path.join(os.path.realpath(SNAPSHOT_TMP_DIR), "%s-live.dat"%str(self._name))
		logger.debug("FILESYSTEM %s: live snapshot = %s"%(self._name, self.live_snapshot))
		logger.debug("FILESYSTEM %s: live snapshot metadata = %s"%(self._name, self.live_snapshot_md))
		if not os.path.isdir(os.path.realpath(SNAPSHOT_TMP_DIR)):
			os.makedirs(os.path.realpath(SNAPSHOT_TMP_DIR))		

	def archive_snapshot(self, mins=15):
		frame = self.get_frame()
		if frame is None:
			logger.error("ERROR %s: getting snapshot to archive !"%self._name)
			return
		
		pattern = "%Y-%m-%dT%H:%M:%S.%fZ"
		if not os.path.isfile(self.live_snapshot_md):
			with open(self.live_snapshot_md, "w") as file:
				file.write(str(datetime.datetime.now().strftime(pattern)))		
				time.sleep(2)

		with open(self.live_snapshot_md, "r") as file:
			t = file.readline()
			lastdate = datetime.datetime.strptime(t, pattern)
	
		currentdate = datetime.datetime.now()		
		delta = datetime.timedelta(minutes=mins)
		logger.debug("ARCHIVE %s: last snapshot = %s / %s"%(self._name, str(currentdate - lastdate), str(delta)))
		
		if lastdate is None or (currentdate - lastdate) > delta:			
			archive_folder = os.path.join(self.archive_folder, 
									str(currentdate.year), 
									"%0.2d"%currentdate.month,
									"%0.2d"%currentdate.day) 
			if not os.path.isdir(archive_folder):
				os.makedirs(archive_folder)			
			
			archive_file = os.path.join(archive_folder,"%s.jpg"%currentdate.strftime("snap-%H-%M-%S"))
			logger.info("ARCHIVE %s: archiving snapshot : %s"%(self._name,archive_file))
			cv2.imwrite(archive_file,frame)
			with open(self.live_snapshot_md, "w") as file:
				file.write(str(currentdate.strftime(pattern)))
		else:
			logger.info("ARCHIVE %s: NOT archiving yet. %s left"%(self._name, str(delta - (currentdate - lastdate))))
	
	
	def write_snapshot(self):
		frame = self.get_frame()
		if frame is None:
			logger.error("ERROR getting snapshot to write !")
			return
		
		logger.info("WRITE %s: Saving frame to file %s"%(self._name, self.live_snapshot))
		cv2.imwrite(self.live_snapshot,frame)
		logger.debug("WRITE %s: done with success !"%self._name)			

picam = VideoStream(usePiCamera=True)
webcam = VideoStream(src=1)
		
cameras = [OpenCamera(picam), OpenCamera(webcam)]		

def gen(camera):
	while True:
		jpeg = camera.get_jpeg()
		
		if jpeg is not None:
			#time.sleep(0.1)
			yield (b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

def snap(camera):
	jpeg = camera.get_jpeg()
	if jpeg is not None:
		return jpeg.tobytes()
	else:
		return abort(404)
	
def archive_thread_func():
    while(1):
      for cam in cameras:
		cam.archive_snapshot()
      time.sleep(10)
    
archive_thread = threading.Thread(None, archive_thread_func, None, (), {}) 

app = Flask(__name__)
@app.route("/")
@app.route("/index.html")
def index():
  return render_template('index.html')
  
"""@app.route("/<page>")
def page(page):
  return render_template(page)  """

@app.route("/camera.html")
def camera_page():
  return render_template('camera.html')    

@app.route("/timelaps.html")
def timelaps_page():
  return render_template('timelaps.html')    
      
@app.route("/video_feed/<int:idx>")
def video_feed(idx):
	return Response(gen(cameras[idx]), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/snapshot/<int:idx>")
def snapshot(idx):
	return Response(snap(cameras[idx]), mimetype="image/jpeg;")

@app.route("/archives")
@app.route("/archives/")
@app.route("/archives/<path:path>")
def list_archives(path="."):
	logger.info("Listing archives in %s"%path)
	root_dir = os.path.realpath(SNAPSHOT_ARCHIVES_DIR)
	full_path = os.path.join(root_dir, path)
	
	if os.path.isdir(full_path):
		subdirs = sorted([f for f in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, f))], reverse=True)
		files = sorted([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))], reverse=True)
		return jsonify({"files": files, "dirs": subdirs})
	
	if os.path.isfile(full_path):
		return send_file(full_path, mimetype="image/png;")

def get_image_after_date(camera, year, month, day, hour):
    root_dir = os.path.realpath(SNAPSHOT_ARCHIVES_DIR)
    folder_path = os.path.join(root_dir, camera, "%04d"%year, "%02d"%month, "%02d"%day)
    if not os.path.isdir(folder_path):
        logger.warning("Folder {} does not exist".format(folder_path))
        return None
    
    files = glob.glob(os.path.join(folder_path, "snap-%02d-*"%hour))
    if len(files) > 0 and os.path.getsize(files[0]) > 50*1024:
        return files[0].replace(root_dir, "").strip("/")
    else:
        return None    
    
    
def get_images(camera, start_dt, evry_hours):
    files = []
    dt = start_dt
    f = get_image_after_date(camera, dt.year,dt.month,dt.day,dt.hour)
    while(dt < datetime.datetime.now()):
        if f is not None:
            files.append(f)
        
        dt = dt + datetime.timedelta(hours=evry_hours)
        f = get_image_after_date(camera, dt.year,dt.month,dt.day,dt.hour)        
                
    return sorted(files, reverse=True)
    
@app.route("/timelap/<string:camera>")
@app.route("/timelap/<string:camera>/<string:start>/<int:evry_hours>")
def gen_timelap(camera, start=None,evry_hours=4):
    if start is None:
        start = "2019-04-14"
    
    start_dt = datetime.datetime.strptime(start, '%Y-%m-%d')
            
    logger.info("Generating timelap starting on {}, pictures every {} hours".format(start_dt, evry_hours))
    files = get_images(camera, start_dt, evry_hours)
    
    return jsonify({"files": files})
    
    
            
if __name__ == '__main__':
  archive_thread.start()
  app.run(host='0.0.0.0', threaded=True)
