from os import listdir, path
import numpy as np
import scipy, cv2, os, sys, argparse
import json, subprocess, random, string
from tqdm import tqdm
from glob import glob
import torch
from Wav2Lip import face_detection, audio
from Wav2Lip.models import Wav2Lip
import platform
from main.synthesize_text import synthesize_text

import shutil
import wave
import contextlib

parser = argparse.ArgumentParser(description='Default')
parser.add_argument('--face', type=str, help='Filepath of video/image that contains faces to use', default="main/video/3.silent_me.mp4", required=False)
parser.add_argument('--audio', type=str, help='Filepath of video/audio file to use as raw audio source', default="Wav2Lip/temp/audio.wav", required=False)
#parser.add_argument('--outfile', type=str, help='Video path to save result. See default for an e.g.', default="./output/output.mp4")
parser.add_argument('--outfile', type=str, help='Video path to save result. See default for an e.g.', default="main/player/output.mp4")

parser.add_argument('--resize_factor', default=1, type=int, help='Reduce the resolution by this factor. Sometimes, best results are obtained at 480p or 720p')
parser.add_argument('--crop', nargs='+', type=int, default=[0, -1, 0, -1], help='Crop video to a smaller region (top, bottom, left, right). Applied after resize_factor and rotate arg. ' 'Useful if multiple face present. -1 implies the value will be auto-inferred based on height, width')
parser.add_argument('--rotate', default=False, action='store_true',help='Sometimes videos taken from a phone can be flipped 90deg. If true, will flip video right by 90deg.''Use if you get a flipped result, despite feeding a normal looking video')
args = parser.parse_args()

mel_step_size = 16


def load_data():
    if not os.path.isfile(args.face):
        raise ValueError('--face argument must be a valid path to video/image file')

    else:
        video_stream = cv2.VideoCapture(args.face)
        fps = video_stream.get(cv2.CAP_PROP_FPS)

        print("Reading video frames...")

        full_frames = []
        while 1:
            still_reading, frame = video_stream.read()
            if not still_reading:
                video_stream.release()
                break
            if args.resize_factor > 1:
                frame = cv2.resize(frame, (frame.shape[1]//args.resize_factor, frame.shape[0]//args.resize_factor))

            if args.rotate:
                frame = cv2.rotate(frame, cv2.cv2.ROTATE_90_CLOCKWISE)

            y1, y2, x1, x2 = args.crop
            if x2 == -1: x2 = frame.shape[1]
            if y2 == -1: y2 = frame.shape[0]

            frame = frame[y1:y2, x1:x2]

            full_frames.append(frame)

    print ("Number of frames available for inference: "+str(len(full_frames)))

    if not args.audio.endswith('.wav'):
        print('Extracting raw audio...')
        command = 'ffmpeg -y -i {} -strict -2 {}'.format(args.audio, 'Wav2Lip/temp/audio.wav')

        subprocess.call(command, shell=True)
        args.audio = 'Wav2Lip/temp/audio.wav'

    wav = audio.load_wav(args.audio, 16000)
    mel = audio.melspectrogram(wav)
    print(mel.shape)
    ''' trial #1'''
    afname = args.audio
    with contextlib.closing(wave.open(afname,'r')) as f:
        aframes = f.getnframes()
        arate = f.getframerate()
        aduration = aframes / float(arate)
        #aduration = int(aduration+0.5)
        print("Number of audio frames: ", aframes)
        print("Length: ", aduration)

    vframes = get_length('Wav2Lip/temp/result.mp4')
    print("Video length in frames: ", vframes)

    quotient = int( (aduration / vframes) + 0.5)
    remainder = int( (aduration % vframes) + 0.5)
    for i in range(quotient):
        print("i: ", i)

    if quotient > 0:
        #command = "ffmpeg -y -hwaccel cuvid -i {} -filter_complex loop=loop={}:size={}:start=0 {}".format('temp/result.mp4', quotient+1, vframes, 'temp/result2.mp4')
        command = "ffmpeg -y -hwaccel cuvid -stream_loop {} -i {} -c copy {}".format(quotient, 'Wav2Lip/temp/result.mp4', 'Wav2Lip/temp/result2.mp4')
        subprocess.call(command, shell=True)
        command = "ffmpeg -y -hwaccel cuvid -ss {} -t {} -i {} -c:v libx264 {}".format(0, aduration, 'Wav2Lip/temp/result2.mp4', 'Wav2Lip/temp/result3.mp4')
        #command = "ffmpeg -y -hwaccel cuvid -ss {} -i {} {}".format(aduration, 'temp/result2.mp4', 'temp/result3.mp4')
        subprocess.call(command, shell=True)

    else:
        command = "ffmpeg -y -hwaccel cuvid -ss {} -t {} -i {} -c:v libx264 {}".format(0, aduration, 'Wav2Lip/temp/result.mp4', 'Wav2Lip/temp/result3.mp4')
        subprocess.call(command, shell=True)

    
    #command = 'ffmpeg -y -hwaccel cuvid -i {} -i {} -strict -2 -q:v 1 {}'.format(args.audio, 'Wav2Lip/temp/result3.mp4', args.outfile)
    command = 'ffmpeg -y -hwaccel cuvid -i {} -i {} -strict -2 -q:v 1 {}'.format(args.audio, 'Wav2Lip/temp/result3.mp4', 'Wav2Lip/results/output.mp4')
    subprocess.call(command, shell=True)

    ########shutil.copy2("./output/output.mp4", "/home/r0-dt/Desktop/past_vb/identity-clonning/5_pipeline/video/output.mp4")
    shutil.copy2("Wav2Lip/results/output.mp4", "main/player/output.mp4")

def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

def process(text):
    synthesize_text(text, args.audio)
    #model, full_frames, fps = load_data()
    load_data()
    return args.outfile
    #return output_video_path

if __name__ == '__main__':
    text = "What's up, how is your new life? Is this better than previous?"
    process(text)



