# jarvis_ai/Makefile

CXX = g++
CXXFLAGS = -Wall -Werror -Wextra -Iinclude
SRC = main.cpp 
OBJ = $(SRC:.cpp=.o)
BIN = jarvis_ai

all: $(BIN)

$(BIN): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(BIN)

pythenv:
	source ./venv/bin/activate

launch:
	./venv/bin/python -u stt/voice_input.py
