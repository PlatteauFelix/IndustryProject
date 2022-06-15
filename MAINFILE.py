from subprocess import Popen
from time import perf_counter
import math
from typing_extensions import Required
from datetime import datetime, timedelta
from collections import OrderedDict
from json import dumps, load
from moviepy.editor import *
import torch

### VARIABLES ###
# likely to change
var_matchName = 'TEST'              # name of match where everything gets saved in folder {var_projectName}/{var_matchName}
var_preClip = 4                     # seconds before goal in clip
var_postClip = 4                    # seconds after goal in clip
var_lockGoal = 15                   # seconds after goal when no new goal can be detected

# unlikely to change
var_projectName = 'RUNS'            # main folder where all matches will be saved
var_videoSourceCam1 = 'data/Videos/cam1.mp4'    # where cam1 is saved after livestream
var_videoSourceCam4 = 'data/Videos/cam4.mp4'    # where cam4 is saved after livestream
var_videoSourceCam6 = 'data/Videos/cam6.mp4'    # where cam5 is saved after livestream
var_livestreamCam4 = 'data/Videos/cam4.mp4'     # RTSP, RTMP, HTTP stream link of cam 4
var_livestreamCam6 = 'data/Videos/cam6.mp4'     # RTSP, RTMP, HTTP stream link of cam 4
var_saveDetects = True              # True = save detection video's, False = only save clips and timestamps goals
var_model = 'yolov5/TrainedModels/BestYolo.pt'               # location of our trained yolov5 model
var_confidence = 0.85               # minimum threshold of confidence






#---------------Detect goal---------------#
def detect(project, name, livestream_cam4, livestream_cam6, save, model, confidence):
    #check how many gpu's are present, else use cpu
    device1 = 0
    device2 = 0
    if torch.cuda.device_count() == 1:
        device1, device2 = 0, 0
    elif torch.cuda.device_count() == 2:
        device1, device2 = 0, 1
    else:
        device1, device2 = 'cpu', 'cpu'


    commands = []
    if save==False:
        commands.append(f"python yolov5/DetectYolo.py --project {project} --name {name} --max 1 --conf {confidence} --weights {model} --img 1080 --source {livestream_cam4} --nosave --exist-ok --device {device1}")
        commands.append(f"python yolov5/DetectYolo.py --project {project} --name {name} --max 1 --conf {confidence} --weights {model} --img 1080 --source {livestream_cam6} --nosave --exist-ok --device {device2}")
    elif save==True:
        commands.append(f"python yolov5/DetectYolo.py --project {project} --name {name} --max 1 --conf {confidence} --weights {model} --img 1080 --source {livestream_cam4} --line-thickness 2 --exist-ok --device {device1}")
        commands.append(f"python yolov5/DetectYolo.py --project {project} --name {name} --max 1 --conf {confidence} --weights {model} --img 1080 --source {livestream_cam6} --line-thickness 2 --exist-ok --device {device2}")
    processes = [Popen(cmd, shell=True) for cmd in commands]
    for p in processes: p.wait()

#---------------convert timestamp goal detection---------------#
def datahandler(path, lock_goal):
    goals = {}

    # remove duplicate timestamps and add goal lock of cam4
    previous = '00:00:00'
    with open(f'{path}/goals_cam4.txt', 'r') as file:
        for timestamp in file:
            timestamp = timestamp.strip()
            if timestamp!=previous and datetime.strptime(timestamp, "%H:%M:%S") > datetime.strptime(previous, "%H:%M:%S") + timedelta(seconds=lock_goal):
                goals[timestamp] = 'cam4'
                previous = timestamp
        file.close()

    # remove duplicate timestamps and add goal lock of cam6
    previous = '00:00:00'
    with open(f'{path}/goals_cam6.txt', 'r') as file:
        for timestamp in file:
            timestamp = timestamp.strip()
            if timestamp!=previous and datetime.strptime(timestamp, "%H:%M:%S") > datetime.strptime(previous, "%H:%M:%S") + timedelta(seconds=lock_goal):
                goals[timestamp] = 'cam6'
                previous = timestamp
        file.close()

    # sort timestamps
    goals = OrderedDict(sorted(goals.items()))

    # dump timestamps into json
    with open(f'{path}/goals.json', "w") as file:
        file.write(dumps(goals))
        file.close()

