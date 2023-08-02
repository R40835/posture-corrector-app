from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "Buffers",
        sources=["CppCircularBuffers.pyx", "CircularBuffers.cpp"],
        language="c++",
        # Add any additional libraries or library directories here if needed.
    ),
]

setup(
    ext_modules=cythonize(extensions),
    language_level="3",  # Set the language level to Python 3
)
