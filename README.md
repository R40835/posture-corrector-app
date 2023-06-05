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
  <img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/dashboard.png?raw=true" style="width: 40%;">
  <img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/history.png?raw=true" style="width: 40%;">
</div>
<div style="display: flex; justify-content: center;">
  <img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/detection1.png?raw=true" style="width: 40%;">
  <img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/detection2.png?raw=true" style="width: 40%;">
</div>

# Django App Setup Instructions
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
python manage.py runserver <host-address>:5000
```
7. Access the web app through a browser to monitor posture, view statistics, and provide feedback.
  
# Jetson Nano setup
1. Write the image into a SDcard following the instruction from nvidia website https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#setup.
2. Connect the Jetson Nano to the camera module and ensure it is properly configured.
3. Install TensorRT, numpy, pycuda, and the latest version of OpenCV on the Jetson Nano.
4. In monitor.py set the url to the IP address where your hosting your Django app.
5. Run the monitor.py script and authenticate to your account created on the Django app.
<img src="https://github.com/R40835/Posture-Corrector-App/blob/main/assets/hardware.jpg?raw=true" width="400" height="400" />

# Contributing
Contributions to the Posture Corrector App are welcome! If you have any ideas, bug fixes, or improvements, please submit a pull request. Make sure to follow the established coding style and guidelines.

# License
This project is licensed under the MIT License. See the LICENSE file for more information.

# Contact
For any questions or inquiries, please reach out to meraghnir93@gmail.com

