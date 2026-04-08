// KataGoAnalyzer.h
#pragma once
#include <string>
#include <vector>
#include <memory>
#include <windows.h>

struct KataGoResult {
    double winrate;           // 0.0-1.0 для текущего игрока
    double scoreLead;         // преимущество в очках
    std::string winner;       // "Black", "White", "Draw"
    double blackScore;        // очки черных
    double whiteScore;        // очки белых
    double komi;              // использованное коми
    std::string bestMove;     // лучший ход в формате SGF
    std::vector<std::string> topMoves;
    std::string ownership;    // карта владения территорией
    int visits;
    bool success;
    std::string errorMessage;
    
    KataGoResult() : winrate(0.5), scoreLead(0.0), blackScore(0.0), 
                     whiteScore(0.0), komi(6.5), visits(0), success(false) {}
};

struct KataGoConfig {
    std::string katagoPath;
    std::string modelPath;
    std::string configPath;
    int maxVisits = 500;
    int maxTime = 0;        
    double komi = 6.5;
    int boardSize = 19;
    bool logToStdout = false;
    std::string analysisMode = "kata-analyze"; // "kata-analyze" или "final_score"
    
    KataGoConfig() = default;
};

class KataGoAnalyzer {
public:
    KataGoAnalyzer();
    ~KataGoAnalyzer();
    
    bool initialize(const KataGoConfig& config);
    bool initialize(const std::string& katagoPath, 
                   const std::string& modelPath,
                   const std::string& configPath = "");

    KataGoResult analyzeSGF(const std::string& sgfContent);
    KataGoResult analyzeSGF(const std::string& sgfContent, int boardSize, double komi);
    
    
    KataGoResult analyzePosition(const std::vector<std::string>& moves);
    KataGoResult analyzePosition(const std::vector<std::string>& moves, 
                                 int boardSize, double komi, int maxVisits);
    
    
    bool loadSGF(const std::string& sgfContent);
    
    std::string sendGTPCommand(const std::string& command);
    
    void clearBoard();
    
    void shutdown();
    
    static bool isAvailable(const std::string& katagoPath);
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;
};