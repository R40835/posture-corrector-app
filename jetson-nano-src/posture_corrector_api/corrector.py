from .movenet_models import ModelTrt
from .post_requests import DjangoAppSession
from .optimised_computations import cpp_functions
from .optimised_buffers import Buffers 
import numpy as np
import math
import cv2


class PostureCorrectorTrt(ModelTrt):
    '''
    * This Class works by loading the moveNet model from Tensorflow and detects 17 body key joints.
    * The body key joints are used to calculate angles and distances used as thresholds to estimate incorrect postures.
    * The model has been optimised to run on the Jetson Nano by converting it to ONNX then to a TensorRT engine to run inference.
    * This only runs on Jetson Nanos as the optimised model file (movenet_v3.trt) is tailored to the device's GPU architecture.
    * Postures are stored in c++ circular buffers, if they're full of an incorrect posture, an alert will be sent to the app along with other data.
    * Buffers are reinisialised if another type of posture is stored as the user is most likely moving.
    * Buffers take one argument, size. It is the number of frames generated throughout the period of time required to send alerts.
    '''
    _euclidian_distance = staticmethod(cpp_functions.euclidean_distance)
    _angle_calculator = staticmethod(cpp_functions.angle_calculator)

    def __init__(self, url: str, port:str, email: str, password: str, camera_position: int=1, fps: int=30, duration: int=10):
        super(PostureCorrectorTrt, self).__init__()
        self.__frame = None
        self.__photos_counter = 0
        self.__forward = b'f'[0] # 102
        self.__upright = b'u'[0] # 117
        self.__reclined = b'r'[0] # 114
        self.__duration = duration 
        self.__CAMERA_POSITION = camera_position
        self.__num_frames = int(self.__duration * fps / 2) 
        self.__neck_buffer = Buffers.PyNeckCircularBuffer(self.__num_frames)
        self.__back_buffer = Buffers.PyBackCircularBuffer(self.__num_frames)
        self.__app = DjangoAppSession(
            url=url,
            port=port,
            email=email,
            password=password 
        )
    
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
    
    @property
    def app(self) -> DjangoAppSession:
        return self.__app 
    
    @property
    def frame(self) -> np.ndarray:
        return self.__frame 
    
    @frame.setter
    def frame(self, frame: np.ndarray) -> None:
        self.__frame = frame 

    def monitor_posture(self) -> None:
        '''
        monitors posture of the subject depending on the camera position selected,
        the surveillance is performed in segments of 10 seconds. if the subject
        happens to be in an improper posture during the whole time he/she will 
        be notified.
        '''
        # lateral right or left posture correction
        if (self.__CAMERA_POSITION == 1) | (self.__CAMERA_POSITION == 3):
            self._lateral_neck_corrector()
            self._lateral_back_corrector()

            if self.__back_buffer.maxIncorrectReached():
                self._send_alert("back")
            if self.__neck_buffer.maxIncorrectReached():
                self._send_alert("neck")

        # frontal posture correction
        elif self.__CAMERA_POSITION == 2 : 
            self._frontal_neck_corrector()
            self._frontal_back_corrector()
                
            # checking if buffers are full of incorrect postures and notifying user if they are
            if self.__back_buffer.maxIncorrectReached():
                self._send_alert("back")
            if self.__neck_buffer.maxIncorrectReached():
                self._send_alert("neck")

    def _frontal_neck_corrector(self) -> None:
        '''computes the neck frontal posture and store it in the neck buffer'''

        # retrieving the coordinates arrays needed
        n = self.parts_coordinates['nose']
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']

        right_shoulder_angle = self._angle_calculator(p1=n, p2=rs, p3=ls)
        left_shoulder_angle = self._angle_calculator(p1=n, p2=ls, p3=rs)

        # 325 is the angle threshold 35 flipped
        if (35 < right_shoulder_angle) & (left_shoulder_angle < 325):
            self.__neck_buffer.addPosture(self.__upright)
        else: 
            self.__neck_buffer.addPosture(self.__forward)        

    def _lateral_neck_corrector(self) -> None:
        '''computes the neck lateral posture and store it in the neck buffer'''

        # retrieving the coordinates arrays needed
        nose_y = self.parts_coordinates['nose'][1]
        left_shoulder_y = self.parts_coordinates['left_shoulder'][1]
        right_shoulder_y = self.parts_coordinates['right_shoulder'][1]

        # Compare the y-coordinates to determine if the subject is sat upright
        # We'll use a range of 10 pixels to allow for some variability in how people sit on chairs
        if (abs(nose_y - left_shoulder_y) < .08) & (abs(nose_y - right_shoulder_y) < .08):
            self.__neck_buffer.addPosture(self.__forward)        
        else:
            self.__neck_buffer.addPosture(self.__upright) 
    
    def _frontal_back_corrector(self) -> None:
        '''computes the back frontal posture and store it in the back buffer'''
        
        # retrieving the coordinates arrays needed
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']
        lh = self.parts_coordinates['left_hip']
        rh = self.parts_coordinates['right_hip']
        nose = self.parts_coordinates['nose']

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
            
    def _lateral_back_corrector(self) -> None:
        '''computes the back lateral posture and store it in the back buffer'''

        # retrieving the coordinates arrays needed
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']
        lh = self.parts_coordinates['left_hip']
        rh = self.parts_coordinates['right_hip']
        lk = self.parts_coordinates['left_knee']
        rk = self.parts_coordinates['right_knee']

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
            # using reflex angles as the camera is on the opposite side
            left_hip_angle = self._angle_calculator(p1=ls, p2=lh, p3=lk)

            if 245 < left_hip_angle < 270: 
                self.__back_buffer.addPosture(self.__upright)
            elif left_hip_angle < 245: 
                self.__back_buffer.addPosture(self.__reclined)
            elif left_hip_angle > 270: 
                self.__back_buffer.addPosture(self.__forward)

    def _send_alert(self, alert_type) -> None:
        '''
        triggers the alert on the user interface, and store the incorrect posture
        sustained by the user during the 10 seconds of time.

        :param alert_type: back or neck
        '''
        print('notifying the user...')
        # notifying the user
        self.__app.notify_user(alert_type=alert_type)
        # incrementing alerts count
        self.__app.total_alerts = 1
        # taking a photo of the incorrect posture
        self._photo(self.__frame)

        # selecting the right buffer
        if alert_type == "back":
            captured_incorrect_posture = self.__back_buffer.getIncorrectPosture()
        elif alert_type == "neck":
            captured_incorrect_posture = self.__neck_buffer.getIncorrectPosture()

        # storing incorrect posture to send it to the app through a post requset
        if alert_type == "back" and captured_incorrect_posture == self.__reclined:
            self.__app.incorrect_postures =  "reclined back"
        elif alert_type == "back" and captured_incorrect_posture == self.__forward:
            self.__app.incorrect_postures = "forward-leaning back"
        elif alert_type == "neck" and captured_incorrect_posture == self.__forward:
            self.__app.incorrect_postures =  "forward-leaning neck"

    def _photo(self, frame: np.ndarray) -> None:
        '''stores the last video frame when the user's posture is incorrect for 10 seconds'''

        # TODO: get photo time and store it along with the incorrect posture TODO
        cv2.imwrite("incorrect_postures/incorrect_posture_{}.jpg".format(self.__photos_counter), frame)
        self.__photos_counter += 1