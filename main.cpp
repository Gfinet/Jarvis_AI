// jarvis_ai/main.cpp
#include <iostream>
#include <unistd.h>

int main() {
    std::cout << "🧠 Lancement de Jarvis..." << std::endl;
	char* args[] = {
        const_cast<char*>("venv/bin/python3"),
        const_cast<char*>("stt/jarvis_clap.py"),
        nullptr
    };

        std::cout << args[0] << args[1] << std::endl;
        execvp(args[0], args);
        exit(0);

    return 0;
}
