import numpy as np 
import requests 
import json
import time
import os 


class DjangoAppSession:
    def __init__(self, host: str, port: str, email: str, password: str):
        self.__port = port
        self.__host = host 
        self.__email = email
        self.__password = password
        self.__incorrect_postures = []
        self.__start_time = int(time.time())
        self.__total_alerts = 0

    # Getters
    @property
    def incorrect_postures(self) -> list:
        return self.__incorrect_postures
    
    @property
    def total_alerts(self) -> int:
        return self.__total_alerts
    
    # Setters
    @incorrect_postures.setter
    def incorrect_postures(self, item: str) -> None:
        self.__incorrect_postures.append(item)

    @total_alerts.setter
    def total_alerts(self, value: int) -> None:
        self.__total_alerts += value
 
    def notify_user(self, alert_type: str) -> None:
        '''sending a notification to the user to straighten up through a post request'''

        # django app url
        url = 'http://' + self.__host + ':'+ self.__port + '/main/my-endpoint/'
        data = {
            'email':self.__email,
            'password':self.__password,
            'alert':alert_type, 
            }
        response = requests.post(url, data=data)
        print(response.json()['status'])

    def upload_photos(self) -> str:
        '''uploads photos of incorrect postures detected during the monitoring video'''
        
        folder_path = 'incorrect_postures/'
        if len(os.listdir(folder_path)) == 0: return "No incorrect postures"

        responses = []
        url = 'http://' + self.__host + ':'+ self.__port + '/main/user-incorrect-postures/'
        data = {
            'email': self.__email,
            'password': self.__password
        } 

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    files = {'image': f}
                    response = requests.post(url, data=data, files=files)
                    responses.append(response.text)
        responses = np.unique(np.array(responses))

        if len(responses) == 1: return responses[0]            

    def update_database(self, end_time: int) -> str:
        '''sends a user's posture data to the django app so that it could be stored in the database'''

        url = 'http://' + self.__host + ':'+ self.__port + '/main/video-data/'
        if len(self.__incorrect_postures) == 0:
            self.__incorrect_postures.append('No Incorrect Postures')
        data = {
            'email': self.__email,
            'password': self.__password,
            'start_time': self.__start_time,
            'end_time': end_time, 
            'total_alerts': self.__total_alerts,
            'incorrect_postures':json.dumps(self.__incorrect_postures),
            }
        response = requests.post(url, data=data)
        return response.json()['status']

    @staticmethod
    def clean_folder() -> None:
        '''deletes all images captured and sent as they are stored in the app's db'''

        folder_path = 'incorrect_postures/'
        # get all image files names in folder
        files = os.listdir(folder_path)

        for file in files:
            file_path = os.path.join(folder_path, file)
            os.remove(file_path)