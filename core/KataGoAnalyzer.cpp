// KataGoAnalyzer.cpp
#include "KataGoAnalyzer.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <regex>
#include <random>
#include <chrono>
#include <filesystem>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
namespace fs = std::filesystem;

struct KataGoAnalyzer::Impl {
    KataGoConfig config;
    
    HANDLE hStdinWrite = INVALID_HANDLE_VALUE;// handle это дескриптор для pipe потом
    HANDLE hStdoutRead = INVALID_HANDLE_VALUE;
    HANDLE hProcess = INVALID_HANDLE_VALUE;// тоже дескриптор но для процесса именно
    DWORD processId = 0;
    
    bool isRunning = false;
    std::mt19937 rng;
    
    Impl() : rng(static_cast<unsigned>(std::chrono::steady_clock::now().time_since_epoch().count())) {}//генерация сида для рандома
    // IMPL - создаватель временных файлов ему нужен рандомайзер для имен
    ~Impl() {
        if (isRunning) {
            shutdown();
        }
    }
    
    // Конвертация UTF-8 в UTF-16 для Windows API
    std::wstring utf8ToWide(const std::string& str) {// сначала узнать размер через опр настройки в функции
        if (str.empty()) return std::wstring();
        int size_needed = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), static_cast<int>(str.size()), NULL, 0);
        std::wstring wstr(size_needed, 0);// буфер - куда закидывать
        MultiByteToWideChar(CP_UTF8, 0, str.c_str(), static_cast<int>(str.size()), &wstr[0], size_needed);
        return wstr;// закидывание ^^
    }
    
    // Конвертация wide string в UTF-8
    std::string wideToUtf8(const std::wstring& wstr) {// наоборот 
        if (wstr.empty()) return std::string();
        int size_needed = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), static_cast<int>(wstr.size()), NULL, 0, NULL, NULL);
        std::string str(size_needed, 0);
        WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), static_cast<int>(wstr.size()), &str[0], size_needed, NULL, NULL);
        return str;
    }
    
    // Создание безопасного временного файла
    std::string createTempFile(const std::string& content, const std::string& prefix = "katago_") {
        wchar_t tempPath[MAX_PATH];
        GetTempPathW(MAX_PATH, tempPath);// путь к папке временных файлов
        
        std::wstring tempDir(tempPath);
        
        for (int attempt = 0; attempt < 10; ++attempt) {
            std::wstring filename = utf8ToWide(prefix + std::to_string(rng()) + L".sgf");
            fs::path tempPath = fs::path(tempDir) / filename;//генерация имени
            
            try {
                if (!fs::exists(tempPath)) {// если такого файла еще нет(не должно быть)
                    std::ofstream file(tempPath, std::ios::out | std::ios::binary);// открыть этот файл в бинарном режиме(sgf формату так удобней )
                    if (file.is_open()) {
                        file.write(content.c_str(), content.size());// закидываем контент в файл
                        file.close();
                        return fs::path(tempPath).string();// вернуть путь к sgf файлу
                    }
                }
            } catch (const fs::filesystem_error&) {// если че то не то, пробуем еще раз
                continue;
            }
        }
        
        throw std::runtime_error("Не удалось создать временный файл");
    }
    
    bool startProcess() {
        SECURITY_ATTRIBUTES sa = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};// структура для определения может ли дочерний процесс брать наши HANDLE
        //                             размер, стандартная безопасность, дочерний наследует HANDLE(это значит возможность связи через pipe)
        HANDLE hStdinRead, hStdoutWrite;// дескрипторы для pipe(для катаго)
        
        // Создаем pipes для stdin(отправка команд катаго)
        if (!CreatePipe(&hStdinRead, &hStdinWrite, &sa, 0)) {// канал(выход,вход,безопасность(наследование),размер буфера(тут юзаем системный))
            return false;
        }
        
        // Создаем pipes для stdout(получение ответов катаго)
        if (!CreatePipe(&hStdoutRead, &hStdoutWrite, &sa, 0)) {
            CloseHandle(hStdinRead);
            CloseHandle(hStdinWrite);
            return false;
        }
        
        // Настройка процесса
        STARTUPINFOW si = {0};// структура для инициализации процесса(лучше обнулить, далле самомму инициализировать)
        PROCESS_INFORMATION pi = {0};// структура получает инфу о созданном процессе
        // PROCESS_INFORMATION - структура, которая получит информацию о созданном процессе
        // pi.hProcess - HANDLE для управления процессом
        // pi.hThread  - HANDLE для управления главным потоком
        // pi.dwProcessId - ID процесса (число)
        // pi.dwThreadId  - ID потока (число)
        si.cb = sizeof(si);// размер
        si.dwFlags = STARTF_USESTDHANDLES;// флаги показывают какие поля юзаем
        si.hStdInput = hStdinRead;// куда катаго будет читать команды пользователя
        si.hStdOutput = hStdoutWrite;// куда катаго будет писать ответы свои
        si.hStdError = hStdoutWrite;// куда писать ошибки(туда же куда и обычный вывод)
        
        std::string cmdLine = "\"" + config.katagoPath + "\" analysis -model \"" + config.modelPath + "\"";
        if (!config.configPath.empty()) {
            cmdLine += " -config \"" + config.configPath + "\"";
        }
        // генерация команды для катаго
        if (config.logToStdout) {
            cmdLine += " -log-to-stderr";// логи отправляем в STDERR(который перенаправлен в pipe)
        }
        
        std::wstring wCmdLine = utf8ToWide(cmdLine);// конвертация из UTF-8 в UTF_16(для API)
        
        // Создаем процесс с скрытым окном
        DWORD creationFlags = CREATE_NO_WINDOW;// флаги создания процесса(не вылезет черное окно пр запуске) // Флаги создания процесса:
    // CREATE_NO_WINDOW (0x08000000) - НЕ ПОКАЗЫВАТЬ ОКНО КОНСОЛИ!
    // Это важно, чтобы не появлялось черное окно при запуске
    
    // Альтернативные флаги:
    // CREATE_NEW_CONSOLE (0x00000010) - показать новое окно консоли
    // DETACHED_PROCESS   (0x00000008) - без консоли (но окно может появиться)
    // NORMAL_PRIORITY_CLASS (0x00000020) - нормальный приоритет

        // запуск процесса
        if (!CreateProcessW(
            NULL,//ipApplicationName указывает пут к exe файлу(если null то имя файла надо указать в начале lpCommandLine )
             wCmdLine.data(),// командная строка(сторка для передачи аргументов командной строки)
              NULL,// безопасность процесса(режим по умолчанию тут)
               NULL,// безопасность потока(так же)
                TRUE,// наследование HANDLE(нужно для правильной работы pipe)
                creationFlags,// флаги создания(тут значение CREATE_NO_WINDOW)
                NULL,//  наследуем переменные среды родителя(по умолчанию)
                 NULL,// наследуем текущую директорию от родительского процесса(тут может быть прямо путь)
                  &si,// наши pipe
                   &pi)) {// HANDLE процесса
            DWORD error = GetLastError();// ошибка
            std::cerr << "Ошибка CreateProcess: " << error << std::endl;
            CloseHandle(hStdinRead);// закрыть все pipe
            CloseHandle(hStdinWrite);
            CloseHandle(hStdoutRead);
            CloseHandle(hStdoutWrite);
            return false;
        }
        
        hProcess = pi.hProcess;
        // Сохраняем HANDLE процесса для управления KataGo
    // С его помощью можно:
    // - ждать завершения процесса (WaitForSingleObject)
    // - проверять, жив ли процесс (WaitForSingleObject с 0 таймаутом)
    // - завершать процесс (TerminateProcess)
        processId = pi.dwProcessId;// Сохраняем ID процесса (для информации, не обязательно)
        
        CloseHandle(pi.hThread);// закрыть ненужные концы pipe
        CloseHandle(hStdinRead);
        CloseHandle(hStdoutWrite);// закрыть HANDLE потока(он не нужен для управления)
        
        isRunning = true;// процесс готов к работе
        
        // Даем процессу время на инициализацию
        Sleep(500);
        
        // Инициализация доски
        sendGTPCommand("boardsize " + std::to_string(config.boardSize));
        sendGTPCommand("komi " + std::to_string(config.komi));
        sendGTPCommand("clear_board");
        
        return true;
    }
    
    std::string sendGTPCommand(const std::string& cmd) {
        if (!isRunning) return "";
        
        DWORD written;
        std::string cmdWithNewline = cmd + "\n";// так надо для gtp протокола
        //      дескриптор pipe для записи  текст сообщения   длина сообщения   что реально записано  параметр асинхронной записи(тут null)
        if (!WriteFile(hStdinWrite, cmdWithNewline.c_str(), 
                       static_cast<DWORD>(cmdWithNewline.size()), &written, NULL)) {//
            return "";
        }
        
        // Читаем ответ
        char buffer[65536];
        DWORD read;
        std::string response;
        
        while (true) { //дескриптор pipe для чтения  буфер(куда читаем) размер(сколько читаем) что реально прочитали синхронный режим
            if (!ReadFile(hStdoutRead, buffer, sizeof(buffer) - 1, &read, NULL) || read == 0) {
                break;
            }
            buffer[read] = '\0';
            response += buffer;// закидываем сообщение из буфера 
            
            // Проверяем завершение ответа (пустая строка после ответа)
            if (response.find("\n\n") != std::string::npos) {
                break;
            }
        }
        
        return response;
    }
    
    KataGoResult parseAnalyzeResponse(const std::string& response) {
        KataGoResult result;
        
        try {
            // Ищем JSON в ответе
            size_t jsonStart = response.find('{');
            if (jsonStart == std::string::npos) {// если не нашлось json
                result.errorMessage = "Не найден JSON в ответе";
                return result;
            }
            
            size_t jsonEnd = response.rfind('}');
            if (jsonEnd == std::string::npos) {
                result.errorMessage = "Не найден конец JSON";
                return result;
            }
            
            std::string jsonStr = response.substr(jsonStart, jsonEnd - jsonStart + 1);// извлекаем json файл
            json data = json::parse(jsonStr);
            
            if (data.contains("winrate")) {// извлечение вероятности победы(от 0 до 1)
                result.winrate = data["winrate"].get<double>();
            }
            
            if (data.contains("scoreLead")) {// извлечение преимущество в очках
                result.scoreLead = data["scoreLead"].get<double>();
            }
            
            if (data.contains("visits")) {// извлекаеи число проанализированных ходов
                result.visits = data["visits"].get<int>();
            }
            
            if (data.contains("ownership")) {// извлекаем карту владения территорий
                result.ownership = data["ownership"].dump();
            }
            
            if (data.contains("rootInfo") && data["rootInfo"].contains("moves")) {// извлекаем топ ходы
                for (const auto& move : data["rootInfo"]["moves"]) {
                    if (move.contains("move")) {
                        std::string moveStr = move["move"].get<std::string>();
                        result.topMoves.push_back(moveStr);
                        if (result.topMoves.size() >= 5) break;// 5 штук
                    }
                }
                if (!result.topMoves.empty()) {
                    result.bestMove = result.topMoves[0];// самый наиахренительнейший ход в партии
                }
            }
            
            // Расчет счета
            double komi = config.komi;
            if (result.scoreLead > 0) {// расчет разницы идет от черных
                result.winner = "Black";
                result.blackScore = komi + result.scoreLead;
                result.whiteScore = komi;
            } else {
                result.winner = "White";
                result.blackScore = komi;
                result.whiteScore = komi - result.scoreLead;
            }
            
            result.success = true;
            
        } catch (const std::exception& e) {
            result.errorMessage = e.what();
        }
        
        return result;
    }
    
    KataGoResult parseFinalScoreResponse(const std::string& response) {
        KataGoResult result;
        
        // Парсим final_score: "= B+12.5" или "= W+3.5" или "= 0"
        std::regex scoreRegex(R"(=\s*([BW])\+(\d+\.?\d*)|=\s*0)");
        std::smatch match;
        
        if (std::regex_search(response, match, scoreRegex)) {
            if (match[1].matched) {
                std::string winner = match[1].str();
                result.winner = (winner == "B") ? "Black" : "White";// парсим победителя и его преимущество в очках
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
            } else {
                // Ничья
                result.winner = "Draw";
                result.scoreLead = 0;
                result.blackScore = config.komi;
                result.whiteScore = config.komi;
                result.success = true;
            }
        } else {
            result.errorMessage = "Не удалось распарсить результат final_score";
        }
        
        return result;
    }
    
    void shutdown() {// как завершить процесс
        if (isRunning) {
            sendGTPCommand("quit");// спокойно просим катаго завершиться
            // если спокойно не получилось будем убивать
            if (hProcess != INVALID_HANDLE_VALUE) {// если десриптор процесса не в значении завершения
                WaitForSingleObject(hProcess, 5000);// даем время 5 секунд
                TerminateProcess(hProcess, 0);// принудительно убиваем
                CloseHandle(hProcess);// закрыть HANDLE процесса
                hProcess = INVALID_HANDLE_VALUE;// обнулить HANDLE
            }
            
            if (hStdinWrite != INVALID_HANDLE_VALUE) {
                CloseHandle(hStdinWrite);// если не закрылся канал записи, закрываем
                hStdinWrite = INVALID_HANDLE_VALUE;// обнулить HANDLE
            }
            
            if (hStdoutRead != INVALID_HANDLE_VALUE) {
                CloseHandle(hStdoutRead);// если не закрылся канал чтения, закрываем
                hStdoutRead = INVALID_HANDLE_VALUE;// обнулить HANDLE
            }
            
            isRunning = false;// маркер завершенности
        }
    }
};

