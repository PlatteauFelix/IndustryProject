# YOLOv5 🚀 by Ultralytics, GPL-3.0 license

from hashlib import new
from logging import Logger
import math
import argparse
import os
import sys
from pathlib import Path
from time import perf_counter, time

import torch
import torch.backends.cudnn as cudnn
from traitlets import default

from datetime import datetime, timedelta
from moviepy.editor import *
from collections import OrderedDict
from json import dumps, load
import time

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync

from shapely.geometry import Point, Polygon
import numpy as np
import DetectUnet

@torch.no_grad()
def run(
        weights=ROOT / 'yolov5s.pt',  # model.pt path(s)
        source=ROOT / 'data/images',  # file/dir/URL/glob, 0 for webcam
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference

        #---------------Sets goal-delay via parser---------------#
        lock_goal = 10,
        #---------------Sets time before and after clips via parser---------------#
        pre_clip = 10,
        post_clip = 10,

        source_cam1 = None

):

    poly = ""
    checkCount = 0


    start = perf_counter()
    source = str(source)
    source_cam1 = str(source_cam1)
    source_cam4 = None
    source_cam6 = None
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
    if is_url and is_file:
        source = check_file(source)  # download

 
    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
    
    #-----GoalDetectPath------# change for docker
    #pathGoalDetect = '../'
    pathGoalDetect = ROOT /'TrainedModels'
    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
        bs = len(dataset)  # batch_size
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
        bs = 1  # batch_size
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
    dt, seen = [0.0, 0.0, 0.0], 0

    for path, im, im0s, vid_cap, s in dataset:
        if 'cam4' in path and source_cam4 is None:
            source_cam4 = path
            poly=""
        if 'cam6' in path and source_cam6 is None:
            source_cam6 = path
            poly=""

        # print(source_cam1)
        # print(source_cam4)
        # print(source_cam6)

        t1 = time_sync()
        im = torch.from_numpy(im).to(device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        t2 = time_sync()
        dt[0] += t2 - t1

        # Inference
        visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
        pred = model(im, augment=augment, visualize=visualize)
        t3 = time_sync()
        dt[1] += t3 - t2

        # NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        dt[2] += time_sync() - t3

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            #--------------Gets seconds frome frame--------------#
            # print(vid_cap.get(cv2.CAP_PROP_FPS))
            time = frame / vid_cap.get(cv2.CAP_PROP_FPS)


            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()
                
                     #-----------sets coords/Visualizes goal-----------------#
            if poly == "":
                if frame == 1 or frame % 100 == 0:
                    poly = DetectUnet.FindGoalCoords(im0,pathGoalDetect).poly
                    checkCount = 0


            elif poly != "":
                if checkCount < 4 and frame % 100 == 0:
                    newPoly = DetectUnet.FindGoalCoords(im0,pathGoalDetect).poly
                    checkCount += 1
                    poly = poly if (newPoly == "") or (newPoly.area < poly.area) else newPoly

                int_coords = lambda x: np.array(x).round().astype(np.int32)
                exterior = [int_coords(poly.exterior.coords)]
                overlay = im0.copy()
                cv2.fillPoly(overlay, exterior, color=(255, 255, 0))
                cv2.addWeighted(overlay, 0.5, im0, 1 - 0.5, 0, im0)



                #---------------Added Coords and goals---------------#
                for *xyxy, conf, cls in reversed(det):
                    c1,c2 = (int(xyxy[0]),int(xyxy[1])),(int(xyxy[2]),int(xyxy[3]))
                    xCoord = round((c1[0]+c2[0])/2)
                    yCoord = round((c1[1]+c2[1])/2)
                    center_point = xCoord,yCoord
                    if Goal(xCoord,yCoord,save_dir,(math.trunc(time)),path,poly):
                        if 'cam4' in path:
                            text_Goal = cv2.putText(im0,f"Goal cam4",(450,150),cv2.FONT_HERSHEY_PLAIN,10,(0, 50, 255),10)
                        if 'cam6' in path:
                            text_Goal = cv2.putText(im0,f"Goal cam6",(450,150),cv2.FONT_HERSHEY_PLAIN,10,(0, 50, 255),10)
                
                


                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{center_point}{'s' * (n > 1)}, "  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                        with open(f'{txt_path}.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or save_crop or view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                    if save_crop:
                        save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)

            # Stream results
            im0 = annotator.result()
            if view_img:
                cv2.imshow(str(p), im0)
                cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer[i].write(im0)

        # Print time (inference-only)
        LOGGER.info(f'{s}Done. ({t3 - t2:.3f}s)')


    # Print results
    t = tuple(x / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    datahandler(save_dir, lock_goal)
    makeClips(source_cam1, source_cam4, source_cam6, save_dir, pre_clip, post_clip)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    else:
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}")

    if update:
        strip_optimizer(weights)  # update model (to fix SourceChangeWarning)
    
    end = perf_counter()
    elapsedTimeSeconds = end-start
    elapsedTimeSeconds = math.ceil(elapsedTimeSeconds)
    elapsedTimeMinutes = elapsedTimeSeconds/60
    elapsedTimeMinutes = math.floor(elapsedTimeMinutes)
    elapsedDelta = elapsedTimeSeconds-elapsedTimeMinutes*60
    elapsedDelta = math.ceil(elapsedDelta)
    print(f'total elapsed time: {elapsedTimeSeconds}sec OR {elapsedTimeMinutes}min {elapsedDelta}sec')



