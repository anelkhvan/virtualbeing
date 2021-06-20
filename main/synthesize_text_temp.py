#!/usr/bin/env python

# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Google Cloud Text-To-Speech API sample application .

Example usage:
    python synthesize_text.py --text "hello"
    python synthesize_text.py --ssml "<speak>Hello there.</speak>"
"""

from logger import logger
import traceback
logger.info("Configuration loaded")

from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file("key.json")


# [START tts_synthesize_text]
def synthesize_text(text, audio_path, voices):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient(credentials=credentials)
    client = client.from_service_account_json("key.json")

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    # https://cloud.google.com/text-to-speech/docs/voices
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        #name="en-US-Standard-F", #en-US-Standard-B
        name=voices,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        # audio_encoding=texttospeech.AudioEncoding.MP3
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    logger.info("Audio synthetized")

    # The response's audio_content is binary.
    with open(audio_path, "wb") as out:
        out.write(response.audio_content)
        #print('Audio content written to file "output.mp3"')
        logger.info("Audio content written to file {}".format(audio_path))


# [END tts_synthesize_text]


if __name__ == "__main__":
    audio_path = "../Wav2Lip/temp/audio_temp.wav"
    text = "Thank you for listening to our presentation. If you have any questions or feedback, please feel free to ask him, not me."
    voices = "en-US-Standard-F"
    synthesize_text(text, audio_path, voices)

