import cv2
import numpy as np

# img = cv2.imread("images/logo.png",0)   # black / white
img = cv2.imread("images/logo.png",1)

cv2.namedWindow("image_logo", cv2.WINDOW_NORMAL)

cv2.imshow("image_logo", img)
cv2.waitKey(0)
cv2.destroyAllWindows()