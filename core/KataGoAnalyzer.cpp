// KataGoAnalyzer.cpp
#include <windows.h>
#include "KataGoAnalyzer.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <regex>
#include <random>
#include <chrono>
#include <filesystem>

namespace fs = std::filesystem;

// Статические члены класса
std::string KataGoAnalyzer::s_defaultKatagoPath = "..\\bot\\KataGo-1.16.4-OpenCL\\katago.exe";
std::string KataGoAnalyzer::s_defaultModelPath = "..\\bot\\KataGo-1.16.4-OpenCL\\models\\kata1-zhizi-b28c512nbt-muonfd2.bin.gz";
std::string KataGoAnalyzer::s_defaultConfigPath = "";
bool KataGoAnalyzer::s_pathsSet = false;

// Структура реализации (Pimpl идиома)
struct KataGoAnalyzer::Impl {
    KataGoConfig config;
    
    HANDLE hStdinWrite = INVALID_HANDLE_VALUE;
    HANDLE hStdoutRead = INVALID_HANDLE_VALUE;
    HANDLE hProcess = INVALID_HANDLE_VALUE;
    DWORD processId = 0;
    
    bool isRunning = false;
    std::mt19937 rng;
    
    Impl() : rng(static_cast<unsigned>(std::chrono::steady_clock::now().time_since_epoch().count())) {}
    
    ~Impl() {
        if (isRunning) {
            shutdown();
        }
    }
    