// Реализация публичных методов
KataGoAnalyzer::KataGoAnalyzer() : pImpl(std::make_unique<Impl>()) {}// конструктор 

KataGoAnalyzer::~KataGoAnalyzer() {// деструктор
    shutdown();
}

bool KataGoAnalyzer::initialize(const KataGoConfig& config) {
    pImpl->config = config;// сохраняем конфигурацию в пимпл
    
    if (config.maxVisits <= 0) {
        std::cerr << "Ошибка: maxVisits должен быть > 0" << std::endl;
        return false;
    }
    
    if (!fs::exists(config.katagoPath)) {
        std::cerr << "Ошибка: KataGo не найден по пути " << config.katagoPath << std::endl;
        return false;
    }
    
    if (!fs::exists(config.modelPath)) {
        std::cerr << "Ошибка: Модель не найдена по пути " << config.modelPath << std::endl;
        return false;
    }
    
    return pImpl->startProcess();// запуск процесса
}

bool KataGoAnalyzer::initialize(const std::string& katagoPath, // просто иницализатор(сеттер своего рода)
                                const std::string& modelPath,
                                const std::string& configPath) {
    KataGoConfig config;
    config.katagoPath = katagoPath;
    config.modelPath = modelPath;
    config.configPath = configPath;
    return initialize(config);
}

