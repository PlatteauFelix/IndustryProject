# IndustryProject
Industry project for Howest MCT AI in co-operation with DLC

---

# 1. Preperation

## 1.1 Make a venv
- python -m venv venv
- .\venv\Scripts\activate
- pip install -r .\requirements.txt
- pip install ipykernel
- python -m ipykernel install --user --name venv
- (optional) reload window
- select venv as kernel

## 1.2 Convert video(s) to frames
See ConvertToFrames folder, 
we each had a notebook to quickly convert videos and test.

## 1.3 Label images
- we used Vott to label ball for yolov5 and goal for unet.
- make dataset in roboflow
- upload images to dataset
- download in format needed for training

---

# 2. Training

## 2.1 Training Yolov5

In Training folder there are 2 notebooks for yolov5 training
Chose between local training or google colab and choose corresponding "training" notebook

## 2.2 Training Unet

There are 2 notebooks in the SegementationUnet folder.
the CreateMasksCoco notebook uses the coco segmentation format from roboflow to create the required images and corresponding masks needed to train Unet.

The Unet notebook is used to train a unet model locally.

---

# 3. Detection

## 3.1 Goal Detection
yolov5 is a object detector we use to find the ball.
the Ball detection happens in the DetectYolo.py in the yolov5 folder.
we used yolov5's detect.py as a base to build our project.
the final clips are also made in this file.


## 3.2 Goal Detection

To detect the goal we used Unet.
this gets called in the DetectYolo file but happens in DetectUnet.
A polygon is created from this goal detection wich is used to see if a ball is in the goal contours. 
there is a check that reruns the unet detect every 100 frames until a goal is found.
this starts an additional check that runs 3 times to use the biggest found polygon to prevent gaps in the goal contours.

---

# 4. Run model
to run the model u need video or livestream from the 2 cams above the goal and the camera following the game.
then u can just run the MAINFILE.py and that should do the trick.

---