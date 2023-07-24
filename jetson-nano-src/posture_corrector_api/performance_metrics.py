from abc import ABC, abstractmethod
import numpy as np
import psutil
import os
import time


class PerfomanceMetrics(ABC):
    @abstractmethod
    def get_fps(self, total_frames: int) -> str:
        pass 

    @abstractmethod
    def get_video_latency(self) -> str:
        pass 

    @abstractmethod
    def get_memory_usage(self) -> str:
        pass 

    @abstractmethod
    def get_inference_time_per_frame(self) -> str:
        pass 

    @abstractmethod
    def get_average_inference_time(self) -> str:        pass 

    @abstractmethod
    def get_model_loading_time(self) -> str:
        pass

    @abstractmethod
    def get_model_size(self) -> str:
        pass 


class ModelPerformance(PerfomanceMetrics):
    def __init__(self, model: str):
        ''':param model: TRT | ONNX | TFLITE'''
        self.__model = model
        self.__start_video_time = None
        self.__end_video_time = None
        self.__total_frames = None
        self.__fps = None
        self.__memory_info = None
        self.__inference_start_time = None
        self.__inference_end_time = None 
        self.__model_loading_start = None 
        self.__model_loading_end = None
        self.__cumulative_latency = 0
        self.__inference_times = np.array([])


    def start_video(self) -> None:
        self.__start_video_time = time.time()

    def end_video(self) -> None:
        self.__end_video_time = time.time()
        
    def start_inference(self) -> None:
        self.__inference_start_time = time.time()

    def end_inference(self) -> None:
        self.__inference_end_time = time.time()

    def track_latency(self) -> None:
        self.__cumulative_latency += self.__inference_end_time - self.__inference_start_time

    def total_frames(self, value) -> None:
        self.__total_frames = value

    def get_memory_info(self) -> None:
        # Get the current process ID
        pid = os.getpid()
        # Get the process object for the current process
        process = psutil.Process(pid)
        # Get the memory usage information for the current process
        self.__memory_info = process.memory_info()

    def get_fps(self) -> str:
        elapsed_time = self.__end_video_time - self.__start_video_time
        # Calculate FPS
        self.__fps = self.__total_frames / elapsed_time
        return f"FPS: {self.__fps:.2f}"
    
    def get_video_latency(self) -> str:
        average_latency = self.__cumulative_latency / self.__total_frames
        return f"Video Latency: {average_latency:.6f} seconds"

    def get_memory_usage(self) -> str:
        return f"Memory usage: {self.__memory_info.rss / 1024 / 1024:.2f} MB."

    def get_inference_time_per_frame(self) -> str:
        inference_time = self.__inference_start_time - self.__inference_end_time
        self.__inference_times = np.append(self.__inference_times, inference_time)
        return f"Inference time per frame: {inference_time} seconds."
    
    def get_average_inference_time(self) -> str:
        return np.sum(self.__inference_times) / len(self.__inference_times)
    
    def get_model_loading_time(self) -> str:
        return f"Model loading time: {self.__model_loading_start - self.__model_loading_end} seconds."
    
    def get_model_size(self, MB: bool=True, GB: bool=None) -> str:
        # Get the size of the model file in bytes
        if self.__model == "TRT":
            model_file_path = "posture_corrector_api/models/movenet_v3.trt"
        elif self.__model == "ONNX":
            model_file_path = "posture_corrector_api/models/movenet_v2.onnx"
        elif self.__model == "TFLITE":
            model_file_path = "posture_corrector_api/models/movenet_v1.tflite"

        model_size_bytes = os.path.getsize(model_file_path)

        # Convert model size to MB or GB for readability
        if MB:
            return f"Model size: {model_size_bytes / (1024 * 1024)} MB."
        elif GB:
            return f"Model size: {model_size_bytes / (1024 * 1024 * 1024)} GB."