from test_imports import(
    ModelPerformance,
    CameraException,
    draw_connections, 
    draw_keypoints
)
from test_correctors import (
    TestCorrectorTrt,
    TestCorrectorOnnx, 
    TestCorrectorTflite,
)
import tensorflow as tf
import numpy as np
import cv2


def processing_tflite(frame: np.ndarray) -> np.ndarray: 
    # Reshape image
    img = frame.copy()
    img = tf.image.resize_with_pad(np.expand_dims(img, axis=0), 256,256)
    input_image = tf.cast(img, dtype=tf.float32)
    return input_image


def processing_onnx(frame: np.ndarray) -> np.ndarray:
    # Reshape the image
    img = cv2.resize(frame, (256, 256))
    img = img.astype(np.float32)
    # Add batch dimension to input image
    input_image = np.expand_dims(img, axis=0)
    return input_image


def processing_trt(frame: np.ndarray) -> np.ndarray:
    # Preprocess the input image
    img = cv2.resize(frame, (256, 256))
    img = img.astype(np.float32)
    input_image = np.expand_dims(img, axis=0)
    return input_image


option = "Please choose one of the following options:\n\t1 ---> TFLITE\n\t2 ---> ONNX\n\t3 ---> TRT\nYour choice: "
option2 = "\nPlease choose a camera angle:\n\t1 ---> Lateral right\n\t2 ---> Frontal\n\t3 ---> Lateral Left\nYour choice: "

def main():

    version_choice = int(input(option))

    camera_position = int(input(option2))

    if version_choice == 1:
        # Version 1: using the moveNet model in its original form (tflite)
        user =  TestCorrectorTflite(
            camera_position=camera_position,
            fps=30,
            duration=10
        )
        metrics = ModelPerformance(model="TFLITE")

    elif version_choice == 2:
        # Version 2: using the moveNet model optimised to onnx
        user = TestCorrectorOnnx(
            camera_position=camera_position,
            fps=30,
            duration=10
        )
        metrics = ModelPerformance(model="ONNX")

    elif version_choice == 3:
        # Version 3: using the moveNet Model optimised to trt
        user = TestCorrectorTrt(
            camera_position=camera_position, 
            fps=30, 
            duration=10
        )     
        metrics = ModelPerformance(model="TRT")

    metrics.get_memory_info()

    # Open the CS2 camera and start capturing frames
    try:
        cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM),width=3280,height=2464,format=NV12,framerate=21/1 \
                                ! nvvidconv flip-method=2 ! video/x-raw, width=(int)640, height=(int)480, format=(string)BGRx \
                            ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")
    except:
        raise CameraException('No camera module detected in your device. Please Make sure your camera is connected.')
    
    frames_count = 0
    while cap.isOpened():
        ret, frame = cap.read()

        if version_choice == 1:
            input_image = processing_tflite(frame)
        elif version_choice == 2:
            input_image = processing_onnx(frame)
        elif version_choice == 3:
            input_image = processing_trt(frame)

        # detect body key joint
        user.detect(input_image)
        keypoints_with_scores = user.keypoints_with_scores
        # Render the output keypoints and drawing connections
        draw_connections(frame, keypoints_with_scores, 0.4)
        draw_keypoints(frame, keypoints_with_scores, 0.4)
        # detection of the current posture
        user.monitor_posture()

        # render neck and back postures on frames
        if len(user.back_status) > 1:
            text = f"back posture: {user.back_status[-1]}"
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        if len(user.neck_status) > 1:
            text2 = f"neck posture: {user.neck_status[-1]}"
            cv2.putText(frame, text2, (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2) 

        frames_count += 1
        # pop up monitoring screen
        cv2.imshow('trt', frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
