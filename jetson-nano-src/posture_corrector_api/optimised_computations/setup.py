from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension("cpp_functions", ["cpp_functions.pyx"], language="c++"),
]

setup(
    ext_modules=cythonize(extensions),
)
