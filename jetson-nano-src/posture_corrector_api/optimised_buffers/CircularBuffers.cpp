#include "CircularBuffers.hpp"

bool BackCircularBuffer::isEmpty() { 
	return !is_full && (head == tail); 
}

void BackCircularBuffer::addPosture(char posture) {
	buffer[head] = posture;
	head = (head + 1) % size;
	if (head == tail) {
		is_full = true;
		tail = (tail + 1) % size;
	}
}

void BackCircularBuffer::reinitialiseBuffer() {
	// Reset all elements to null characters
	std::memset(buffer, '\0', size);  
	head = 0; 
	tail = 0; 
	is_full = false; 
}

bool BackCircularBuffer::isIncorrect() {
	// Check if all data in the buffer are 'r' or 'f'
	bool allReclined = true; 
	bool allForwardLeaning = true; 
	
	for (size_t i = 0; i < size; i++) { 
		if (buffer[i] != 'r') { 
			allReclined = false; 
		}

		if (buffer[i] != 'f') { 
			allForwardLeaning = false; 
		}
	}

	return allReclined || allForwardLeaning; 
}

bool BackCircularBuffer::isMoving() {
	bool upright_back_found = false;
	bool reclined_back_found = false;
	bool forward_back_found = false;

	for (size_t i = 0; i < size; ++i) { 
		if (buffer[i] == 'u') {
			upright_back_found = true;
		}
		else if (buffer[i] == 'r') {  
			reclined_back_found = true;
		}
		else if (buffer[i] == 'f') { 
			forward_back_found = true; 
		}
	}

	return (reclined_back_found || forward_back_found) && upright_back_found;

}

bool BackCircularBuffer::maxIncorrectReached() {
	if (isIncorrect()) {  
		std::cout << "User has had incorrect posture for the last 10 seconds." << std::endl;
		std::cout << "Reinitializing the buffer..." << std::endl;
		incorrect_posture = buffer[0];
		reinitialiseBuffer(); 
		return true;
	}
	else if (isMoving()) { 
		std::cout << "User is moving. must keep track of the posture strictly when it is stable." << std::endl;
		std::cout << "Reinitializing the buffer..." << std::endl;
		reinitialiseBuffer(); 
		return false;
	}

	return false;
}

bool NeckCircularBuffer::isIncorrect() {
	// Check if all data in the buffer are 'f'
	bool allForwardLeaning = true;

	for (size_t i = 0; i < size; i++) {

		if (buffer[i] != 'f') {
			allForwardLeaning = false;
		}
	}

	return  allForwardLeaning;
}

bool NeckCircularBuffer::isMoving() {
	bool upright_back_found = false;
	bool forward_back_found = false;

	for (size_t i = 0; i < size; ++i) {
		if (buffer[i] == 'u') {
			upright_back_found = true;
		}
		else if (buffer[i] == 'f') {
			forward_back_found = true;
		}
	}

	return forward_back_found && upright_back_found;  
}