KataGoResult KataGoAnalyzer::analyzeSGF(const std::string& sgfContent) {
    return analyzeSGF(sgfContent, pImpl->config.boardSize, pImpl->config.komi);// берем параметры из конфигурации пимпл и делаем анализ
}

KataGoResult KataGoAnalyzer::analyzeSGF(const std::string& sgfContent, // можно и так запускать анализ
                                        int boardSize, 
                                        double komi) {
    KataGoResult result;
    
    if (!pImpl->isRunning) {//вкл или не вкл
        result.errorMessage = "KataGo не инициализирован";
        return result;
    }
    
    // Создаем временный файл
    std::string tempFile;
    try {
        tempFile = pImpl->createTempFile(sgfContent);// создание временного файла
    } catch (const std::exception& e) {
        result.errorMessage = e.what();
        return result;
    }
    
    // Используем соответствующий режим анализа
    std::string analysisCmd;// выбрать режиим анализа
    if (pImpl->config.analysisMode == "kata-analyze") {// если там анализ то анализ
        analysisCmd = "kata-analyze " + std::to_string(pImpl->config.maxVisits);
    } else {
        analysisCmd = "final_score";// если там счет то просто счет
    }
    
    // Отправляем команды
    pImpl->sendGTPCommand("boardsize " + std::to_string(boardSize));// отправляем команды
    pImpl->sendGTPCommand("komi " + std::to_string(komi));
    pImpl->sendGTPCommand("clear_board");
    pImpl->sendGTPCommand("loadsgf " + tempFile);
    
    std::string response = pImpl->sendGTPCommand(analysisCmd);// получаем ответ
    
    // Парсим ответ
    if (pImpl->config.analysisMode == "kata-analyze") {
        result = pImpl->parseAnalyzeResponse(response);// разыне режимы анализа
    } else {
        result = pImpl->parseFinalScoreResponse(response);
    }
    
    // Удаляем временный файл
    try {
        fs::remove(tempFile);
    } catch (...) {}
    
    return result;
}