#---------------make clips from goals---------------#
def makeClips(source_cam1, source_cam4, source_cam6, path, pre_clip, post_clip):
    ### get timestamps from goals in form of totalseconds
    previous = '00:00:00'
    totalSeconds = 0
    timestamps = {}

    with open(f'{path}/goals.json', 'r') as file:
        data = load(file)
        for timestamp, cam in data.items():
            diff = (datetime.strptime(timestamp, "%H:%M:%S") - datetime.strptime(previous, "%H:%M:%S")).total_seconds()
            totalSeconds += diff
            timestamps[totalSeconds] = cam
            # print(diff)
            # print(totalSeconds)
            # print(timestamp)
            previous=timestamp
        file.close()

    ### cut clips and paste toghether
    videoCam1 = VideoFileClip(source_cam1)
    videoCam4 = VideoFileClip(source_cam4)
    videoCam6 = VideoFileClip(source_cam6)
    clips = []

    for timestamp, cam in timestamps.items():
        if cam == 'cam4':
            clips.append(videoCam1.subclip(timestamp-pre_clip, timestamp+post_clip))
            clips.append(videoCam4.subclip(timestamp-pre_clip, timestamp+post_clip))
        elif cam == 'cam6':
            clips.append(videoCam1.subclip(timestamp-pre_clip, timestamp+post_clip))
            clips.append(videoCam6.subclip(timestamp-pre_clip, timestamp+post_clip))

    print('Making clips.....')
    cut = concatenate_videoclips(clips)
    cut.write_videofile(f'{path}/clips.mp4')

def MAINFILE(project, name, source_cam1, source_cam4, source_cam6, livestream_cam4, livestream_cam6, pre_clip, post_clip, lock_goal, save, model, confidence):
    #region validation
    message = ''
    if not isinstance(project, str) or project=='':
        message += "ERROR: project name is invalid\n"

    if not isinstance(name, str) or name=='':
        message += "ERROR: name is invalid\n"
    
    if not isinstance(source_cam1, str) or source_cam1=='':
        message += "ERROR: source video cam1 invalid\n"

    if not isinstance(source_cam4, str) or source_cam4=='':
        message += "ERROR: source video cam4 invalid\n"

    if not isinstance(source_cam6, str) or source_cam6=='':
        message += "ERROR: source video cam6 invalid\n"

    if not isinstance(livestream_cam4, str) or livestream_cam4=='':
        message += "ERROR: livestream link cam4 invalid\n"

    if not isinstance(livestream_cam6, str) or livestream_cam6=='':
        message += "ERROR: livestream link cam6 invalid\n"

    if not isinstance(save, bool):
        message += "ERROR: set `True` to save detect videos\n"
    
    if isinstance(pre_clip, int):
        if pre_clip < 0:
            message += "ERROR: time before clip cannot be less than 0\n"
        if pre_clip > 15:
            message += "ERROR: time before after cannot be more than 15\n"
    else:
        message += "ERROR: pre_clip has to be a number\n"

    if isinstance(post_clip, int):
        if post_clip < 0:
            message += "ERROR: time after clip cannot be less than 0\n"
        if post_clip > 15:
            message += "ERROR: time after clip cannot be more than 15\n"
    else:
        message += "ERROR: post_clip has to be a number\n"

    if isinstance(lock_goal, int):
        if lock_goal < 15:
            message += "ERROR: time goal is locked cannot be less than 15\n"
        if lock_goal > 60:
            message += "ERROR: time goal is locked cannot be more than 60\n"
    else:
        message += "ERROR: lock_goal has to be a number\n"

    if not isinstance(model, str) or model=='':
        message += "ERROR: model source invalid\n"

    if isinstance(confidence, float):
        if confidence < 0.80:
            message += "ERROR: confidence cannot be less than 0.80\n"
        if confidence > 0.95:
            message += "ERROR: confidence cannot be more than 0.95\n"
    else:
        message += "ERROR: confidence has to be a number\n"
    #endregion

    if message == '':
        detect(project, name, livestream_cam4, livestream_cam6, save, model, confidence)
        path = f'{project}/{name}'
        datahandler(path, lock_goal)
        makeClips(source_cam1, source_cam4, source_cam6, path, pre_clip, post_clip)
    else:
        print(message)




# call function
start = perf_counter()

MAINFILE(var_projectName, var_matchName, var_videoSourceCam1, var_videoSourceCam4, var_videoSourceCam6, var_livestreamCam4, var_livestreamCam6, var_preClip, var_postClip, var_lockGoal, var_saveDetects, var_model, var_confidence)

end = perf_counter()
elapsedTimeSeconds = end-start
elapsedTimeSeconds = math.ceil(elapsedTimeSeconds)
elapsedTimeMinutes = elapsedTimeSeconds/60
elapsedTimeMinutes = math.floor(elapsedTimeMinutes)
elapsedDelta = elapsedTimeSeconds-elapsedTimeMinutes*60
elapsedDelta = math.ceil(elapsedDelta)
print(f'total elapsed time: {elapsedTimeSeconds}sec OR {elapsedTimeMinutes}min {elapsedDelta}sec')