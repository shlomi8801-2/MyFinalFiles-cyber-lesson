import cv2

# open video file
print("trying to acuire video")
video = cv2.VideoCapture('video/steel-balls-moving.mp4')

# video = cv2.VideoCapture(0)

# Initialize algorithm fo the background removing
background_subtractor = cv2.createBackgroundSubtractorMOG2()

while True:
    # Frames reading
    ret, frame = video.read()
    if not ret:
        break

    # Background removing
    fg_mask = background_subtractor.apply(frame)

    # Noise removing
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    # Contours detection
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Rectangle drawing
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Frame drawing with object were detected
    cv2.imshow('Detected Objects', frame)

    # Exit from the loop upon key pressing - 'q'
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

# Free resources
video.release()
cv2.destroyAllWindows()
