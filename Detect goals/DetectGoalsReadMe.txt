Place in detectgoals.py and getCoordsFrame.py in yolov5 repo
place cam1, cam4 and cam6 video's in (same) folder
cd yolov5

command:
python detectGoals.py --conf 0.81 --weights ..\best.pt --img 1080 --source ..\cam[4,6]*.mp4 --source-cam1 ..\cam1.mp4 --lock-goal 15


python detectGoals.py --conf 0.81 --weights ..\best.pt --img 1080 --source ..\cam[4,6]*.mp4 --source-cam1 ..\cam1.mp4 --lock-goal 15 --pre-clip 10 --post-clip 10 --nosave