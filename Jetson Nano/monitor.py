import numpy as np
import cv2
from corrector import PostureCorrector
from utils import draw_connections, draw_keypoints
from corrector import PostureCorrector
import getpass
import requests
import time


def authenticate_user(url: str, email: str, password: str) -> str:
    '''
    checks if the user credential are correct before launching the program
    
    :param url: app url
    :param email: user email
    :param password: user password
    '''
    url = 'http://' + url + ':5000/main/identify-camera/'
    data = {
        'email': email,
        'password': password,
        }
    response = requests.post(url, data=data)
    return response.json()['status']


options = 'Please choose a camera position to be monitored from. Your options are as follows:\n\n \
              1 ---> [lateral right]\n \
              2 ---> [frontal]\n \
              3 ---> [lateral left]\n \
              \n'
# pass in the url the ip address used to host the django app 
# (before running this script run the django app server; it has to be listening on port 5000)
url = ''
email = ''
password = ''
camera_position = 0
print('Please enter your account email and password to be authenticated.' +'\n')
while 1:
    email = str(input('Enter your email: '))
    password = getpass.getpass(prompt='Enter your password: ')
    if authenticate_user(url, email, password) == 'user identified':
        print('\n' + 'Authentication successful' + '\n')
        print(options)
        while 1:
            camera_position = int(input('Enter your camera position choice: '))
            if (camera_position == 1) | (camera_position == 2) | (camera_position == 3):
                if camera_position == 1:
                    print('\n' + 'Camera configured to [lateral right]' + '\n')
                elif camera_position == 2:
                    print('\n' + 'Camera configured to [frontal]' + '\n')
                elif camera_position == 3:
                    print('\n' + 'Camera configured to [lateral left]' + '\n')
                print('Launching Program...' + '\n')
                break
            else:
                print('\nError: Incorrect option.\n\n' + options)
        break
    else:
        print('\n' + 'Authentication Error: Incorrect email or password, please try again.' + '\n')

# creating an instance of the class defined in corrector.py
pose = PostureCorrector(
                    url=url, 
                    email=email, 
                    password=password,
                    camera_position=camera_position, 
                    fps=30, 
                    duration=10
                    )
# Open the CS2 camera and start capturing frames
cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM),width=3280,height=2464,format=NV12,framerate=21/1 \
                        ! nvvidconv flip-method=2 ! video/x-raw, width=(int)640, height=(int)480, format=(string)BGRx \
                       ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")
while cap.isOpened():
    ret, frame = cap.read()

    # Preprocess the input image
    img = cv2.resize(frame, (256, 256))
    img = img.astype(np.float32)
    img = np.expand_dims(img, axis=0)

    # detect body key joint
    pose.detect(img)
    keypoints_with_scores = pose.keypoints_with_scores
    # Render the output keypoints and drawing connections
    draw_connections(frame, keypoints_with_scores, 0.4)
    draw_keypoints(frame, keypoints_with_scores, 0.4)
    # detection of the current posture
    pose.posture_corrector(frame)
    # update frames for photos if incorrect postures last 10 seconds
    pose.frame = frame
    # render neck and back postures on frames
    if len(pose.back_status) > 1:
        text = f"back posture: {pose.back_status[len(pose.back_status) - 1]}"
        cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    if len(pose.neck_status) > 1:
        text2 = f"neck posture: {pose.neck_status[len(pose.neck_status) - 1]}"
        cv2.putText(frame, text2, (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2) 

    # pop up monitoring screen
    cv2.imshow('trt', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

end_time = int(time.time())

# exceptions handling
try:
    pose._upload_photos()
except:
    print('No photos existing')
try:
    pose._clean_folder()
except:
    print('Couldn\'t clean folder')
try:
    pose._update_database(end_time)
except:
    print('Couldn\'t update database')
