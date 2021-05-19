import cv2
import os
import numpy as np
from ffpyplayer.player import MediaPlayer
import time

import pyfakewebcam
from capture import VideoCaptureThreading

talking_video_file = "video/output.mp4"
silent_video_file = "video/3.silent_me.mp4"

def is_talking():
    return os.path.isfile(talking_video_file)

ff_opts = {
}
isTalkingPlaying = False
cap = VideoCaptureThreading(silent_video_file)
#cap = VideoCaptureThreading(-1)
cap.start()
#cap = cv2.VideoCapture(silent_video_file)
#audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)
print(cap.get(cv2.CAP_PROP_FPS))
print(cap.get(cv2.CAP_PROP_FRAME_COUNT))

while cap.isOpened():
    (ret, frame) = cap.read()
    if ret == True:
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    else:
        break


cap.stop()
#cap.release()
cv2.destroyAllWindows

