from test_imports import cpp_functions
import numpy as np
import math
import time 


class GenericCorrector:

    _euclidian_distance = staticmethod(cpp_functions.euclidean_distance)
    _angle_calculator = staticmethod(cpp_functions.angle_calculator)

    def __init__(self, camera_position: int=1, fps: int=30, duration: int=10):

        self.__duration = duration
        self.__num_frames = int(self.__duration * fps) / 2
        self.__CAMERA_POSITION = camera_position
        self.__neck_status = np.array([])
        self.__back_status = np.array([])
        self.__back_counter = 0
        self.__neck_counter = 0

    @property
    def neck_status(self) -> np.ndarray:
        return self.__neck_status
    
    @property
    def back_status(self) -> np.ndarray:
        return self.__back_status

    def monitor_posture(self, parts_coordinates: dict) -> None:
        '''
        monitors posture of the subject depending on the camera position selected
        the surveillance is performed in segments of 10 seconds. if the subject
        happens to be in an improper posture during the whole time he/she will 
        be notified.
        '''
        # lateral right or left posture correction
        if (self.__CAMERA_POSITION == 1) | (self.__CAMERA_POSITION == 3):
            neck_state = self._lateral_neck_corrector(parts_coordinates)
            back_state = self._lateral_back_corrector(parts_coordinates)
        
            self._timer(back_state, self.__num_frames, 'back')
            self._timer(neck_state, self.__num_frames, 'neck')

        elif self.__CAMERA_POSITION == 2 : 
            neck_state = self._frontal_neck_corrector(parts_coordinates)
            back_state = self._frontal_back_corrector(parts_coordinates)
                
            # checking if 10 seconds were spent in a poor posture
            self._timer(back_state, self.__num_frames, 'back')
            self._timer(neck_state, self.__num_frames, 'neck')

    def _frontal_neck_corrector(self, parts_coordinates: dict) -> int:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        n = parts_coordinates['nose']
        ls = parts_coordinates['left_shoulder']
        rs = parts_coordinates['right_shoulder']

        right_shoulder_angle = self._angle_calculator(p1=n, p2=rs, p3=ls)
        left_shoulder_angle = self._angle_calculator(p1=n, p2=ls, p3=rs)

        # 325 is the same angle threshold as 35 it is just inverted
        if (35 < right_shoulder_angle) & (left_shoulder_angle < 325):
            self.__neck_status = np.append(self.__neck_status, 'upright neck')
            return 1
        self.__neck_status = np.append(self.__neck_status, 'forward-leaning neck')
        return 0

    def _lateral_neck_corrector(self, parts_coordinates: dict) -> int:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        nose_y = parts_coordinates['nose'][1]
        left_shoulder_y = parts_coordinates['left_shoulder'][1]
        right_shoulder_y = parts_coordinates['right_shoulder'][1]

        # Compare the y-coordinates to determine if the subject is sat upright
        # We'll use a range of 10 pixels to allow for some variability in how people sit on chairs
        if (abs(nose_y - left_shoulder_y) < .08) & (abs(nose_y - right_shoulder_y) < .08):
            self.__neck_status = np.append(self.__neck_status, 'forward-leaning neck') 
            return 0
        
        # storing neck posture result
        self.__neck_status = np.append(self.__neck_status, 'upright neck') 
        return 1
    
    def _frontal_back_corrector(self, parts_coordinates: dict) -> int:
        '''checks correct back posture returns 0 for incorrect and 1 for correct posture'''
        
        # coordinates of left and right shoulders, left and right hips, and nose
        ls = parts_coordinates['left_shoulder']
        rs = parts_coordinates['right_shoulder']
        lh = parts_coordinates['left_hip']
        rh = parts_coordinates['right_hip']
        nose = parts_coordinates['nose']

        # calculating distances between shoulders and hips
        left_shoulder_hip_dist = self._euclidian_distance(x1=ls[0], x2=lh[0], y1=ls[1], y2=lh[1])
        right_shoulder_hip_dist = self._euclidian_distance(x1=rs[0], x2=rh[0], y1=rs[1], y2=rh[1])
        shoulder_hip_dist = left_shoulder_hip_dist + right_shoulder_hip_dist
        # calculating distances between nose and hips
        left_nose_hip_dist = self._euclidian_distance(x1=nose[0], x2=lh[0], y1=nose[1], y2=lh[1]) 
        right_nose_hip_dist = self._euclidian_distance(x1=nose[0], x2=rh[0], y1=nose[1], y2=rh[1]) 
        nose_hip_dist = left_nose_hip_dist + right_nose_hip_dist

        # compare the distances
        if nose_hip_dist < shoulder_hip_dist:
            self.__back_status = np.append(self.__back_status, 'froward-leaning back') 
            return 0
        elif nose_hip_dist > shoulder_hip_dist:
            self.__back_status = np.append(self.__back_status, 'upright back') 
            return 1
            
    def _lateral_back_corrector(self, parts_coordinates: dict) -> int:
        '''checks correct back posture returns 0 for incorrect and 1 for correct posture'''

        # retrieving coordinates arrays of relevant body parts
        ls = parts_coordinates['left_shoulder']
        rs = parts_coordinates['right_shoulder']
        lh = parts_coordinates['left_hip']
        rh = parts_coordinates['right_hip']
        lk = parts_coordinates['left_knee']
        rk = parts_coordinates['right_knee']

        # lateral right
        if self.__CAMERA_POSITION == 1:
            # right hip angle
            right_hip_angle = self._angle_calculator(p1=rs, p2=rh, p3=rk)

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
            left_hip_angle = self._angle_calculator(p1=ls, p2=lh, p3=lk)

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
        elif counter_type == 'neck':
            self.__neck_counter = counter

        # If the counter reaches the specified number of frames, perform the desired action
        if counter == num_frames:

            if counter_type == 'back':
                print('straighten up your back')
            elif counter_type == 'neck':
                print('straighten up your neck')