#---------------Create Timestamps---------------#

def getTimeStamp(sec):
    if sec < 1:
        return "00:00:00"
    else:
        mm, ss = divmod((sec), 60)
        hh, mm= divmod(mm, 60)
        return f"{(str(hh).rjust(2, '0'))}:{(str(mm).rjust(2, '0'))}:{(str(ss).rjust(2, '0'))}"


#---------------Goal detection---------------#

def Goal(x,y,save_dir,time,path,poly=""):
    if 'cam4' in path and poly != "":
        bal = Point(x,y)
        if bal.within(poly):
            with open(f'{save_dir}/goals_cam4.txt', 'a') as f:
                f.write(f'{getTimeStamp(time)}\n')
                f.close()
            return True
    elif 'cam6' in path and poly != "":
        bal = Point(x,y)
        if bal.within(poly):
            with open(f'{save_dir}/goals_cam6.txt', 'a') as f:
                f.write(f'{getTimeStamp(time)}\n')
                f.close()
            return True


#---------------convert timestamp goal detection---------------#
def datahandler(path, delay):
    goals = {}

    # remove duplicate timestamps and add goal lock of cam4
    previous = '00:00:00'
    with open(f'{path}/goals_cam4.txt', 'r') as file:
        for timestamp in file:
            timestamp = timestamp.strip()
            if timestamp!=previous and datetime.strptime(timestamp, "%H:%M:%S") > datetime.strptime(previous, "%H:%M:%S") + timedelta(seconds=delay):
                goals[timestamp] = 'cam4'
                previous = timestamp
        file.close()

    # remove duplicate timestamps and add goal lock of cam6
    previous = '00:00:00'
    with open(f'{path}/goals_cam6.txt', 'r') as file:
        for timestamp in file:
            timestamp = timestamp.strip()
            if timestamp!=previous and datetime.strptime(timestamp, "%H:%M:%S") > datetime.strptime(previous, "%H:%M:%S") + timedelta(seconds=delay):
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
def makeClips(source_cam1, source_cam4, source_cam6, path, preclip, postclip):
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
            clips.append(videoCam1.subclip(timestamp-preclip, timestamp+postclip))
            clips.append(videoCam4.subclip(timestamp-preclip, timestamp+postclip))
        elif cam == 'cam6':
            clips.append(videoCam1.subclip(timestamp-preclip, timestamp+postclip))
            clips.append(videoCam6.subclip(timestamp-preclip, timestamp+postclip))

    print('Making clips.....')
    cut = concatenate_videoclips(clips)
    cut.write_videofile(f'{path}/clips.mp4')



def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')

    #Add goal lock to arguments
    parser.add_argument('--lock-goal', type=int, default=30, help='sets locked time after goal, during this time no goal is recognized')

    #Add time before and after goal clips
    parser.add_argument('--pre-clip', type=int, default=10, help='sets time clips start before goal')
    parser.add_argument('--post-clip', type=int, default=10, help='sets time clips end after goal')

    parser.add_argument('--source-cam1', type=str, default=None, help='file location for cam1')


    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))


if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