KataGoResult KataGoAnalyzer::analyzePosition(const std::vector<std::string>& moves) {// анализ не через sgf а через историю просто
    return analyzePosition(moves, pImpl->config.boardSize, pImpl->config.komi, pImpl->config.maxVisits);
}

KataGoResult KataGoAnalyzer::analyzePosition(const std::vector<std::string>& moves,
                                             int boardSize,
                                             double komi,
                                             int maxVisits) {
    KataGoResult result;
    
    if (!pImpl->isRunning) {
        result.errorMessage = "KataGo не инициализирован";
        return result;
    }
    
    if (maxVisits <= 0) {
        result.errorMessage = "maxVisits должен быть > 0";
        return result;
    }
    
    // Инициализация доски
    pImpl->sendGTPCommand("boardsize " + std::to_string(boardSize));
    pImpl->sendGTPCommand("komi " + std::to_string(komi));
    pImpl->sendGTPCommand("clear_board");
    
    // Выполняем ходы
    for (const auto& move : moves) {
        std::string response = pImpl->sendGTPCommand("play " + move);
        if (response.find("illegal move") != std::string::npos) {
            result.errorMessage = "Неверный ход: " + move;
            return result;
        }
    }
    
    // Анализ
    std::string response = pImpl->sendGTPCommand("kata-analyze " + std::to_string(maxVisits));
    return pImpl->parseAnalyzeResponse(response);
}

bool KataGoAnalyzer::loadSGF(const std::string& sgfContent) {
    if (!pImpl->isRunning) return false;
    
    std::string tempFile;
    try {
        tempFile = pImpl->createTempFile(sgfContent);
    } catch (...) {
        return false;
    }
    
    pImpl->sendGTPCommand("boardsize " + std::to_string(pImpl->config.boardSize));
    pImpl->sendGTPCommand("komi " + std::to_string(pImpl->config.komi));
    std::string response = pImpl->sendGTPCommand("loadsgf " + tempFile);
    
    try {
        fs::remove(tempFile);
    } catch (...) {}
    
    return response.find("=") == 0;
}

std::string KataGoAnalyzer::sendGTPCommand(const std::string& command) {
    return pImpl->sendGTPCommand(command);
}

void KataGoAnalyzer::clearBoard() {
    if (pImpl->isRunning) {
        pImpl->sendGTPCommand("clear_board");
    }
}

void KataGoAnalyzer::shutdown() {
    pImpl->shutdown();
}

bool KataGoAnalyzer::isAvailable(const std::string& katagoPath) {
    return fs::exists(katagoPath);
}