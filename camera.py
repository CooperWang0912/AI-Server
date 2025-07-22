import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0)

person_found = False

while not person_found:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    boxes = results[0].boxes
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        w, h = x2 - x1, y2 - y1
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        if label == "person" and w > 500 and h > 500:
            print(f"Label: {label}, Width: {w:.1f}, Height: {h:.1f}")
            person_found = True

    annotated_frame = results[0].plot()

    cv2.imshow("YOLOv8", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

import sounddevice as sd
from scipy.io.wavfile import write
import datetime

filename = datetime.datetime.now()

filename = str(filename) + ".wav"

freq = 16000
duration = 3

print("start talking")

recording = sd.rec(int(duration * freq), samplerate=freq, channels=1)

sd.wait()

write(filename, freq, recording)

import argparse
from dotenv import load_dotenv
import alibabacloud_oss_v2 as oss

import os

load_dotenv()

class CredentialProviderWrapper(oss.credentials.CredentialsProvider):
    def get_credentials(self):
        return oss.credentials.Credentials(os.getenv("OSS_ACCESS_KEY_ID"), os.getenv("OSS_ACCESS_KEY_SECRET"))

credentials_provider = CredentialProviderWrapper()
cfg = oss.config.load_default()
cfg.credentials_provider = credentials_provider

cfg.region = 'cn-shanghai'

client = oss.Client(cfg)

result = client.put_object_from_file(
    oss.PutObjectRequest(
        bucket="l-www",
        key="recording/test.wav"
    ),
    filepath=filename
)

pre_result = client.presign(
        oss.GetObjectRequest(
            bucket="l-www",
            key="recording/test.wav",
        )
    )

print(pre_result.url)

# ! /usr/bin/env python
# coding=utf-8
from dotenv import load_dotenv
import os
import time
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException

load_dotenv()

token = ""

client = AcsClient(
   ak=os.getenv('ALIYUN_AK_ID'),
   secret=os.getenv('ALIYUN_AK_SECRET'),
   region_id="cn-shanghai"
)

request = CommonRequest()
request.set_method('POST')
request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
request.set_version('2019-02-28')
request.set_action_name('CreateToken')

try:
   response = client.do_action_with_exception(request)
   # print(response)

   jss = json.loads(response)
   if 'Token' in jss and 'Id' in jss['Token']:
      token = jss['Token']['Id']
      expireTime = jss['Token']['ExpireTime']
      print("token = " + token)
      print("expireTime = " + str(expireTime))
except Exception as e:
   print(e)

def fileTrans(akId, akSecret, appKey, fileLink):
   REGION_ID = "cn-shanghai"
   PRODUCT = "nls-filetrans"
   DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
   API_VERSION = "2018-08-17"
   POST_REQUEST_ACTION = "SubmitTask"
   GET_REQUEST_ACTION = "GetTaskResult"
   KEY_APP_KEY = "appkey"
   KEY_FILE_LINK = "file_link"
   KEY_VERSION = "version"
   KEY_ENABLE_WORDS = "enable_words"
   KEY_AUTO_SPLIT = "auto_split"
   KEY_TASK = "Task"
   KEY_TASK_ID = "TaskId"
   KEY_STATUS_TEXT = "StatusText"
   KEY_RESULT = "Result"
   STATUS_SUCCESS = "SUCCESS"
   STATUS_RUNNING = "RUNNING"
   STATUS_QUEUEING = "QUEUEING"
   client = AcsClient(akId, akSecret, REGION_ID)
   postRequest = CommonRequest()
   postRequest.set_domain(DOMAIN)
   postRequest.set_version(API_VERSION)
   postRequest.set_product(PRODUCT)
   postRequest.set_action_name(POST_REQUEST_ACTION)
   postRequest.set_method('POST')
   task = {KEY_APP_KEY: appKey, KEY_FILE_LINK: fileLink, KEY_VERSION: "4.0", KEY_ENABLE_WORDS: False}
   task = json.dumps(task)
   print(task)
   postRequest.add_body_params(KEY_TASK, task)
   taskId = ""
   try:
      postResponse = client.do_action_with_exception(postRequest)
      postResponse = json.loads(postResponse)
      print(postResponse)
      statusText = postResponse[KEY_STATUS_TEXT]
      if statusText == STATUS_SUCCESS:
         print("Success")
         taskId = postResponse[KEY_TASK_ID]
      else:
         print("Failed")
         return
   except ServerException as e:
      print(e)
   except ClientException as e:
      print(e)
   getRequest = CommonRequest()
   getRequest.set_domain(DOMAIN)
   getRequest.set_version(API_VERSION)
   getRequest.set_product(PRODUCT)
   getRequest.set_action_name(GET_REQUEST_ACTION)
   getRequest.set_method('GET')
   getRequest.add_query_param(KEY_TASK_ID, taskId)
   statusText = ""
   while True:
      try:
         getResponse = client.do_action_with_exception(getRequest)
         getResponse = json.loads(getResponse)
         print(getResponse)
         statusText = getResponse[KEY_STATUS_TEXT]
         if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING:
            time.sleep(10)
         else:
            break
      except ServerException as e:
         print(e)
      except ClientException as e:
         print(e)
   if statusText == STATUS_SUCCESS:
      print("Success")
   else:
      print("Fail")
   return

accessKeyId = os.getenv('ALIYUN_AK_ID')
accessKeySecret = os.getenv('ALIYUN_AK_SECRET')
appKey = os.getenv('ALIYUN_APP_KEY')
fileLink = pre_result.url
fileTrans(accessKeyId, accessKeySecret, appKey, fileLink)