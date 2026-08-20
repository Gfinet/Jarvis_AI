// jarvis_ai/stt/stt.cpp
#include <iostream>
#include <cstdlib>
#include <memory>
#include <array>
#include "../include/jarvis.hpp"

std::string listen_and_transcribe() {
    std::cout << "[STT] → Activation du micro..." << std::endl;

    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen("./venv/bin/python3 -u stt/voice_input.py", "r"), pclose);

    if (!pipe) {
        std::cerr << "Erreur : impossible de démarrer le micro." << std::endl;
        return "";
    }
	
	std::cout << "Micro on" << std::endl;
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    std::cout << "stt End" << std::endl;
    return result;
}
