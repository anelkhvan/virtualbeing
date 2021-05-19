#!/usr/bin/env python

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample application using the streaming API.

NOTE: This module requires the dependencies `pyaudio` and `termcolor`.
To install using pip:

    pip install pyaudio
    pip install termcolor

Example usage:
    python transcribe_streaming_infinite.py
"""

# [START speech_transcribe_infinite_streaming]

import json
import os
import re
import sys
import time

from google.cloud import speech
import pyaudio
from six.moves import queue
import requests
from google.oauth2 import service_account

from typing import Dict, Text, Any, List
import logging
logger = logging.getLogger(__name__)

credentials = service_account.Credentials.from_service_account_file("key.json")

# Server URL from where you get the generated video of the person talking the given sentence
#AI_server = "http://GPU-server-address"
AI_server = "http://localhost"

## CONFIGS
url = "http://localhost:5005/webhooks/rest/webhook"
error_message = "I don't understand. Please ask something else."
cacheFolderName = "video/source/new/cache/"
talking_video_file = "video/output.mp4"

# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"

def is_talking():
    return os.path.isfile(talking_video_file)

class InitializeParlAIAction():
    """This action class allows to display buttons for each facility type
    for the user to chose from to fill the facility_type entity slot."""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_initialize_ParlAI"

    def run(self) -> List:
        sendToParlAI('begin')
        sendToParlAI('begin')
        sendToParlAI('begin')
        logger.debug("action_initialize_ParlAI initilize")
        return []

parlAI_base_url = "http://localhost:8080"
def sendToParlAI(user_message, silentMode=False):
    url = "{}/interact".format(parlAI_base_url)
    headers = {'Content-Type': 'application/json'}
    response_text = ""
    if silentMode:
        asyncReq(url, headers=headers, data=user_message)
    else:
        import requests
        response = requests.request("POST", url, headers=headers, data=user_message)
        import json
        response_json = json.loads(response.text)
        response_text = response_json['text']
        #print(response_text)
        logger.debug("send_message_to_ParlAI: message - {}".format(response_text))

    return response_text


"""
def getResponseFromRasa(person, message):
    payload = {"sender": person, "message": message}
    payload = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    response = response.text.encode('utf8')
    response = json.loads(response)
    responseString = ""
    for message in response:
        responseString = responseString + message['text'] + "\n"

    return responseString
"""

#def process_text(senderName, input):
def process_text(input):
    
    try:
        #response = getResponseFromRasa(senderName, input)
        response = sendToParlAI(input)
    except:
        response = error_message
    #response = sendToParlAI(input)
    return response


"""
def generateFileName(responseMessage):
    filename = ""
    if (responseMessage and len(responseMessage.strip()) > 0):
        responseMessage = responseMessage.strip()
        import hashlib
        filename = hashlib.md5(responseMessage.encode('utf-8')).hexdigest()
        #print("{0} : {1}".format(responseMessage, filename))
    return filename.strip()
"""


"""
def downloadfile(url, srcFileName, dstFileName):
    print("****Connected****")
    # try:
    r = requests.get(url)

    # 1.mp4 to be played by the streamer
    f1 = open(dstFileName, 'wb')

    # Store it in the cache server for future use
    f2 = open(srcFileName, 'wb')

    print("Dowloading.....")
    for chunk in r.iter_content(chunk_size=255):
        if chunk:  # filter out keep-alive new chunks
            f1.write(chunk)
            f2.write(chunk)
    print("Done")
    f1.close()
    f2.close()
"""

def getVideoResponse(text):
    """
    srcFileName = cacheFolderName + generateFileName(text) + ".mp4"
    #print(srcFileName)
    
    if os.path.isfile(srcFileName):
        print("Play from local...")
        from shutil import copyfile
        copyfile(srcFileName, talking_video_file)
    else:
        #print("Download from AI...")
        url = "{}:5000/render?text={}".format(AI_server, text)
        #print(url)
        r = requests.get(url)

        
        try:
            downloadfile(url, srcFileName, talking_video_file)
            return
        except:
            getVideoResponse(error_message)"""
    url = "{}:5000/render?text={}".format(AI_server, text)
    r = requests.get(url)
    return

def get_current_time():
    """Return Current Time in MS."""

    return int(round(time.time() * 1000))


class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk_size):
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

    def __enter__(self):

        self.closed = False
        return self

    def __exit__(self, type, value, traceback):

        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, *args, **kwargs):
        """Continuously collect data from the audio stream, into the buffer."""

        if not is_talking():
            self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        """Stream Audio from microphone to API and to local buffer"""

        while not self.closed:
            data = []

            if self.new_stream and self.last_audio_input:

                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:

                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset)
                        / chunk_time
                    )

                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            data.append(chunk)
            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)

                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses, stream):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """

    for response in responses:
        #print("RESPONSE.RESULTS[0]_{}".format(response.results[0:4]))
        if get_current_time() - stream.start_time > STREAMING_LIMIT:
            stream.start_time = get_current_time()
            break

        if not response.results:
            continue

        result = response.results[0]

        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        result_seconds = 0
        result_micros = 0

        if result.result_end_time.seconds:
            result_seconds = result.result_end_time.seconds

        if result.result_end_time.microseconds:
            result_micros = result.result_end_time.microseconds

        stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

        corrected_time = (
            stream.result_end_time
            - stream.bridging_offset
            + (STREAMING_LIMIT * stream.restart_counter)
        )
        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.

        if result.is_final:

            sys.stdout.write(GREEN)
            sys.stdout.write("\033[K")
            sys.stdout.write(str(corrected_time) + ": " + transcript + "\n")

            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                sys.stdout.write(YELLOW)
                sys.stdout.write("Exiting...\n")
                stream.closed = True
                break

            else:
                if transcript[0] == " ":
                    transcript = transcript[1:]
                #transcript = transcript.strip()
                if transcript != "":
                    print("TRANSCRIPT_{}".format(transcript))
                    response_text = process_text(transcript)
                    response_text = response_text.replace("'", "").replace("  ", "")
                    #response_text = response_text.replace("  ", "")
                    print("Response: {}".format(response_text))
                    if response_text and len(response_text) > 0:
                        getVideoResponse(response_text)

        else:
            sys.stdout.write(RED)
            sys.stdout.write("\033[K")
            sys.stdout.write(str(corrected_time) + ": " + transcript + "\r")

            stream.last_transcript_was_final = False


def main():
    """start bidirectional streaming from microphone input to speech API"""

    client = speech.SpeechClient(credentials=credentials)
    #client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",
        max_alternatives=1,
        enable_automatic_punctuation=False,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    print(mic_manager.chunk_size)
    sys.stdout.write(YELLOW)
    sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
    sys.stdout.write("End (ms)       Transcript Results/Status\n")
    sys.stdout.write("=====================================================\n")

    with mic_manager as stream:

        while not stream.closed:
            sys.stdout.write(YELLOW)
            sys.stdout.write(
                "\n" + str(STREAMING_LIMIT * stream.restart_counter) + ": NEW REQUEST\n"
            )

            stream.audio_input = []
            audio_generator = stream.generator()

            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            listen_print_loop(responses, stream)

            if stream.result_end_time > 0:
                stream.final_request_end_time = stream.is_final_end_time
            stream.result_end_time = 0
            stream.last_audio_input = []
            stream.last_audio_input = stream.audio_input
            stream.audio_input = []
            stream.restart_counter = stream.restart_counter + 1

            if not stream.last_transcript_was_final:
                sys.stdout.write("\n")
            stream.new_stream = True


if __name__ == "__main__":

    main()

# [END speech_transcribe_infinite_streaming]