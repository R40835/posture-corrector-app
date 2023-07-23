import numpy as np
import requests
import cv2


# utility functions to draw the key points detected by 
# the moveNet model and the connection between them
def authenticate_user(url: str, port:str, email: str, password: str) -> str:
    '''
    checks if the user credential are correct before launching the program
    
    :param url: app url
    :param email: user email
    :param password: user password
    '''
    url = 'http://' + url + ':' + port + '/main/identify-camera/'
    data = {
        'email': email,
        'password': password,
        }
    response = requests.post(url, data=data)
    return response.json()['status']


def draw_keypoints(frame, keypoints, ct) -> None:
    '''draws key body parts detected by the moveNet model
    :param frame: video frame in the form of an array
    :param keypoints: key points detected
    :param ct: confidence threshold
    '''
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y,x,1]))
    
    for kp in shaped:
        ky, kx, kp_conf = kp
        if kp_conf > ct:
            cv2.circle(frame, (int(kx), int(ky)), 4, (0,255,0), -1) 


def draw_connections(frame, keypoints, ct) -> None:
    '''draws connections between body parts detected by the moveNet model
    :param frame: video frame in the form of an array
    :param keypoints: key points detected
    :param ct: confidence threshold
    '''
    EDGES = {
    (0, 1): 'm',
    (0, 2): 'c',
    (1, 3): 'm',
    (2, 4): 'c',
    (0, 5): 'm',
    (0, 6): 'c',
    (5, 7): 'm',
    (7, 9): 'm',
    (6, 8): 'c',
    (8, 10): 'c',
    (5, 6): 'y',
    (5, 11): 'm',
    (6, 12): 'c',
    (11, 12): 'y',
    (11, 13): 'm',
    (13, 15): 'm',
    (12, 14): 'c',
    (14, 16): 'c'
    }
    y, x, _ = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y,x,1]))
    
    for edge, _ in EDGES.items():
        p1, p2 = edge
        y1, x1, c1 = shaped[p1]
        y2, x2, c2 = shaped[p2]
        
        if (c1 > ct) & (c2 > ct):      
            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0,0,255), 2)