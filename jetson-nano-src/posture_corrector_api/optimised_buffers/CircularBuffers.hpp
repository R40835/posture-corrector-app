#pragma once
#include <iostream>
#include <cstring>

class CircularBuffer {
protected:
    size_t size; 
    char* buffer;
    int head = 0;
    int tail = 0;
    bool is_full = false;
    char incorrect_posture = '\0'; // null

public:
    // Constructor to initialize size and buffer
    CircularBuffer(size_t s) : size(s), buffer(new char[s]) {
        std::memset(buffer, '\0', s);
    }
    ~CircularBuffer() { 
        delete[] buffer; 
    }


    virtual void addPosture(char posture) = 0;
    virtual void reinitialiseBuffer() = 0;
    virtual bool isEmpty() = 0;
    virtual bool isIncorrect() = 0;
    virtual bool isMoving() = 0;
    virtual bool maxIncorrectReached() = 0;
};

class BackCircularBuffer : protected CircularBuffer {
public:
    // Constructor to pass the size parameter to the base class constructor
    BackCircularBuffer(size_t s) : CircularBuffer(s) {}
    ~BackCircularBuffer() {}


    char* getBuffer() { return buffer; }
    char getIncorrectPosture() { return incorrect_posture; }
    void addPosture(char posture) override;
    void reinitialiseBuffer() override;
    bool isEmpty() override;
    bool isIncorrect() override;
    bool isMoving() override;
    bool maxIncorrectReached() override;
};

class NeckCircularBuffer : public BackCircularBuffer {
public:
    // Constructor to pass the size parameter to the base class constructor
    NeckCircularBuffer(size_t s) : BackCircularBuffer(s) {}
    ~NeckCircularBuffer() {}


    bool isIncorrect() override;
    bool isMoving() override; 
};
	