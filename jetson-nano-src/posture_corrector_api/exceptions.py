class CameraException(Exception):
    def __init__(self, message: str="No camera module detected on your device. Please make sure your camera is connected."):
        self.message = message 
        super().__init__(self.message)

    def __str__(self) -> str: return self.message


class PhotosUploadException(Exception):
    def __init__(self, message: str="The incorrect posture photos captured during the video weren't sent to the app."):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str: return self.message 


class FolderCleaningException(Exception):
    def __init__(self, message: str="Either you don't have an empty folder named incorrect_postures under the root directory, or the photos weren't deleted."):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str: return self.message 


class DatabaseUpdateException(Exception):
    def __init__(self, message: str="The data collected to assess your posture during the video weren't sent to the app."):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str: return self.message 