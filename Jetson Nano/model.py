import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np


class MoveNetModel:
    def __init__(self):
        # Load the TensorRT model engine
        # Load the serialized engine from file
        with open('engine.trt', 'rb') as f:
            engine_data = f.read()
        self._runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
        self._engine = self._runtime.deserialize_cuda_engine(engine_data)
        # Create a context for inference
        self._context = self._engine.create_execution_context()
        # Allocate device memory for input and output buffers
        self._input_shape = (1, 256, 256, 3)
        self._output_shape = (1, 17, 3)
        self._input_buf = cuda.mem_alloc(int(np.prod(self._input_shape) * np.dtype(np.float32).itemsize))
        self._output_buf = cuda.mem_alloc(int(np.prod(self._output_shape) * np.dtype(np.float32).itemsize))
        # Create a CUDA stream to run inference asynchronously
        self._stream = cuda.Stream()
        # initialising attributes and different data structure to store relevant info
        self.keypoints_with_scores = None
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

    def detect(self, input_image: np.array) -> None:
        '''
        making predictions on the 17 body key points and updating coordinates
        
        :param input_image: image converted array
        '''

        # Copy the input data to the device
        cuda.memcpy_htod_async(self._input_buf, input_image, self._stream)
        # Run inference
        self._context.execute_async_v2(bindings=[int(self._input_buf), int(self._output_buf)], stream_handle=self._stream.handle)
        # Copy the output data back to the host
        self.keypoints_with_scores = np.empty(self._output_shape, dtype=np.float32)
        cuda.memcpy_dtoh_async(self.keypoints_with_scores, self._output_buf, self._stream)
        # Wait for the CUDA stream to finish
        self._stream.synchronize()
        # updating coordinates
        # getting key points position after each prediction
        kpts_x = self.keypoints_with_scores[0, :, 1]
        kpts_y = self.keypoints_with_scores[0, :, 0]
        # zipping x and y coordinates
        coordinates = list(zip(kpts_x, kpts_y))
        # updatting dictionary coordinates
        for idx, part in enumerate(self.parts_coordinates):
            self.parts_coordinates[part] = coordinates[idx]
