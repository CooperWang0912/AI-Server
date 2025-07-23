from typing import Union
from fastapi import FastAPI
import glob
import os
import json

import cv2
from ultralytics import YOLO

from pydantic import BaseModel

model = YOLO("yolov8n.pt")

app = FastAPI()

@app.get("/")
def read_root():
    return {"Test"}


@app.get("/api/speech_recognition")
def read_transcription():
    list_of_files = glob.glob('*.json')
    latest_file = max(list_of_files, key=os.path.getctime)
    result = json.load(open(latest_file))
    if result["StatusText"] != "SUCCESS":
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
            "content": result["Result"]["Sentences"],
            "identify_people": ""
        }

@app.get("/api/identify_people")
def read_identification():
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
async def read_end_conversation():
    os.system("python3 camera.py")
    return {
        "code": 0,
        "message": "Started New Session"
    }