    // Конвертация UTF-8 в UTF-16 для Windows API
    std::wstring utf8ToWide(const std::string& str) {
        if (str.empty()) return std::wstring();
        int size_needed = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), static_cast<int>(str.size()), NULL, 0);
        std::wstring wstr(size_needed, 0);
        MultiByteToWideChar(CP_UTF8, 0, str.c_str(), static_cast<int>(str.size()), &wstr[0], size_needed);
        return wstr;
    }
    
    // Создание безопасного временного файла
    std::string createTempFile(const std::string& content, const std::string& prefix = "katago_") {
        wchar_t tempPath[MAX_PATH];
        GetTempPathW(MAX_PATH, tempPath);
        
        std::wstring tempDir(tempPath);
        
        for (int attempt = 0; attempt < 10; ++attempt) {
            std::wstring filename = utf8ToWide(prefix + std::to_string(rng()) + ".sgf");
            fs::path tempPath = fs::path(tempDir) / filename;
            
            try {
                if (!fs::exists(tempPath)) {
                    std::ofstream file(tempPath, std::ios::out | std::ios::binary);
                    if (file.is_open()) {
                        file.write(content.c_str(), content.size());
                        file.close();
                        return fs::path(tempPath).string();
                    }
                }
            } catch (const fs::filesystem_error&) {
                continue;
            }
        }
        
        throw std::runtime_error("Failed to create temp file");
    }
    
    bool startProcess() {
        SECURITY_ATTRIBUTES sa = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};
        HANDLE hStdinRead, hStdoutWrite;
        
        // Создаем pipes
        if (!CreatePipe(&hStdinRead, &hStdinWrite, &sa, 0)) {
            return false;
        }
        
        if (!CreatePipe(&hStdoutRead, &hStdoutWrite, &sa, 0)) {
            CloseHandle(hStdinRead);
            CloseHandle(hStdinWrite);
            return false;
        }
        
        // Настройка процесса
        STARTUPINFOW si = {0};
        PROCESS_INFORMATION pi = {0};
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = hStdinRead;
        si.hStdOutput = hStdoutWrite;
        si.hStdError = hStdoutWrite;
        
        // ВАЖНО: используем gtp режим
        std::string cmdLine = "\"" + config.katagoPath + "\" gtp -model \"" + config.modelPath + "\"";
        if (!config.configPath.empty()) {
            cmdLine += " -config \"" + config.configPath + "\"";
        }
        
        std::wstring wCmdLine = utf8ToWide(cmdLine);
        
        if (!CreateProcessW(NULL, (LPWSTR)wCmdLine.c_str(), NULL, NULL, TRUE,
                            CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
            CloseHandle(hStdinRead);
            CloseHandle(hStdinWrite);
            CloseHandle(hStdoutRead);
            CloseHandle(hStdoutWrite);
            return false;
        }
        
        hProcess = pi.hProcess;
        processId = pi.dwProcessId;
        
        CloseHandle(pi.hThread);
        CloseHandle(hStdinRead);
        CloseHandle(hStdoutWrite);
        
        isRunning = true;
        
        // Ждём инициализацию процесса
        Sleep(500);
        
        // Отправляем инициализационные команды без ожидания ответа
        DWORD written;
        std::string cmd;
        
        cmd = "boardsize " + std::to_string(config.boardSize) + "\n";
        WriteFile(hStdinWrite, cmd.c_str(), static_cast<DWORD>(cmd.size()), &written, NULL);
        
        cmd = "komi " + std::to_string(config.komi) + "\n";
        WriteFile(hStdinWrite, cmd.c_str(), static_cast<DWORD>(cmd.size()), &written, NULL);
        
        cmd = "clear_board\n";
        WriteFile(hStdinWrite, cmd.c_str(), static_cast<DWORD>(cmd.size()), &written, NULL);
        
        Sleep(200);
        
        return true;
    }
    
    std::string sendGTPCommand(const std::string& cmd) {
        if (!isRunning) return "";
        
        DWORD written;
        std::string cmdWithNewline = cmd + "\n";
        
        if (!WriteFile(hStdinWrite, cmdWithNewline.c_str(), 
                       static_cast<DWORD>(cmdWithNewline.size()), &written, NULL)) {
            return "";
        }
        
        // Читаем ответ с таймаутом
        char buffer[65536];
        DWORD read;
        std::string response;
        
        // DWORD startTime = GetTickCount();
        // const DWORD TIMEOUT_MS = 10000; // 10 секунд
        
        while (true) {
            // if (GetTickCount() - startTime > TIMEOUT_MS) {
            //     break;
            // }
            
            DWORD bytesAvailable = 0;
            if (!PeekNamedPipe(hStdoutRead, NULL, 0, NULL, &bytesAvailable, NULL)) {
                break;
            }
            
            if (bytesAvailable == 0) {
                Sleep(50);
                continue;
            }
            
            if (!ReadFile(hStdoutRead, buffer, sizeof(buffer) - 1, &read, NULL) || read == 0) {
                break;
            }
            
            buffer[read] = '\0';
            response += buffer;
            
            // GTP ответы заканчиваются пустой строкой
            if (response.find("\n\n") != std::string::npos) {
                break;
            }
        }
        
        return response;
    }
    
    KataGoResult parseFinalScoreResponse(const std::string& response) {
    KataGoResult result;
    
    // Если KataGo вернул ошибку GTP (? ...)
    if (response.find('?') != std::string::npos) {
        result.errorMessage = "KataGo GTP error: " + response;
        return result;
    }
    
    std::regex scoreRegex(R"(=\s*([BW])\+(\d+\.?\d*))");
    std::regex drawRegex(R"(=\s*0)");
    std::smatch match;
    
    if (std::regex_search(response, match, scoreRegex)) {
        std::string winner = match[1].str();
        result.winner = (winner == "B") ? "Black" : "White";
        result.scoreLead = std::stod(match[2].str());
        
        double komi = config.komi;
        if (result.winner == "Black") {
            result.blackScore = komi + result.scoreLead;
            result.whiteScore = komi;
        } else {
            result.whiteScore = komi + result.scoreLead;
            result.blackScore = komi;
        }
        result.success = true;
    } 
    else if (std::regex_search(response, match, drawRegex)) {
        result.winner = "Draw";
        result.scoreLead = 0;
        result.blackScore = config.komi;
        result.whiteScore = config.komi;
        result.success = true;
    } 
    else {
        // Теперь видно, что именно пришло — проще отлаживать
        result.errorMessage = "Failed to parse final_score. Raw response:\n" + response;
    }
    
    return result;
}
    
    void shutdown() {
        if (isRunning) {
            sendGTPCommand("quit");
            
            if (hProcess != INVALID_HANDLE_VALUE) {
                WaitForSingleObject(hProcess, 5000);
                TerminateProcess(hProcess, 0);
                CloseHandle(hProcess);
                hProcess = INVALID_HANDLE_VALUE;
            }
            
            if (hStdinWrite != INVALID_HANDLE_VALUE) {
                CloseHandle(hStdinWrite);
                hStdinWrite = INVALID_HANDLE_VALUE;
            }
            
            if (hStdoutRead != INVALID_HANDLE_VALUE) {
                CloseHandle(hStdoutRead);
                hStdoutRead = INVALID_HANDLE_VALUE;
            }
            
            isRunning = false;
        }
    }
};

