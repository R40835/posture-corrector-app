# distutils: language = c++
# distutils: sources=CircularBuffers.cpp
# distutils: language_level=3


cdef extern from "CircularBuffers.hpp":
    cdef cppclass CircularBuffer:
        CircularBuffer(size_t s) except +
        void addPosture(char posture)
        void reinitialiseBuffer()
        bint isEmpty()
        bint isIncorrect()
        bint isMoving()
        bint maxIncorrectReached()


    cdef cppclass BackCircularBuffer:
        BackCircularBuffer(size_t s) except +
        char* getBuffer()
        char getIncorrectPosture()
        void addPosture(char posture)
        void reinitialiseBuffer()
        bint isEmpty()
        bint isIncorrect()
        bint isMoving()
        bint maxIncorrectReached()


    cdef cppclass NeckCircularBuffer:
        NeckCircularBuffer(size_t s) except +
        bint isIncorrect()
        bint isMoving()


cdef class PyBackCircularBuffer:
    cdef BackCircularBuffer* cpp_back_buffer

    def __cinit__(self, size_t s):
        self.cpp_back_buffer = new BackCircularBuffer(s)

    def __dealloc__(self):
        del self.cpp_back_buffer

    # Define methods that wrap the C++ methods
    def getIncorrectPosture(self):
        return self.cpp_back_buffer.getIncorrectPosture()

    def getBuffer(self):
        return self.cpp_back_buffer.getBuffer()

    def addPosture(self, char posture): 
        self.cpp_back_buffer.addPosture(posture)

    def reinitialiseBuffer(self):
        self.cpp_back_buffer.reinitialiseBuffer()

    def isEmpty(self):
        return self.cpp_back_buffer.isEmpty()

    def isIncorrect(self):
        return self.cpp_back_buffer.isIncorrect()

    def isMoving(self):
        return self.cpp_back_buffer.isMoving()

    def maxIncorrectReached(self):
        return self.cpp_back_buffer.maxIncorrectReached()


cdef class PyNeckCircularBuffer(PyBackCircularBuffer):
    cdef NeckCircularBuffer* cpp_neck_buffer

    def __cinit__(self, size_t s):
        self.cpp_neck_buffer = new NeckCircularBuffer(s)

    # Override methods if needed
    def isIncorrect(self):
        return self.cpp_neck_buffer.isIncorrect()

    def isMoving(self):
        return self.cpp_neck_buffer.isMoving()