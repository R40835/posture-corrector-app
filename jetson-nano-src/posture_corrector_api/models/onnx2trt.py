import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np 

onnx_path = 'movenet_v2.onnx'

# set up TensorRT
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(TRT_LOGGER)
network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
parser = trt.OnnxParser(network, TRT_LOGGER) 

with open(onnx_path, 'rb') as model:
    parser.parse(model.read())
    # model optimisations
    config = builder.create_builder_config()
    config.set_flag(trt.BuilderFlag.SPARSE_WEIGHTS)
    config.set_flag(trt.BuilderFlag.FP16)
    # enforcing fp16 types
    config.set_flag(trt.BuilderFlag.OBEY_PRECISION_CONSTRAINTS)
    # allocating max memory workspace
    config.max_workspace_size = 1 << 30
    # build and serialize engine
    serialized_engine = builder.build_serialized_network(network, config)

trt_path = 'movenet_v3.trt'

with open(trt_path, 'wb') as f:
    f.write(serialized_engine)
