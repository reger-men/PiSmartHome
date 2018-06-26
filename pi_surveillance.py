# python pi_surveillance.py --conf conf.json

# import the necessary packages
#from picamera.array import PiRGBArray #raspberry spec
#from picamera import PiCamera #raspberry spec
from utils import send_email, TempImage
import argparse
import warnings
import datetime
import json
import time
import cv2
import urllib2
import sys

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
ap.add_argument("-s", "--source", default="cam", required=False,
	help="video source may cam (PI camera) or stream1, stream2,... (for stream canal 1,..,6) ")
ap.add_argument("-d", "--debug", required=False,
	help="debug mode on/off")
args = vars(ap.parse_args())

# filter warnings, load the configuration 
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None

# set debug mode on 
if args['debug']:
	print('Debug mode is on !')
	debug_mode = True
else:
	debug_mode = False

# check whatever the source video is.
if args['source'] == "stream1":
	username = raw_input("Please enter the username: ")
	pw = raw_input("Please enter your password: ")
	if not username or not pw:
		print 'The Username or password has to be not empty!'
		sys.exit()
	else:
        	hoststr = 'rtsp://' + username + ':' + pw + '@195.60.68.239:554/axis-media/media.amp?camera=1'
		print 'Streaming ' + hoststr

		cap = cv2.VideoCapture(hoststr)
	
		if (not cap.isOpened()):
			print('Error while open Stream url')
	
elif args['source'] == "stream2":
	username = raw_input("Please enter the username: ")
        pw = raw_input("Please enter your password: ")
        if not username or not pw:
                print 'The Username or password has to be not empty!'
                sys.exit()
        else:
		hoststr = 'rtsp://' + username + ':' + pw + '@193.159.244.132:554/?h26x=0' #?h26x=0 to select camera1
		print 'Streaming ' + hoststr

		cap = cv2.VideoCapture(hoststr)
	
		if (not cap.isOpened()):
			print('Error while open Stream url')

else:
	# initialize the camera and grab a reference to the raw camera capture
	camera = PiCamera()
	camera.resolution = tuple(conf["resolution"])
	camera.framerate = conf["fps"]
	rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print "[INFO] warming up..."
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0
print('[INFO] PiSH started !!')

# capture frames from the camera
#for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True): #raspberry spec
while(True):
	# Capture frame-by-frame
    	ret, frame = cap.read()
    	frame = cv2.resize(frame, (640,480), interpolation=cv2.INTER_AREA)
	
	# grab the raw NumPy array representing the image and initialize
	#frame = f.array
	timestamp = datetime.datetime.now()
	text = "No Motion detected"

	######################################################################
	# COMPUTER VISION
	######################################################################
	# resize the frame, convert it to grayscale, and blur it
	# TODO: resize image here into smaller sizes 
	gray_ = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray_, tuple(conf['blur_size']), 0)

	
        if debug_mode:
		cv2.imwrite("gray.jpeg", gray_)
		cv2.imwrite("blur.jpeg", gray)

	# if the average frame is None, initialize it
	if avg is None:
		print "[INFO] starting background model..."
		avg = gray.copy().astype("float")
		#cv2.imwrite("avg.jpeg", avg)
		#rawCapture.truncate(0) #raspberry spec
		continue

	# accumulate the weighted average between the current frame and
	# previous frames, then compute the difference between the current
	# frame and running average
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
	#cv2.imwrite("frameDelta.jpeg", frameDelta)
	cv2.accumulateWeighted(gray, avg, 0.5)
	
	# threshold the delta image, dilate the thresholded image to fill
	# in holes, then find contours on thresholded image
	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
		cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=2)
	im2 ,cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)

	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < conf["min_area"]:
			continue

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Alert"

	# draw the text and timestamp on the frame
	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, "PiSH Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)


	###################################################################################
	# LOGIC
	###################################################################################

	# check to see if any motion detected
	if text == "Alert":
                # save frame
                cv2.imwrite("/tmp/PiSH_{}.jpg".format(motionCounter), frame);

                # check to see if enough time has passed between uploads
                if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:

                        # increment the motion counter
                        motionCounter += 1;

                        # check to see if the number of frames with consistent motion is
                        # high enough
                        if motionCounter >= int(conf["min_motion_frames"]):
                                # send an email if enabled
                                if conf["use_email"]:
                                        print("[INFO] Sending an alert email!!!")
                                        send_email(conf)
                                        print("[INFO] waiting {} seconds...".format(conf["camera_warmup_time"]))
                                        #time.sleep(conf["camera_warmup_time"])
                                        print("[INFO] running")

                                # update the last uploaded timestamp and reset the motion
                                # counter
                                lastUploaded = timestamp
                                motionCounter = 0

	# otherwise, no motion detected
	else:
		motionCounter = 0

	# check to see if the frames should be displayed to screen
	if conf["show_video"]:
		# display the security feed
		cv2.imshow("Security Feed", frame)
		key = cv2.waitKey(1) & 0xFF

		if debug_mode:
			cv2.imshow('Debug blurred gray frame', gray)
			cv2.imshow('Debug threshold frame', thresh)

		# if the `q` key is pressed, break from the lop
		if key == ord("q"):
			break

	# clear the stream in preparation for the next frame
	#rawCapture.truncate(0)#raspberry spec

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
