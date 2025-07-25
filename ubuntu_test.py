import os
import sys
import signal
import sounddevice as sd
import numpy as np
import queue

import dashscope
from dashscope.audio.asr import *
from dotenv import load_dotenv

import time

load_dotenv()
dashscope.api_key = os.getenv("DASH_API_KEY")

sample_rate = 16000
channels = 1
dtype = 'int16'
block_size = 3200
format_pcm = 'pcm'

audio_q = queue.Queue()

conversation_end = False

transcription_results = []

start_time = None
cur_time = None
actual_start_time = None

class Callback(RecognitionCallback):
    def on_open(self) -> None:
        print('RecognitionCallback open.')

    def on_close(self) -> None:
        print('RecognitionCallback close.')

    def on_complete(self) -> None:
        print('RecognitionCallback completed.')

    def on_error(self, message) -> None:
        print('RecognitionCallback task_id:', message.request_id)
        print('RecognitionCallback error:', message.message)
        sys.exit(1)

    def on_event(self, result: RecognitionResult) -> None:
        global conversation_end
        global transcription_results
        global start_time
        global cur_time
        global actual_start_time
        sentence = result.get_sentence()
        if 'text' in sentence:
            start_time = time.time()
            print('RecognitionCallback text:', sentence['text'])
            if RecognitionResult.is_sentence_end(sentence):
                print('RecognitionCallback sentence end,', sentence['text'])
                transcription_results.append(sentence['text'])
                if cur_time - actual_start_time > 20:
                    conversation_end = True


def audio_callback(indata, frames, time, status):
    if status:
        print("Audio callback status:", status, file=sys.stderr)
    audio_q.put(indata.copy().tobytes())

def signal_handler(sig, frame):
    print('Ctrl+C pressed, stopping translation...')
    recognition.stop()
    print('Translation stopped.')
    print('[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'.format(
        recognition.get_last_request_id(),
        recognition.get_first_package_delay(),
        recognition.get_last_package_delay()))
    sys.exit(0)

callback = Callback()
recognition = Recognition(
    model='paraformer-realtime-v2',
    format=format_pcm,
    sample_rate=sample_rate,
    semantic_punctuation_enabled=False,
    callback=callback
)

recognition.start()
signal.signal(signal.SIGINT, signal_handler)

print("Press Ctrl+C to stop recording and translation...")

start_time = time.time()

actual_start_time = time.time()

with sd.InputStream(samplerate=sample_rate,
                    channels=channels,
                    dtype=dtype,
                    blocksize=block_size,
                    callback=audio_callback):
    while not conversation_end:
        cur_time = time.time()
        data = audio_q.get()
        recognition.send_audio_frame(data)
        if cur_time - start_time > 3:
            conversation_end = True


import datetime
import json

json_name = str(datetime.datetime.now()) + ".json"

recognition.stop()
with open(json_name, "w") as final:
    json.dump({"data": transcription_results}, final)