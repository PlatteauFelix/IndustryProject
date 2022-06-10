import subprocess

def MAINFILE(project=None, name=None, source=None, source_cam1=None, save=False, pre_clip=4, post_clip=4, lock_goal=15, model='best.pt', confidence=0.81):
    #region validation
    message = ''
    if not isinstance(project, str) or project=='':
        message += "ERROR: project name is invalid\n"

    if not isinstance(name, str) or name=='':
        message += "ERROR: name is invalid\n"

    if not isinstance(source, str) or source=='':
        message += "ERROR: cam4 and cam6 source invalid\n"

    if not isinstance(source_cam1, str) or source_cam1=='':
        message += "ERROR: cam1 source invalid\n"

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
        if save==False:
            command = f"python yolov5/detectGoals.py --project {project} --name {name} --max 1 --conf {confidence} --weights {model} --img 1080 --source {source} --source-cam1 {source_cam1} --lock-goal {lock_goal} --pre-clip {pre_clip} --post-clip {post_clip} --nosave --view-img"
        elif save==True:
            command = f"python yolov5/detectGoals.py --project {project} --name {name} --max 1 --conf {confidence} --weights {model} --img 1080 --source {source} --source-cam1 {source_cam1} --lock-goal {lock_goal} --pre-clip {pre_clip} --post-clip {post_clip} --line-thickness 2"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    else:
        print(message)



# call function
MAINFILE(project='RUNS', name='Match_X', source = 'cam[4,6]*.mp4', source_cam1='cam1.mp4', save=False)