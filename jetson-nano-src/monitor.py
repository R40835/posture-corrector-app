from posture_corrector_api import (
    PostureCorrectorTrt, 
    draw_connections, 
    draw_keypoints, 
    authenticate_user,
    CameraException, 
    PhotosUploadException, 
    FolderCleaningException, 
    DatabaseUpdateException
)
import numpy as np
import getpass
import time
import cv2
import os


def main():

    options = 'Please choose a camera position to be monitored from. Your options are as follows:\n\n \
                1 ---> [lateral right]\n \
                2 ---> [frontal]\n \
                3 ---> [lateral left]\n \
                \n'
    # pass in the url the ip address used to host the django app 
    # (before running this script run the django app server; assign the port on which the server is listening)
    url = ''
    # assign port
    port = ''
    email = ''
    password = ''
    camera_position = 0
    print('Please enter your account email and password to be authenticated.' +'\n')
    while 1:
        email = str(input('Enter your email: '))
        password = getpass.getpass(prompt='Enter your password: ')
        if authenticate_user(url, port, email, password) == 'user identified':
            print('\n' + 'Authentication successful' + '\n')
            print(options)
            while 1:
                try:
                    camera_position = int(input('Enter your camera position choice: '))
                    if (camera_position == 1) | (camera_position == 2) | (camera_position == 3):
                        if camera_position == 1:
                            print('\n' + 'Camera configured to [lateral right]' + '\n')
                        elif camera_position == 2:
                            print('\n' + 'Camera configured to [frontal]' + '\n')
                        elif camera_position == 3:
                            print('\n' + 'Camera configured to [lateral left]' + '\n')
                        print('Launching Program...' + '\n')
                        break
                    else:
                        print('\nError: Incorrect option.\n\n' + options)
                except:
                    print('\nError: Incorrect option.\n\n' + options)
            break
        else:
            print('\n' + 'Authentication Error: Incorrect email or password, please try again.' + '\n')

    # creating an instance of the class defined in corrector.py
    user = PostureCorrectorTrt(
        url=url, 
        port=port,
        email=email, 
        password=password,
        camera_position=camera_position, 
        fps=30, 
        duration=10
    )
    try: 
        # Open the CS2 camera and start capturing frames
        cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM),width=3280,height=2464,format=NV12,framerate=21/1 \
                                ! nvvidconv flip-method=2 ! video/x-raw, width=(int)640, height=(int)480, format=(string)BGRx \
                            ! videoconvert ! video/x-raw, format=(string)BGR ! appsink")
    except:
        raise CameraException("No camera module detected on your device. Please make sure your camera is connected.")
        
    while cap.isOpened():
        ret, frame = cap.read()

        # Preprocess the input image
        img = cv2.resize(frame, (256, 256))
        img = img.astype(np.float32)
        img = np.expand_dims(img, axis=0)

        # detect body key joint
        user.detect(img)
        keypoints_with_scores = user.keypoints_with_scores
        # Render the output keypoints and drawing connections
        draw_connections(frame, keypoints_with_scores, 0.4)
        draw_keypoints(frame, keypoints_with_scores, 0.4)
        # detection of the current posture
        user.monitor_posture()
        # update frames for photos if incorrect postures last 10 seconds
        user.frame = frame 
        # render neck and back postures on frames
        if len(user.back_status) > 1:
            text = f"back posture: {user.back_status[-1]}"
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        if len(user.neck_status) > 1:
            text2 = f"neck posture: {user.neck_status[-1]}"
            cv2.putText(frame, text2, (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2) 

        # pop up monitoring screen
        cv2.imshow('trt', frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    end_time = int(time.time())

    # exceptions handling
    try:
        upload_photos = user.app.upload_photos() 
        if upload_photos != "Files uploaded successfully." and upload_photos != "No incorrect postures":
            raise PhotosUploadException("The incorrect posture photos captured during the video weren't sent to the app.")
        
    except PhotosUploadException as e:
        print(f"Error uploading photos: {e}")
    except Exception as e:
        print(f"Unexpected error while uploading photos: {e}")
    else:
        try:
            user.app.clean_folder()
            folder_path = 'incorrect_postures/'
            empty_folder = True if len(os.listdir(folder_path)) == 0 else False 
            if not empty_folder:
                raise FolderCleaningException("Either you don't have an empty folder named incorrect_postures under the root directory, or the photos weren't deleted.")
            
        except FolderCleaningException as e:
            print(f"Error cleaning folder: {e}")
        except Exception as e:
            print(f"Unexpected error while cleaning folder: {e}")
        else:
            try:
                update_database = user.app.update_database(end_time)
                if update_database != "success":
                    raise DatabaseUpdateException("The data collected to assess your posture during the video weren't sent to the app.")
                
            except DatabaseUpdateException as e:
                print(f"Error updating database: {e}")
            except Exception as e:
                print(f"Unexpected error while updating database: {e}")

if __name__ == '__main__':
    main()