// ============================================================================
// Реализация публичных методов KataGoAnalyzer
// ============================================================================

KataGoAnalyzer::KataGoAnalyzer() : pImpl(std::make_unique<Impl>()) {}

KataGoAnalyzer::~KataGoAnalyzer() {
    shutdown();
}

void KataGoAnalyzer::setDefaultPaths(const std::string& katagoPath, 
                                      const std::string& modelPath, 
                                      const std::string& configPath) {
    s_defaultKatagoPath = katagoPath;
    s_defaultModelPath = modelPath;
    s_defaultConfigPath = configPath;
    s_pathsSet = true;
}

bool KataGoAnalyzer::autoDetectPaths() {
    std::vector<std::string> possiblePaths = {
        "bot\\KataGo-1.16.4-OpenCL\\katago.exe",
        "bot\\katago\\katago.exe",
        "..\\bot\\KataGo-1.16.4-OpenCL\\katago.exe",
        "..\\bot\\katago\\katago.exe",
        "C:\\OS_GO\\bot\\KataGo-1.16.4-OpenCL\\katago.exe",
        "C:\\OS_GO\\bot\\katago\\katago.exe",
        ".\\katago.exe"
    };
    
    std::vector<std::string> possibleModels = {
        "bot\\KataGo-1.16.4-OpenCL\\models\\kata1-zhizi-b28c512nbt-muonfd2.bin.gz",
        "bot\\katago\\models\\kata1.bin.gz",
        "..\\bot\\KataGo-1.16.4-OpenCL\\models\\kata1-zhizi-b28c512nbt-muonfd2.bin.gz",
        "..\\bot\\katago\\models\\kata1.bin.gz",
        "C:\\OS_GO\\bot\\KataGo-1.16.4-OpenCL\\models\\kata1-zhizi-b28c512nbt-muonfd2.bin.gz",
        "C:\\OS_GO\\bot\\katago\\models\\kata1.bin.gz",
        ".\\kata1.bin.gz"
    };
    
    bool foundExe = false;
    bool foundModel = false;
    
    for (const auto& path : possiblePaths) {
        if (fs::exists(path)) {
            s_defaultKatagoPath = fs::absolute(path).string();
            foundExe = true;
            break;
        }
    }
    
    for (const auto& path : possibleModels) {
        if (fs::exists(path)) {
            s_defaultModelPath = fs::absolute(path).string();
            foundModel = true;
            break;
        }
    }
    
    if (foundExe && foundModel) {
        s_pathsSet = true;
        return true;
    }
    
    return false;
}

bool KataGoAnalyzer::isAvailable() {
    // Если пути не установлены - пробуем найти
    if (!s_pathsSet) {
        autoDetectPaths();  // ← ВАЖНО: сохраняет пути в статические переменные!
    }
    
    if (s_pathsSet && !s_defaultKatagoPath.empty()) {
        return fs::exists(s_defaultKatagoPath);
    }
    
    return false;
}


