from model import MoveNetModel
from post_requests import DjangoAppSession
import numpy as np
import time
import math
import cv2
import os 


class PostureCorrector(MoveNetModel):
    '''
    * This Class works by loading the moveNet model from Tensorflow and detects 17 body key joints.
    * The body key joints are used to calculate angles and distances used as thresholds to estimate incorrect postures.
    * The model has been optimised to run on the jetson nano by converting it to ONNX and then to a TensorRT engine 
    used to run inference.
    * This runs only on the Jetson Nanos as the optimised model's file (engine.trt) is tailored to the Jetson Nano's 
    GPU architecture.
    '''

    def __init__(self, url: str, port:str, email: str, password: str, camera_position: int=1, fps: int=None, duration: int=10):
        super().__init__()
        self.__duration = duration 
        self.__num_frames = int(self.__duration * fps) / 2
        self.__CAMERA_POSITION = camera_position
        self.__frame = None
        self.__neck_status = np.array([])
        self.__back_status = np.array([])
        self.__photos_counter = 0
        self.__back_counter = 0
        self.__neck_counter = 0
        self.__app = DjangoAppSession(
                                url=url,
                                port=port,
                                email=email,
                                password=password
                                    )

    @property
    def frame(self) -> np.array:
        return self.__frame 
    
    @property
    def neck_status(self) -> np.array:
        return self.__neck_status

    @property
    def back_status(self) -> np.array:
        return self.__back_status
        
    @property
    def app(self) -> object:
        return self.__app 

    @frame.setter
    def frame(self, frame: np.array) -> None:
        self.__frame = frame 

    def monitor_posture(self) -> None:
        '''
        monitors posture of the subject depending on the camera position selected
        the surveillance is performed in segments of 10 seconds. if the subject
        happens to be in an improper posture during the whole time he/she will 
        be notified.
        '''
        # lateral right or left posture correction
        if (self.__CAMERA_POSITION == 1) | (self.__CAMERA_POSITION == 3):
            neck_state = self._lateral_neck_corrector()
            back_state = self._lateral_back_corrector()
                
            # checking if 10 seconds were spent in a poor posture:
            # the timer method takes results of the predictions (1 or 0) 
            # and triggers the alarm by sending a post request 
            # to the django app if the incorrect posture was predicted 
            # for all the frames generated in 10 seconds 
            self._timer(back_state, self.__num_frames, 'back')
            self._timer(neck_state, self.__num_frames, 'neck')
        elif self.__CAMERA_POSITION == 2 : 
            neck_state = self._frontal_neck_corrector()
            back_state = self._frontal_back_corrector()
                
            # checking if 10 seconds were spent in a poor posture
            self._timer(back_state, self.__num_frames, 'back')
            self._timer(neck_state, self.__num_frames, 'neck')

    def _frontal_neck_corrector(self) -> int:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        n = self.parts_coordinates['nose']
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']

        right_shoulder_angle = self.angle_calculator(p1=n, p2=rs, p3=ls)
        left_shoulder_angle = self.angle_calculator(p1=n, p2=ls, p3=rs)

        # 325 is the same angle threshold as 35 it is just inverted
        if (35 < right_shoulder_angle) & (left_shoulder_angle < 325):
            self.__neck_status = np.append(self.__neck_status, 'upright neck')
            return 1
        self.__neck_status = np.append(self.__neck_status, 'forward-leaning neck')
        return 0

    def _lateral_neck_corrector(self) -> int:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        nose_y = self.parts_coordinates['nose'][1]
        left_shoulder_y = self.parts_coordinates['left_shoulder'][1]
        right_shoulder_y = self.parts_coordinates['right_shoulder'][1]

        # Compare the y-coordinates to determine if the subject is sat upright
        # We'll use a range of 10 pixels to allow for some variability in how people sit on chairs
        if (abs(nose_y - left_shoulder_y) < .08) & (abs(nose_y - right_shoulder_y) < .08):
            self.__neck_status = np.append(self.__neck_status, 'forward-leaning neck') 
            return 0
        
        # storing neck posture result
        self.__neck_status = np.append(self.__neck_status, 'upright neck') 
        return 1
    
    def _frontal_back_corrector(self) -> int:
        '''checks correct back posture returns 0 for incorrect and 1 for correct posture'''
        
        # coordinates of left and right shoulders, left and right hips, and nose
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']
        lh = self.parts_coordinates['left_hip']
        rh = self.parts_coordinates['right_hip']
        nose = self.parts_coordinates['nose']

        # calculating distances between shoulders and hips
        left_shoulder_hip_dist = self.euclidean_distance(x1=ls[0], x2=lh[0], y1=ls[1], y2=lh[1])
        right_shoulder_hip_dist = self.euclidean_distance(x1=rs[0], x2=rh[0], y1=rs[1], y2=rh[1])
        shoulder_hip_dist = left_shoulder_hip_dist + right_shoulder_hip_dist
        # calculating distances between nose and hips
        left_nose_hip_dist = self.euclidean_distance(x1=nose[0], x2=lh[0], y1=nose[1], y2=lh[1]) 
        right_nose_hip_dist = self.euclidean_distance(x1=nose[0], x2=rh[0], y1=nose[1], y2=rh[1]) 
        nose_hip_dist = left_nose_hip_dist + right_nose_hip_dist

        # compare the distances
        if nose_hip_dist < shoulder_hip_dist:
            self.__back_status = np.append(self.__back_status, 'froward-leaning back') 
            return 0
        elif nose_hip_dist > shoulder_hip_dist:
            self.__back_status = np.append(self.__back_status, 'upright back') 
            return 1
            
    def _lateral_back_corrector(self) -> int:
        '''checks correct back posture returns 0 for incorrect and 1 for correct posture'''

        # retrieving coordinates arrays of relevant body parts
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']
        lh = self.parts_coordinates['left_hip']
        rh = self.parts_coordinates['right_hip']
        lk = self.parts_coordinates['left_knee']
        rk = self.parts_coordinates['right_knee']

        # lateral right
        if self.__CAMERA_POSITION == 1:
            # right hip angle
            right_hip_angle = self.angle_calculator(p1=rs, p2=rh, p3=rk)

            if 90 < right_hip_angle < 115: 
                self.__back_status = np.append(self.__back_status, 'upright back') 
                return 1
            elif right_hip_angle < 90: 
                self.__back_status = np.append(self.__back_status, 'froward-leaning back') 
                return 0
            elif right_hip_angle > 115: 
                self.__back_status = np.append(self.__back_status, 'reclined back') 
                return 0
            
        # lateral left
        elif self.__CAMERA_POSITION == 3:
            # left hip angle same angles are used as thresholds there just inverted
            left_hip_angle = self.angle_calculator(p1=ls, p2=lh, p3=lk)

            if 245 < left_hip_angle < 270: 
                self.__back_status = np.append(self.__back_status, 'upright back') 
                return 1
            elif left_hip_angle < 245: 
                self.__back_status = np.append(self.__back_status, 'reclined back') 
                return 0
            elif left_hip_angle > 270: 
                self.__back_status = np.append(self.__back_status, 'forward-leaning back') 
                return 0

    def _timer(self, current_status: int, num_frames: int, counter_type: str) -> None:
        '''
        triggers the alarm on the user interface, and store the incorrect posture
        sustained by the user for 10 seconds
        
        :param current_status: 1 or 0 for proper or improper posture
        :param num_frames: the number of frames to be processed 
            for the timer to send a notification
        :param counter_type: back or neck
        '''
        # If the current status is the same as the previous status, increment the counter
        if counter_type == 'back':
            counter = self.__back_counter
        elif counter_type == 'neck':
            counter = self.__neck_counter

        if current_status == 0:
            counter += 1
        else:
            # If the current status is different from the previous status, reset the counter
            counter = 0

        # Set the correct counter
        if counter_type == 'back':
            self.__back_counter = counter
            name = 'back'
        elif counter_type == 'neck':
            self.__neck_counter = counter
            name = 'neck'

        # If the counter reaches the specified number of frames, perform the desired action
        if counter == num_frames:
            print('notifying the user')
            # notifying the user
            self.__app.notify_user(alert_type=name)
            # taking a photo of the incorrect posture
            self._photo(self.__frame)
            # incrementing alerts count
            self.__app.total_alerts = 1
            if counter_type == 'back':
                self.__app.incorrect_postures = self.__back_status[-1] 
            elif counter_type == 'neck':
                self.__app.incorrect_postures = self.__neck_status[-1] 

    def _photo(self, frame: np.array) -> None:
        '''stores the last video frame when the user's posture is incorrect for 10 seconds'''

        cv2.imwrite("incorrect_postures/incorrect_posture_{}.jpg".format(self.__photos_counter), frame)
        self.__photos_counter += 1

    @staticmethod
    def angle_calculator(p1: np.array, p2: np.array, p3: np.array) -> float:
        '''
        computes angle for three given points and returns the angle in degrees.

        :param p1: first point
        :param p2: second point (target)
        :param p3: third point
        '''
        # unpacking arrays to get the coordinates
        x1, y1 = p1
        x2, y2 = p2 
        x3, y3 = p3

        # calculating angle
        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))

        # converting negative angles to positive
        if angle < 0:
            return angle + 360
        return angle

    @staticmethod
    def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
        '''
        computes distance between 2 cartesian points.

        :param x1: x coordinate for first point
        :param y1: y coordinate for first point
        :param x2: x coordinate for second point
        :param y2: y coordinate for second point
        '''
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
