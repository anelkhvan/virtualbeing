import cv2
import os
import numpy as np
from ffpyplayer.player import MediaPlayer

import pyfakewebcam
from capture import VideoCaptureThreading

virt_cam = 9


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
audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)
frame_count = 0


(ret, frame) = cap.read()
stream_img_size = frame.shape[1], frame.shape[0]
fake = pyfakewebcam.FakeWebcam(f'/dev/video{virt_cam}', *stream_img_size)



print(cap.get(cv2.CAP_PROP_FPS))
print(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
while cap.isOpened():
#while True:

    if is_talking() and isTalkingPlaying is False:
        isTalkingPlaying = True
        frame_count = 0
        cap = VideoCaptureThreading(talking_video_file, )
        cap.start()
        audio_stream = MediaPlayer(talking_video_file, ff_opts=ff_opts)

    if frame_count == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        if isTalkingPlaying:
            isTalkingPlaying = False
            cap = VideoCaptureThreading(silent_video_file)
            cap.start()
            audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)
            os.remove(talking_video_file)
            frame_count = 0

        else:
            frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    (ret, frame) = cap.read()
    audio_frame, audio_val = audio_stream.get_frame(show=True)
    frame_count += 1

    try:
        if ret == True:
            cv2.imshow("Frame", frame)
            #print(frame_count)
            cvt_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            fake.schedule_frame(cvt_frame)

        else:
            print("TRY1")
            frame_count = 0
            isTalkingPlaying = False
            cap.stop()
            #cap.release()
            cap = VideoCaptureThreading(silent_video_file)
            cap.start()
            audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)

    except:
        print("EXCEPT1")
        frame_count = 0
        isTalkingPlaying = False
        cap.stop()
        #cap.release()
        cap = VideoCaptureThreading(silent_video_file)
        cap.start()
        audio_stream = MediaPlayer(silent_video_file, ff_opts=ff_opts)

    if cv2.waitKey(32) & 0xFF == ord('q'):
        break


    '''
    if ret == True:
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    else:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        #break'''
#cap.release()
cap.stop()
print("down ehre")
cv2.destroyAllWindows

