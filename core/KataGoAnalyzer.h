// KataGoAnalyzer.h
#pragma once
#include <string>
#include <vector>
#include <memory>
#include <functional>

// Результат анализа партии
struct KataGoResult {
    double winrate;           // 0.0-1.0 для текущего игрока
    double scoreLead;         // преимущество в очках (положительное = черные/текущий игрок)
    std::string winner;       // "Black", "White", "Draw"
    double blackScore;        // очки черных
    double whiteScore;        // очки белых
    double komi;              // использованное коми
    std::string bestMove;     // лучший ход в формате SGF
    std::vector<std::string> topMoves; // топ-5 ходов
    bool success;
    std::string errorMessage;
};

// Результат анализа позиции (для текущего состояния)
struct KataGoPositionResult {
    double winrate;           // 0.0-1.0 для текущего игрока
    double scoreLead;         // преимущество в очках
    std::vector<std::pair<std::string, double>> moveRankings; // (ход, winrate)
    int visits;
    std::string ownership;    // владение территорией (строка с данными)
    bool success;
    std::string errorMessage;
};

// Класс для взаимодействия с KataGo
class KataGoAnalyzer {
public:
    KataGoAnalyzer();
    ~KataGoAnalyzer();
    
    // Инициализация анализатора
    bool initialize(const std::string& katagoPath, 
                   const std::string& modelPath,
                   const std::string& configPath = "");
    
    // Анализ SGF файла (подсчет очков после завершения партии)
    KataGoResult analyzeSGF(const std::string& sgfContent, int boardSize = 19, double komi = 6.5);
    
    // Анализ текущей позиции (промежуточная оценка)
    KataGoPositionResult analyzePosition(const std::vector<std::string>& moves, 
                                         int boardSize = 19, 
                                         double komi = 6.5,
                                         int maxVisits = 500);
    
    // Анализ позиции из SGF (альтернативный метод)
    KataGoPositionResult analyzePositionFromSGF(const std::string& sgfContent, 
                                                int maxVisits = 500);
    
    // Получить лучший ход для текущей позиции
    std::string getBestMove(const std::vector<std::string>& moves, 
                           int boardSize = 19, 
                           double komi = 6.5);
    
    // Очистка и завершение работы
    void shutdown();
    
    // Проверка доступности KataGo
    static bool isAvailable(const std::string& katagoPath);
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;
};