from test_imports import cpp_functions, Buffers 
import numpy as np
import time 


class GenericCorrector:

    _euclidian_distance = staticmethod(cpp_functions.euclidean_distance)
    _angle_calculator = staticmethod(cpp_functions.angle_calculator)

    def __init__(self, camera_position: int=1, fps: int=30, duration: int=10):
        self.__forward = b'f'[0] # 102
        self.__upright = b'u'[0] # 117
        self.__reclined = b'r'[0] # 114
        self.__duration = duration
        self.__num_frames = int(self.__duration * fps/ 2)
        self.__CAMERA_POSITION = camera_position
        self.__neck_buffer = Buffers.PyNeckCircularBuffer(self.__num_frames)
        self.__back_buffer = Buffers.PyBackCircularBuffer(self.__num_frames)

    @property
    def neck_posture(self) -> str:
        buffer = self.__neck_buffer.getBuffer()
        if len(buffer) > 0 and buffer[0] == 102: return "forward-leaning neck"
        if len(buffer) > 0 and buffer[0] == 117: return "upright neck"
           
    @property
    def back_posture(self) -> str:
        buffer = self.__back_buffer.getBuffer()
        if len(buffer) > 0 and buffer[0] == 102: return "forward-leaning back"
        if len(buffer) > 0 and buffer[0] == 117: return "upright back"
        if len(buffer) > 0 and buffer[0] == 114: return "reclined back"

    def monitor_posture(self, parts_coordinates: dict) -> None:
        '''
        monitors posture of the subject depending on the camera position selected
        the surveillance is performed in segments of 10 seconds. if the subject
        happens to be in an improper posture during the whole time he/she will 
        be notified.
        '''
        # lateral right or left posture correction
        if (self.__CAMERA_POSITION == 1) | (self.__CAMERA_POSITION == 3):
            # reinitialise buffer here and work out the logic for the timer here as well
            self._lateral_neck_corrector(parts_coordinates)
            self._lateral_back_corrector(parts_coordinates)
            if self.__back_buffer.maxIncorrectReached():
                print("notify user here and now!")
                print(self.__back_buffer.getIncorrectPosture())
                print('back-alert')
                time.sleep(5)
            if self.__neck_buffer.maxIncorrectReached():
                print("notify user here and now!")
                print(self.__neck_buffer.getIncorrectPosture())
                print('neck-alert')
                time.sleep(5)

        elif self.__CAMERA_POSITION == 2 : 
            
            self._frontal_neck_corrector(parts_coordinates)
            self._frontal_back_corrector(parts_coordinates)
            # checking if 10 seconds were spent in a poor posture
            if self.__back_buffer.maxIncorrectReached():
                print("notify user here and now!")
                print(self.__back_buffer.getIncorrectPosture)
                time.sleep(5)
            if self.__neck_buffer.maxIncorrectReached():
                print("notify user here and now!")
                print(self.__neck_buffer.getIncorrectPosture())
                time.sleep(5)
            
    def _frontal_neck_corrector(self, parts_coordinates: dict) -> None:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        n = parts_coordinates['nose']
        ls = parts_coordinates['left_shoulder']
        rs = parts_coordinates['right_shoulder']

        right_shoulder_angle = self._angle_calculator(p1=n, p2=rs, p3=ls)
        left_shoulder_angle = self._angle_calculator(p1=n, p2=ls, p3=rs)

        # 325 is the same angle threshold as 35 it is just inverted
        if (35 < right_shoulder_angle) & (left_shoulder_angle < 325):
            self.__neck_buffer.addPosture(self.__upright)
        else:
            self.__neck_buffer.addPosture(self.__forward)

    def _lateral_neck_corrector(self, parts_coordinates: dict) -> None:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        nose_y = parts_coordinates['nose'][1]
        left_shoulder_y = parts_coordinates['left_shoulder'][1]
        right_shoulder_y = parts_coordinates['right_shoulder'][1]

        # Compare the y-coordinates to determine if the subject is sat upright
        # We'll use a range of 10 pixels to allow for some variability in how people sit on chairs
        if (abs(nose_y - left_shoulder_y) < .08) & (abs(nose_y - right_shoulder_y) < .08):
            self.__neck_buffer.addPosture(self.__forward)
        else:
            # storing neck posture result
            self.__neck_buffer.addPosture(self.__upright) 
    
    def _frontal_back_corrector(self, parts_coordinates: dict) -> None:
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
            self.__back_buffer.addPosture(self.__forward)
        elif nose_hip_dist > shoulder_hip_dist:
            self.__back_buffer.addPosture(self.__upright) 
            
    def _lateral_back_corrector(self, parts_coordinates: dict) -> None:
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
                self.__back_buffer.addPosture(self.__upright)
            elif right_hip_angle < 90: 
                self.__back_buffer.addPosture(self.__forward)
            elif right_hip_angle > 115: 
                self.__back_buffer.addPosture(self.__reclined)
            
        # lateral left
        elif self.__CAMERA_POSITION == 3:
            # left hip angle same angles are used as thresholds there just inverted
            left_hip_angle = self._angle_calculator(p1=ls, p2=lh, p3=lk)

            if 245 < left_hip_angle < 270: 
                self.__back_buffer.addPosture(self.__upright)
            elif left_hip_angle < 245: 
                self.__back_buffer.addPosture(self.__reclined)
            elif left_hip_angle > 270: 
                self.__back_buffer.addPosture(self.__forward)