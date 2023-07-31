# distutils: language=c++
# distutils: sources=my_functions.cpp
# cython: embedsignature=True

from libc.math cimport atan2, sqrt

cdef float PI = 3.1415926

def angle_calculator(const float[::1] p1, const float[::1] p2, const float[::1] p3):
    cdef float x1, y1, x2, y2, x3, y3
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    x3 = p3[0]
    y3 = p3[1]

    cdef float angle = (atan2(y3 - y2, x3 - x2) - atan2(y1 - y2, x1 - x2)) * 180.0 / PI

    if angle < 0:
        return angle + 360
    return angle

def euclidean_distance(float x1, float y1, float x2, float y2):
    return sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))

