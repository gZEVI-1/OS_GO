// KataGoAnalyzer.h
#pragma once
#include <string>
#include <vector>
#include <memory>

// Конфигурация KataGo
struct KataGoConfig {
    std::string katagoPath;
    std::string modelPath;
    std::string configPath;
    int maxVisits = 500;
    double maxTime = 0.0;
    double komi = 6.5;
    int boardSize = 19;
    bool logToStdout = false;
};

// Результат анализа партии
struct KataGoResult {
    double winrate = 0.0;
    double scoreLead = 0.0;
    std::string winner;
    double blackScore = 0.0;
    double whiteScore = 0.0;
    double komi = 6.5;
    std::string bestMove;
    std::vector<std::string> topMoves;
    std::string ownership;
    int visits = 0;
    bool success = false;
    std::string errorMessage;
};

struct SGFInfo {
    std::string filename;
    std::string fullPath;
    std::string playerBlack;
    std::string playerWhite;
    std::string result;
    double komi = 6.5;
    int boardSize = 19;
    int moveCount = 0;
    std::string date;
    size_t fileSize = 0;
    bool valid = false;
};


// Основной класс анализатора
class KataGoAnalyzer {
public:
    KataGoAnalyzer();
    ~KataGoAnalyzer();
    
    bool initialize();
    bool initialize(const std::string& katagoPath, 
                   const std::string& modelPath,
                   const std::string& configPath = "");
    bool initialize(const KataGoConfig& config);
    
    static void setDefaultPaths(const std::string& katagoPath, 
                                const std::string& modelPath, 
                                const std::string& configPath = "");
    static bool autoDetectPaths();
    static bool isAvailable();
    static bool isAvailable(const std::string& katagoPath);
    
    KataGoResult analyzeSGF(const std::string& sgfContent, 
                           int boardSize = 19, 
                           double komi = 6.5);

    KataGoResult analyzeSGFFile(const std::string& filepath,
                                int boardSize = -1,  // -1 = автоопределение
                                double komi = -1);    // -1 = автоопределение
    
    // Работа с папкой SGF файлов
    static std::string getLoadedSGFPath();
    static std::vector<SGFInfo> listSGFFiles(const std::string& directory = "");
    static SGFInfo parseSGFInfo(const std::string& filepath);
    static std::string readSGFFile(const std::string& filepath);
    
    void shutdown();
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;
    
    static std::string s_defaultKatagoPath;
    static std::string s_defaultModelPath;
    static std::string s_defaultConfigPath;
    static bool s_pathsSet;
};