bool KataGoAnalyzer::isAvailable(const std::string& katagoPath) {
    if (katagoPath.empty()) {
        return isAvailable();
    }
    return fs::exists(katagoPath);
}

bool KataGoAnalyzer::initialize(const KataGoConfig& config) {
    pImpl->config = config;
    
    if (!fs::exists(config.katagoPath)) {
        return false;
    }
    
    if (!fs::exists(config.modelPath)) {
        return false;
    }
    
    return pImpl->startProcess();
}

bool KataGoAnalyzer::initialize(const std::string& katagoPath,
                                const std::string& modelPath,
                                const std::string& configPath) {
    KataGoConfig config;
    config.katagoPath = katagoPath;
    config.modelPath = modelPath;
    config.configPath = configPath;
    config.maxVisits = 500;
    config.boardSize = 19;
    config.komi = 6.5;
    return initialize(config);
}

bool KataGoAnalyzer::initialize() {
    if (!s_pathsSet) {
        if (!autoDetectPaths()) {
            return false;
        }
    }
    
    KataGoConfig config;
    config.katagoPath = s_defaultKatagoPath;
    config.modelPath = s_defaultModelPath;
    config.configPath = s_defaultConfigPath;
    config.maxVisits = 500;
    config.boardSize = 19;
    config.komi = 6.5;
    
    return initialize(config);
}

KataGoResult KataGoAnalyzer::analyzeSGF(const std::string& sgfContent,
                                         int boardSize,
                                         double komi) {
    KataGoResult result;
    
    if (!pImpl->isRunning) {
        result.errorMessage = "KataGo not initialized";
        return result;
    }
    
    std::string tempFile = getLoadedSGFPath() + "\\_temp_analyze.sgf";
    
    try {
        std::ofstream file(tempFile, std::ios::out | std::ios::binary);
        if (!file.is_open()) {
            result.errorMessage = "Failed to create temp file: " + tempFile;
            return result;
        }
        file.write(sgfContent.c_str(), sgfContent.size());
        file.close();
    } catch (const std::exception& e) {
        result.errorMessage = std::string("File write error: ") + e.what();
        return result;
    }
    
    pImpl->sendGTPCommand("boardsize " + std::to_string(boardSize));
    pImpl->sendGTPCommand("clear_board");
    pImpl->sendGTPCommand("komi " + std::to_string(komi));
    
    std::string loadResponse = pImpl->sendGTPCommand("loadsgf " + tempFile);
    
    if (loadResponse.empty() || loadResponse[0] == '?' || loadResponse.find('=') == std::string::npos) {
        result.errorMessage = "loadsgf failed. Raw response: " + loadResponse;
        try { fs::remove(tempFile); } catch (...) {}
        return result;
    }
    
    std::string response = pImpl->sendGTPCommand("final_score");
    result = pImpl->parseFinalScoreResponse(response);
    
    try { fs::remove(tempFile); } catch (...) {}
    
    return result;
}

std::string KataGoAnalyzer::getLoadedSGFPath() {
    fs::path currentPath = fs::current_path();
    
    fs::path projectRoot = currentPath;
    while (projectRoot.has_parent_path()) {
        if (fs::exists(projectRoot / "games")) {
            break;
        }
        projectRoot = projectRoot.parent_path();
    }
    
    fs::path loadedPath = projectRoot / "games" / "loaded";
    
    if (!fs::exists(loadedPath)) {
        fs::create_directories(loadedPath);
    }
    
    return loadedPath.string();
}

