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
Open "convert" notebook

## 1.3 Label images
- make dataset in roboflow
- upload images to dataset
- label images
- export or download to yolov5

---

# 2. Training

## 2.1 Train model
Chose between local training or in google colab and choose corresponding "training" notebook

---

# 3. Detection

## 3.1 Detect
Open "detect" notebook to test model on video