import os
import sys

# setting up module search path for testing purposes
# Get the path to the directory containing the tests.py script
current_dir = os.path.dirname(os.path.abspath(__file__))
# # Get the path to the parent directory (one level up from current_dir)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

# # Add the parent directory to the module search path
sys.path.append(parent_dir)

# imports
from movenet_models import ModelTrt, ModelOnnx, ModelTflite
from utils import draw_connections, draw_keypoints
from exceptions import CameraException
from optimised_computations import cpp_functions 
from optimised_buffers import Buffers 
