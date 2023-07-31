#include "my_functions.hpp"
#include <cmath>

float PI = 3.1415926;

float angle_calculator(const float p1[2], const float p2[2], const float p3[2]) {
    float x1, y1, x2, y2, x3, y3;
    x1 = p1[0];
    y1 = p1[1];
    x2 = p2[0];
    y2 = p2[1];
    x3 = p3[0];
    y3 = p3[1];

    float angle = (std::atan2(y3 - y2, x3 - x2) - std::atan2(y1 - y2, x1 - x2)) * 180.0 / M_PI;

    if (angle < 0) {
        return angle + 360;
    }
    return angle;
}

float euclidean_distance(float x1, float y1, float x2, float y2) {
    return std::sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));
}
