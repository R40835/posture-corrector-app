from test_imports import (
    ModelTrt, 
    ModelOnnx, 
    ModelTflite 
)
from test_generic_corrector import GenericCorrector


class TestCorrectorTflite(ModelTflite, GenericCorrector):
    def __init__(self, camera_position: int=1, fps: int=2, duration: int=10):
        super(TestCorrectorTflite, self).__init__()
        GenericCorrector.__init__(
            self, 
            camera_position, 
            fps, 
            duration
        )
        
    def monitor_posture(self) -> None:
        super(TestCorrectorTflite, self).monitor_posture(
            parts_coordinates=self.parts_coordinates
        )


class TestCorrectorOnnx(ModelOnnx, GenericCorrector):
    def __init__(self, camera_position: int=1, fps: int=3, duration: int=10):
        super(TestCorrectorOnnx, self).__init__()
        GenericCorrector.__init__(
            self, 
            camera_position, 
            fps, 
            duration
        )
    
    def monitor_posture(self) -> None:
        super(TestCorrectorOnnx, self).monitor_posture(
            parts_coordinates=self.parts_coordinates
        )


class TestCorrectorTrt(ModelTrt, GenericCorrector):
    def __init__(self, camera_position: int=1, fps: int=19, duration: int=10):
        super(TestCorrectorTrt, self).__init__()
        GenericCorrector.__init__(
            self, 
            camera_position, 
            fps, 
            duration
        )
        
    def monitor_posture(self) -> None:
        super(TestCorrectorTrt, self).monitor_posture(
            parts_coordinates=self.parts_coordinates
        )
