import cv2
import os
import numpy as np
from ffpyplayer.player import MediaPlayer
import argparse

import pyfakewebcam

parser = argparse.ArgumentParser(description='Default')
parser.add_argument('--silent', type=str, help='Silent video file', default="video/3.silent_me.mp4")
args = parser.parse_args()

virt_cam = 9
fake = pyfakewebcam.FakeWebcam(f'/dev/video{virt_cam}', 854, 480) #854 640 854 480

talking_video_file = "player/output.mp4"
#silent_video_file = "video/3.silent_me.mp4"
silent_video_file = args.silent


def is_talking():
    return os.path.isfile(talking_video_file)

ff_opts = {
}
isTalkingPlaying = False
video_stream = cv2.VideoCapture(silent_video_file)
audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)
frame_counter = 0

# Create a VideoCapture object and read from input file
while(True):

    # If new talking file reached
    if is_talking() and isTalkingPlaying is False:
        isTalkingPlaying = True
        frame_counter = 0
        video_stream = cv2.VideoCapture(talking_video_file, )
        audio_stream = MediaPlayer(talking_video_file, ff_opts=ff_opts)

    # If the last frame is reached, reset the capture and the frame_counter
    if frame_counter == video_stream.get(cv2.CAP_PROP_FRAME_COUNT):
        if isTalkingPlaying:
            # Return to loop the silent video and remove the file
            isTalkingPlaying = False
            video_stream = cv2.VideoCapture(silent_video_file)
            audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)
            os.remove(talking_video_file)
            frame_counter = 0
        else:
            # Loop the silent video
            frame_counter = 0  # Or whatever as long as it is the same as next line
            video_stream.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # Capture frame-by-frame
    ret, frame = video_stream.read()
    audio_frame, audio_val = audio_stream.get_frame(show=True)
    frame_counter += 1

    # Show
    try:
        if frame is not None:
            cv2.imshow('Frame', frame)
            cvt_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            fake.schedule_frame(cvt_frame)
        else:
            video_stream.release()
            frame_counter = 0
            isTalkingPlaying = False
            video_stream = cv2.VideoCapture(silent_video_file)
            audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)

    except:
        video_stream.release()
        frame_counter = 0
        isTalkingPlaying = False
        video_stream = cv2.VideoCapture(silent_video_file)
        audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)

    # Press Q on keyboard to  exit
    if cv2.waitKey(32) & 0xFF == ord('q'):
        break


# When everything done, release
video_stream.release()
cv2.destroyAllWindows()