SGFInfo KataGoAnalyzer::parseSGFInfo(const std::string& filepath) {
    SGFInfo info;
    info.fullPath = filepath;
    info.filename = fs::path(filepath).filename().string();
    info.valid = false;
    
    try {
        if (!fs::exists(filepath)) {
            return info;
        }
        
        info.fileSize = fs::file_size(filepath);
        
        std::ifstream file(filepath);
        if (!file.is_open()) {
            return info;
        }
        
        std::string content((std::istreambuf_iterator<char>(file)),
                             std::istreambuf_iterator<char>());
        file.close();
        
        std::regex szRegex(R"(SZ\[(\d+)\])");
        std::regex pbRegex(R"(PB\[([^\]]*)\])");
        std::regex pwRegex(R"(PW\[([^\]]*)\])");
        std::regex kmRegex(R"(KM\[([^\]]*)\])");
        std::regex reRegex(R"(RE\[([^\]]*)\])");
        std::regex dtRegex(R"(DT\[([^\]]*)\])");
        std::regex moveRegex(R"(;([BW])\[)");
        
        std::smatch match;
        
        // Размер доски
        if (std::regex_search(content, match, szRegex)) {
            info.boardSize = std::stoi(match[1].str());
        }
        
        // Имена игроков
        if (std::regex_search(content, match, pbRegex)) {
            info.playerBlack = match[1].str();
        }
        if (std::regex_search(content, match, pwRegex)) {
            info.playerWhite = match[1].str();
        }
        
        // Коми
        if (std::regex_search(content, match, kmRegex)) {
            info.komi = std::stod(match[1].str());
        }
        
        // Результат
        if (std::regex_search(content, match, reRegex)) {
            info.result = match[1].str();
        }
        
        // Дата
        if (std::regex_search(content, match, dtRegex)) {
            info.date = match[1].str();
        }
        
        // Количество ходов
        auto movesBegin = std::sregex_iterator(content.begin(), content.end(), moveRegex);
        auto movesEnd = std::sregex_iterator();
        info.moveCount = std::distance(movesBegin, movesEnd);
        
        info.valid = true;
        
    } catch (const std::exception& e) {
        info.valid = false;
    }
    
    return info;
}

std::vector<SGFInfo> KataGoAnalyzer::listSGFFiles(const std::string& directory) {
    std::vector<SGFInfo> files;
    
    std::string dirPath = directory.empty() ? getLoadedSGFPath() : directory;
    
    if (!fs::exists(dirPath)) {
        return files;
    }
    
    try {
        for (const auto& entry : fs::directory_iterator(dirPath)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
                
                if (ext == ".sgf") {
                    SGFInfo info = parseSGFInfo(entry.path().string());
                    if (info.valid) {
                        files.push_back(info);
                    } else {
                        info.fullPath = entry.path().string();
                        info.filename = entry.path().filename().string();
                        info.fileSize = entry.file_size();
                        files.push_back(info);
                    }
                }
            }
        }
    } catch (const fs::filesystem_error& e) {
        std::cerr << "Error reading directory: " << e.what() << std::endl;
    }
    
    // Сортируем по имени файла
    std::sort(files.begin(), files.end(), [](const SGFInfo& a, const SGFInfo& b) {
        return a.filename < b.filename;
    });
    
    return files;
}

 std::string KataGoAnalyzer::readSGFFile(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        return "";
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

KataGoResult KataGoAnalyzer::analyzeSGFFile(const std::string& filepath,
                                              int boardSize,
                                              double komi) {
    KataGoResult result;
    
    std::string content = readSGFFile(filepath);
    if (content.empty()) {
        result.errorMessage = "Cannot read file: " + filepath;
        return result;
    }
    
    // Если параметры не заданы, извлекаем из SGF
    if (boardSize <= 0 || komi < 0) {
        SGFInfo info = parseSGFInfo(filepath);
        if (boardSize <= 0) {
            boardSize = info.boardSize > 0 ? info.boardSize : 19;
        }
        if (komi < 0) {
            komi = info.komi;
        }
    }
    
    return analyzeSGF(content, boardSize, komi);
}
void KataGoAnalyzer::shutdown() {
    pImpl->shutdown();
}