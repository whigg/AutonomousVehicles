import rospy as rp
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

bridge = CvBridge()

def callback(data):
  cv2.imshow("left_eye",bridge.imgmsg_to_cv2(data, desired_encoding="passthrough"))
  if cv2.waitKey(20) & 0xFF == ord('q'):
    pass

def listener():
  rp.init_node('listener', anonymous=True)
  rp.Subscriber("left", Image, callback)
  rp.spin()

if __name__ == '__main__':
  listener()
  cv2.destroyAllWindows()
