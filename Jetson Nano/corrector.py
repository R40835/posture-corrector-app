import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np
import math
import time
import requests
import json
import cv2
import os


class PostureCorrector:
    '''
    * This Class works by loading the moveNet model from Tensorflow and detects 17 body key joints.
    * The body key joints are used to calculate angles and distances used as thresholds to estimate incorrect postures.
    * The model has been optimised to run on the jetson nano by converting it to ONNX and then to a TensorRT engine 
    used to run inference.
    * This runs only on the Jetson Nanos as the optimisation model file (engine.trt) is tailored to the Jetson Nano's 
    GPU architecture.
    '''

    def __init__(self, url: str, email: str, password: str, camera_position: int=1, fps: int=None, duration: int=10):
        '''
        Constructor
        
        :param url: ip address on which the django app is hosted
        :param email: user email to authenticate on the django app
        :param password: user password to authenticate on the django app
        :param camera_position: camera position could be one of the following options:
                1 -> lateral right 
                2 -> frontal 
                3 -> lateral left
        :param fps: frames per second
        :param duration: duration of the incorrect posture to trigger the alert in seconds
        '''
        # user
        self.email = email
        self.password = password
        # Django App Server:
        self.url = url 
        self.port = '5000'
        # Defining the number of frames generated in 10 seconds: 
        # this is to trigger the alarm on the user interface if the incorrect predictions 
        # in a row for each frame equals the number of frames in 10 seconds
        self.duration = duration 
        self.num_frames = int(self.duration * fps)

        # other attributes
        self.CAMERA_POSITION = camera_position
        self.start_time = int(time.time())

        # Load the TensorRT model engine
        # Load the serialized engine from file
        with open('engine.trt', 'rb') as f:
            engine_data = f.read()
        self.runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
        self.engine = self.runtime.deserialize_cuda_engine(engine_data)

        # Create a context for inference
        self.context = self.engine.create_execution_context()

        # Allocate device memory for input and output buffers
        self.input_shape = (1, 256, 256, 3)
        self.output_shape = (1, 17, 3)
        self.input_buf = cuda.mem_alloc(int(np.prod(self.input_shape) * np.dtype(np.float32).itemsize))
        self.output_buf = cuda.mem_alloc(int(np.prod(self.output_shape) * np.dtype(np.float32).itemsize))

        # Create a CUDA stream to run inference asynchronously
        self.stream = cuda.Stream()
        
        # initialising attributes and different data structure to store relevant info
        self.frame = None
        self.keypoints_with_scores = None
        self.incorrect_postures = []
        self.neck_status = np.array([])
        self.back_status = np.array([])
        self.total_alerts = 0
        self.photos_counter = 0
        self.back_counter = 0
        self.neck_counter = 0
        self.poor_posture_time = 0
        self.parts_coordinates = {
            'nose': None,
            'left_eye': None,
            'right_eye': None,
            'left_ear': None,
            'right_ear': None,
            'left_shoulder': None,
            'right_shoulder': None,
            'left_elbow': None,
            'right_elbow': None,
            'left_wrist': None,
            'right_wrist': None,
            'left_hip': None,
            'right_hip': None,
            'left_knee': None,
            'right_knee': None,
            'left_ankle': None,
            'right_ankle': None
        }

    def detect(self, input_image) -> None:
        '''
        making predictions on the 17 body key points and updating coordinates
        
        :param input_image: image converted array
        '''

        # Copy the input data to the device
        cuda.memcpy_htod_async(self.input_buf, input_image, self.stream)

        # Run inference
        self.context.execute_async_v2(bindings=[int(self.input_buf), int(self.output_buf)], stream_handle=self.stream.handle)

        # Copy the output data back to the host
        self.keypoints_with_scores = np.empty(self.output_shape, dtype=np.float32)
        cuda.memcpy_dtoh_async(self.keypoints_with_scores, self.output_buf, self.stream)

        # Wait for the CUDA stream to finish
        self.stream.synchronize()

        # updating coordinates
        # getting key points position after each prediction
        kpts_x = self.keypoints_with_scores[0, :, 1]
        kpts_y = self.keypoints_with_scores[0, :, 0]

        # zipping x and y coordinates
        coordinates = list(zip(kpts_x, kpts_y))

        # updatting dictionary coordinates
        for idx, part in enumerate(self.parts_coordinates):
            self.parts_coordinates[part] = coordinates[idx]

    def posture_corrector(self) -> None:
        '''
        monitors posture of the subject depending on the camera position selected
        the surveillance is performed in segments of 10 seconds. if the subject
        happens to be in an improper posture during the whole time he/she will 
        be notified.
        '''
        # lateral right or left posture correction
        if (self.CAMERA_POSITION == 1) | (self.CAMERA_POSITION == 3):
            neck_state = self._lateral_neck_corrector()
            back_state = self._lateral_back_corrector()
                
            # checking if 10 seconds were spent in a poor posture:
            # the timer method takes results of the predictions (1 or 0) 
            # and triggers the alarm by sending a post request 
            # to the django app if the incorrect posture was predicted 
            # for all the frames generated in 10 seconds 
            self._timer(back_state, self.num_frames, 'back')
            self._timer(neck_state, self.num_frames, 'neck')
        elif self.CAMERA_POSITION == 2 : 
            neck_state = self._frontal_neck_corrector()
            back_state = self._frontal_back_corrector()
                
            # checking if 10 seconds were spent in a poor posture
            self._timer(back_state, self.num_frames, 'back')
            self._timer(neck_state, self.num_frames, 'neck')

    def _frontal_neck_corrector(self) -> int:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        n = self.parts_coordinates['nose']
        ls = self.parts_coordinates['left_shoulder']
        rs = self.parts_coordinates['right_shoulder']

        right_shoulder_angle = self._angle_calculator(p1=n, p2=rs, p3=ls)
        left_shoulder_angle = self._angle_calculator(p1=n, p2=ls, p3=rs)

        # 325 is the same angle threshold as 35 it is just inverted
        if (35 < right_shoulder_angle) & (left_shoulder_angle < 325):
            self.neck_status = np.append(self.neck_status, 'upright neck')
            return 1
        self.neck_status = np.append(self.neck_status, 'forward-leaning neck')
        return 0

    def _lateral_neck_corrector(self) -> int:
        '''checks correct neck posture returns 0 for incorrect and 1 for correct posture'''

        nose_y = self.parts_coordinates['nose'][1]
        left_shoulder_y = self.parts_coordinates['left_shoulder'][1]
        right_shoulder_y = self.parts_coordinates['right_shoulder'][1]

        # Compare the y-coordinates to determine if the subject is sat upright
        # We'll use a range of 10 pixels to allow for some variability in how people sit on chairs
        if (abs(nose_y - left_shoulder_y) < .08) & (abs(nose_y - right_shoulder_y) < .08):
            self.neck_status = np.append(self.neck_status, 'forward-leaning neck') 
            return 0
        
        # storing neck posture result
        self.neck_status = np.append(self.neck_status, 'upright neck') 
        return 1
    
    def _frontal_back_corrector(self):
        '''checks correct back posture returns 0 for incorrect and 1 for correct posture'''
        
        # coordinates of left and right shoulders, left and right hips, and nose
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
            self.back_status = np.append(self.back_status, 'froward-leaning back') 
            return 0
        elif nose_hip_dist > shoulder_hip_dist:
            self.back_status = np.append(self.back_status, 'upright back') 
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
        if self.CAMERA_POSITION == 1:
            # right hip angle
            right_hip_angle = self._angle_calculator(p1=rs, p2=rh, p3=rk)

            if 90 < right_hip_angle < 115: 
                self.back_status = np.append(self.back_status, 'upright back') 
                return 1
            elif right_hip_angle < 90: 
                self.back_status = np.append(self.back_status, 'froward-leaning back') 
                return 0
            elif right_hip_angle > 115: 
                self.back_status = np.append(self.back_status, 'reclined back') 
                return 0
            
        # lateral left
        elif self.CAMERA_POSITION == 3:
            # left hip angle same angles are used as thresholds there just inverted
            left_hip_angle = self._angle_calculator(p1=ls, p2=lh, p3=lk)

            if 245 < left_hip_angle < 270: 
                self.back_status = np.append(self.back_status, 'upright back') 
                return 1
            elif left_hip_angle < 245: 
                self.back_status = np.append(self.back_status, 'reclined back') 
                return 0
            elif left_hip_angle > 270: 
                self.back_status = np.append(self.back_status, 'forward-leaning back') 
                return 0

    def _angle_calculator(self, p1: np.array, p2: np.array, p3: np.array) -> float:
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

    def _euclidian_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        '''
        computes distance between 2 cartesian points.

        :param x1: x coordinate for first point
        :param y1: y coordinate for first point
        :param x2: x coordinate for second point
        :param y2: y coordinate for second point
        '''
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

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
            counter = self.back_counter
        elif counter_type == 'neck':
            counter = self.neck_counter

        if current_status == 0:
            counter += 1
        else:
            # If the current status is different from the previous status, reset the counter
            counter = 0

        # Set the correct counter
        if counter_type == 'back':
            self.back_counter = counter
            name = 'back'
        elif counter_type == 'neck':
            self.neck_counter = counter
            name = 'neck'

        # If the counter reaches the specified number of frames, perform the desired action
        if counter == num_frames:
            print('notifying the user')
            # notifying the user
            self._notify_user(alert_type=name)
            # taking a photo of the incorrect posture
            self._photo(self.frame)
            # count of alerts
            self.total_alerts += 1
            if counter == 'back':
                self.incorrect_postures.append(self.back_status[len(self.back_status) - 1])
            elif counter == 'neck':
                self.incorrect_postures.append(self.neck_status[len(self.neck_status) -1])
            
    def _notify_user(self, alert_type: str) -> None:
        '''sending a notification to the user to straighten up through a post request'''

        # django app url
        url = 'http://' + self.url + ':'+ self.port + '/main/my-endpoint/'
        data = {
            'email':self.email,
            'password':self.password,
            'alert':alert_type, 
            'back_postures' : 'reclined'
            }
        response = requests.post(url, data=data)
        print(response.json()['status'])

    def _photo(self, frame):
        '''stores the last video frame when the user's posture is incorrect for 10 seconds'''

        cv2.imwrite("incorrect_postures/incorrect_posture_{}.jpg".format(self.photos_counter), frame)
        self.photos_counter += 1

    def _upload_photos(self):
        '''uploads photos of incorrect postures detected during the monitoring video'''

        url = 'http://' + self.url + ':'+ self.port + '/main/user-incorrect-postures/'
        data = {
            'email': self.email,
            'password': self.password
        }
        folder_path = 'incorrect_postures/'
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    files = {'image': f}
                    response = requests.post(url, data=data, files=files)
                    print(response.text)

    def _clean_folder(self):
        '''deletes all images captured and sent as they are stored in the app's db'''

        folder_path = 'incorrect_postures/'
        # get all image files names in folder
        files = os.listdir(folder_path)

        for file in files:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)

    def _update_database(self, end_time):
        '''sends a user's posture data to the django app so that it could be stored in the database'''

        url = 'http://' + self.url + ':'+ self.port + '/main/video-data/'
        if len(self.incorrect_postures) == 0:
            self.incorrect_postures.append('No Incorrect Postures')
        data = {
            'email': self.email,
            'password': self.password,
            'start_time': self.start_time,
            'end_time': end_time, 
            'total_alerts': self.total_alerts,
            'incorrect_postures':json.dumps(self.incorrect_postures),
            }
        response = requests.post(url, data=data)
        print(response.json()['status'])
