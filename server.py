from typing import Union
from fastapi import FastAPI
import glob
import os
import json

import cv2
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from ultralytics import YOLO

from pydantic import BaseModel

import subprocess
import signal
camera_process = None

model = YOLO("yolov8n.pt")

from fastapi.staticfiles import StaticFiles

app = FastAPI()


@app.get("/api/speech_recognition")
def read_transcription():
    list_of_files = glob.glob('*.json')
    latest_file = max(list_of_files, key=os.path.getctime)
    result = json.load(open(latest_file))
    if result is None:
        return {
            "code": -1,
            "message": "Transcription failed",
            "content": "",
            "identify_people": ""
        }
    else:
        return{
            "code": 0,
            "message": "Get Transcription Success",
            "content": result,
            "identify_people": ""
        }

@app.get("/api/identify_people")
def read_identification():
    global camera_process

    camera_process = None

    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()

    cap.release()

    results = model(frame)

    boxes = results[0].boxes
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        w, h = x2 - x1, y2 - y1
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        if label == "person":
            return {
                "code": 0,
                "message": "Person Found",
                "person_found": True
            }
    return {
        "code": 0,
        "message": "Person Not Found",
        "person_found": False
    }

@app.post("/api/start_recording")
async def read_start_recording():
    global camera_process
    camera_process = subprocess.Popen(["python3", "ubuntu_test.py"])
    camera_process.wait()
    list_of_files = glob.glob('*.json')
    latest_file = max(list_of_files, key=os.path.getctime)
    result = json.load(open(latest_file))
    return {
        "code": 0,
        "message": "Recording Finished",
        "content": result
    }

@app.post("/api/stop_program")
async def stop_program():
    global camera_process
    if camera_process is not None:
        os.kill(camera_process.pid, signal.SIGKILL)
        camera_process = None
        return {
            "code": 0,
            "message": "Program Terminated"
        }
    else:
        return {
            "code": -1,
            "message": "Recording Process Not Running"
        }

@app.post("/api/clean_files")
async def clean_files():
    filenames = glob.glob('*.json')
    filenames += glob.glob('*.wav')
    for i in filenames:
        os.remove(i)
    return {
        "code": 0,
        "message": "Files Cleaned"
    }