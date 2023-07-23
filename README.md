# Posture-Corrector-App
Jetson Nano-based app using computer vision and a CNN model to analyse sitting posture. Alerts sent for poor posture, with real-time monitoring and user feedback. Optimised for Jetson Nano, with data storage and user statistics. Promotes better spinal health and posture habits.
The Posture Corrector App is a computer vision-based application developed using the Jetson Nano platform. It utilises a CNN model, specifically the "Single Pose MoveNet" model from TensorFlow, optimised to ONNX then TensorRT to analyse the user's sitting posture in real-time. By calculating hip and neck angles and other distances between key body joints detected by the model, the app determines whether the user is sitting upright, forward, or reclined.

# Features
- Real-time posture analysis using the Jetson Nano's integrated camera (Raspberry Pi Camera Module 2).
- Real-time alerts sent to the Django web app for poor posture detection.
- User-friendly web interface for monitoring and feedback.
- Data storage in a PostgreSQL database for historical analysis.
- Authentication system for user profiles and personalised statistics.
- Spinal health promotion through posture correction.
- Photos of incorrect postures sustained throughout the monitoring video.

<div style="display: flex; justify-content: center;">
  <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/welcome.PNG?raw=true" style="width: 32%;">
  <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/home.PNG?raw=true" style="width: 32%;">
  <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/monitoralert.PNG?raw=true" style="width: 32%;">

</div>
<div style="display: flex; justify-content: center;">
  <img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/dashboard.png?raw=true" style="width: 32%;">
  <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/detections.PNG?raw=true" style="width: 32%;">
  <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/history.PNG?raw=true" style="width: 32%;">

</div>
<div style="display: flex; justify-content: center;">
</div>

# Django App Setup
1. Install the necessary dependencies and libraries listed in the requirements.txt file using the following command:
```
pip install -r requirements.txt
```
2. Create a postgres database and link it to the app in settings.py.
3. Pass your IP address to the allowed_hosts in settings.py.
4. Make migrations using the following command: 
```
python manage.py makemigrations
```
5. Migrate using the following command: 
```
python manage.py migrate
```
6. Run the server using the following command: 
```
python manage.py runserver <host-address>:<port>
```
7. Access the web app through a browser to monitor posture, view statistics, and provide feedback.
  
# Jetson Nano Setup
1. Write the image into a SDcard following the instruction from nvidia website https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#setup.
2. Connect the Jetson Nano to the camera module and ensure it is properly configured.
3. Install TensorRT, numpy, pycuda, and the latest version of OpenCV on the Jetson Nano.
4. In monitor.py set the url to the address where your hosting your Django app, and the port to the port where the app is listening.
5. Open a terminal and type in the following command:
```
LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
```
6. Run the monitor.py script and authenticate to your account created on the Django app.

<div style="display: flex; justify-content: center;"> 
    <img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/hardware.jpg?raw=true" style="width: 17%;" />
    <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/startingprogram.jpg?raw=true" style="width: 30%;" />
    <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/programatrun.jpg?raw=true" style="width: 30%;" />

</div>

# Monitoring Perspectives
Once the monitoring script is running, and the authentication is complete on the jetson nano side, the user is prompt to choose an angle to be monitored from, there are 3 options:
1. Lateral Right
2. Frontal
3. Lateral Left

Some of the body key joints detected by the moveNet model are used in order to determine the user posture as shown below:
<div style="display: flex; justify-content: center;"> 
    <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/perspectives2.PNG?raw=true" style="width: 30%;" />
    <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/moveNet.PNG?raw=true" style="width: 15%;" />
    <img src="https://github.com/R40835/posture-corrector-app/blob/main/assets/perspectives.PNG?raw=true" style="width: 30%;" />

</div>

# Performance Optimisation
The original model was in the form of a Tensorflow-lite file, that was optimised to an ONNX file, and then to a Tensort engine in order to speed up the inference. The following table shows the performance of each model on the jetson nano:
| Model Format | Memory Usage (megabytes) | Video Latency (seconds) | Inference Time per Frame (seconds) |
| ------------ | ------------------------ | ----------------------- | ---------------------------------- |
| .TFLITE      | 328.11 MB                | 8.00 s                  | 0.45 s                             |
| .onnx        | 98.06 MB                 | 6.00 s                  | 0.36 s                             |
| .trt         | 156.86 MB                | 0.5 s                   | 0.043 s                            |

# Contributing
Contributions to the Posture Corrector App are welcome! If you have any ideas, bug fixes, or improvements, please submit a pull request. Make sure to follow the established coding style and guidelines.

# License
This project is licensed under the MIT License. See the LICENSE file for more information.

# Contact
For any questions or inquiries, please reach out to meraghnir93@gmail.com

