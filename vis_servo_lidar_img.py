
import rospy as rp
import numpy as np
import cv2
import random
from sensor_msgs.msg import LaserScan, Image
from cv_bridge import CvBridge,CvBridgeError
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive

bridge = CvBridge()

drive_msg_stamped = AckermannDriveStamped()
drive_msg = AckermannDrive()
drive_msg.speed = 0.4
drive_msg.steering_angle = -1.0
drive_msg.acceleration = 1
drive_msg.jerk = 0
drive_msg.steering_angle_velocity = 0
drive_msg_stamped.drive = drive_msg
global proportional_error
global integral_error
global derivative_error

global active_lidar_in
global inactive_lidar_in
global left_lidar_pts
global right_lidar_pts
global previous_error


def callback2(data):
	global prepSwitch
	global direction
	global lastPixelDetectionX
	global lastPixelDetectionY
	in_scan = bridge.imgmsg_to_cv2(data,desired_encoding="passthrough")
	img0 = in_scan[0:367,0:1344]
	img = img0.copy()


	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	lowerYellow = np.array([25,170,120])
	upperYellow = np.array([35,255,200])

	lowerOrange = np.array([12,180,100])
	upperOrange = np.array([17,255,200])
	orangeMask = cv2.inRange(hsv,lowerOrange,upperOrange)
	yellowMask = cv2.inRange(hsv,lowerYellow,upperYellow)


	conemask = cv2.bitwise_and(img,img,mask=yellowMask)
	cubemask = cv2.bitwise_and(img,img,mask=orangeMask)

	graycone = cv2.cvtColor(conemask, cv2.COLOR_BGR2GRAY)
	graycube = cv2.cvtColor(cubemask, cv2.COLOR_BGR2GRAY)

	blurcone = cv2.GaussianBlur(graycone,(5,5),0)
	blurcube = cv2.GaussianBlur(graycube,(5,5),0)

	ret,conethresh = cv2.threshold(blurcone,0,255,cv2.THRESH_BINARY)
	ret2,cubethresh = cv2.threshold(blurcube,0,255,cv2.THRESH_BINARY)

	_,conecontours,_ = cv2.findContours(conethresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	_, cubecontours,_ = cv2.findContours(cubethresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	blk = np.zeros(img.shape).astype(img.dtype)
	blk2 = np.zeros(img.shape).astype(img.dtype)

	cv2.drawContours(blk, conecontours, -1, (255,0,255),3)
#	cv2.imshow("beforegreen",blk)

	cv2.drawContours(blk2, cubecontours,-1,(0,255,0),3)
#	cv2.imshow("aftergreen",blk2)
	found = False
	foundcube = False
	if (prepSwitch == False):

		if (direction == "RIGHT"):
			scanCol = [110,115,120,125,130,135,140]

		elif (direction == "LEFT"):
			scanCol = [1205,1210,1215,1220,1225,1230,1235]

		scanRow = 0
		counter = 0
		i = 0

		while i < 7:
			while found == False:


				scanPx = blk[scanRow,scanCol[i]]
				scanPx2 = blk2[scanRow,scanCol[i]]
				if (np.any(scanPx > (250,0,250))):
					print("Cone Value:",scanPx)

					found = True
				if (np.any(scanPx2 > (0,250,0))):
					print("Cube Value: ",scanPx)
					foundcube = True

				if (scanRow > 250):
					break

				scanRow+=random.randint(1,5)

			if (foundcube == True):
				if (found == True):
					print ("I see a cube but I also see a cone so I'm not gonna do anything about it")

				else:
					print("I only see the cube. I'm gonna turn around the cube.")
					prepSwitch = True
					lastPixelDetectionX = scanRow
					lastPixelDetectionY = scanCol[i]
					break
			i+=1
			if (found == True):
				prepSwitch = True
				print("I see a cone! Waiting for the cone to be in range")
				print(scanRow,scanCol[i])
				lastPixelDetectionX = scanRow
				lastPixelDetectionY = scanCol[i]
				break





	finalMask = cv2.addWeighted(blk,0.8,img,0.2,0)
	finalMask = cv2.addWeighted(blk2,0.8,finalMask,1,0)


#	cv2.imshow("oof",finalMask)

#	button = cv2.waitKey(25)
#	if button & 0xFF == ord('q'):
#		pass
	#	sys.exit()

def callback(data):

  global lidar_latch
  global active_lidar_in
  global left_lidar_pts
  global right_lidar_pts
  global inactive_lidar_in
  global prepSwitch
  global direction
  global lastPixelDetectionX
  global lastPixelDetectionY
  #print(data.ranges)
  a=0
 # b=0
 # c=0

  left_lidar_pts = np.sort(data.ranges[721:1011])
  right_lidar_pts = np.sort(data.ranges[69:360])

  if (direction == "RIGHT"):
	active_lidar_in = right_lidar_pts
	inactive_lidar_in = left_lidar_pts
  elif(direction == "LEFT"):
        active_lidar_in = left_lidar_pts
	inactive_lidar_in = right_lidar_pts
  '''
  for i in range(162,198):
    a+=data.ranges[i]
  for i in range(496,585):
    b+=data.ranges[i]
  for i in range(721,1080):
    c+=data.ranges[i]

  '''
  a/=36
  '''
  b/=90
  c/=360
  '''
  a=active_lidar_in[5]
  c = inactive_lidar_in[5]


  print("\x1b[2J")
  print("LEFT SIDE", c)
  print("RIGHT SIDE", a)
  print("Cone Seen:",prepSwitch)
  print("Current Direction:",direction)
  print("last cone detected at location:",lastPixelDetectionX, lastPixelDetectionY)
  print("")



  if (prepSwitch == True):
	#print("passed prepswitch test")
  	if (inactive_lidar_in[5] < 1.3):
		print("switching sides")
		switch_active_lidar()
       		prepSwitch = False


  process_pid(a)
  #print(data.ranges[i])
  #print(data.ranges[540])

def listener():
  rp.init_node('listener', anonymous=True)
  rp.Subscriber("/scan", LaserScan, callback)
  rp.Subscriber("left",Image, callback2)
  rp.spin()


def switch_active_lidar():
  global direction
  global active_lidar_in
  global inactive_lidar_in
  global left_lidar_pts
  global right_lidar_pts

  if (direction == "LEFT"):
     print("Switching direction to RIGHT")
     direction = "RIGHT"

  elif (direction == "RIGHT"):
     print ("Switching direction to LEFT")
     direction = "LEFT"



#def process_pid(left_side, right_side, front):
def process_pid(side):
	global direction
	kp = 2
	ki = 0.01
	kd = 0.01
	proportional_error = 0
	integral_error = 0
	derivative_error = 0
	previous_error = 0

	pub=rp.Publisher("/vesc/ackermann_cmd_mux/input/navigation",AckermannDriveStamped,queue_size=10)

	'''if front < 0.3:
		drive_msg.speed = 0
	elif front < 0.7:
		drive_msg.speed = 0.65 * front
	else:
		drive_msg.speed = 0.8'''
	drive_msg.speed = 0.8
	if (direction == "RIGHT"):
		dire = whichSideIsFurtherAway(.3, side)
	elif (direction == "LEFT"):
		dire = whichSideIsFurtherAway(side,.3)

	proportional_error = abs(side - .3)

	integral_error += proportional_error

	if (integral_error > .25):
		integral_error = 0
	if (proportional_error == 0):
		integral_error = 0

        derivative_error = proportional_error - previous_error
        previous_error = proportional_error

        out_angle = dire*(kp*proportional_error+ki*integral_error+kd*derivative_error)

	pub.publish(drive_msg_stamped)

	drive_msg.steering_angle = out_angle



def whichSideIsFurtherAway(left, right):
	if left > right:
		return 1
	elif left < right:
		return -1
	else:
		return 0



if __name__ == '__main__':

  lastPixelDetectionX = 0
  lastPixelDetectionY = 0
  prepSwitch = False
  proportional_error = 0
  integral_error = 0
  derivative_error = 0
  previous_error = 0
  lidar_latch = 0
  direction = "RIGHT"
  listener()
  cv2.destroyAllWindows()
