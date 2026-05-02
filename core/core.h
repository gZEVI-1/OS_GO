// core.h
#pragma once
#include <vector>
#include <string>
#include <sstream>
#include <fstream>
#include "Board_new.h"

// ============================================================================
// Правила игры — ДОЛЖНЫ БЫТЬ ДО ВСЕХ КЛАССОВ, КОТОРЫЕ ИХ ИСПОЛЬЗУЮТ
// ============================================================================
enum class Rules {
    Chinese,
    Japanese
};

inline std::string rulesToString(Rules r) {
    return (r == Rules::Chinese) ? "Chinese" : "Japanese";
}

inline Rules rulesFromString(const std::string& s) {
    if (s == "Japanese" || s == "JP") return Rules::Japanese;
    return Rules::Chinese;
}

// ============================================================================

int getBoardSizeFromSGF(const std::string& filename);

struct Move {
    Position pos{-1,-1};
    Color color = Color::None;
    int moveNumber = 0;
    bool isPass = true;
    
    Move() = default;
    Move(int x, int y, Color c, int num) : pos{x,y}, color(c), moveNumber(num), isPass(false) {}
    Move(Color c, int num) : color(c), moveNumber(num), isPass(true) {}
};

class SGFGame {
private:
    std::vector<Move> moves;
    int boardSize = 9;
    std::string playerBlack, playerWhite, result, komi = "6.5";
    Rules rules = Rules::Chinese;          // <-- НОВОЕ
    
public:
    SGFGame() = default;
    SGFGame(int size);
    void addMove(const Move& move);
    void setPlayerNames(const std::string& black, const std::string& white);
    void setResult(const std::string& res);
    void setRules(Rules r) { rules = r; }  // <-- НОВОЕ
    Rules getRules() const { return rules; } // <-- НОВОЕ
    void setKomi(const std::string& k) { komi = k; } // <-- НОВОЕ
    std::string posToSGF(const Position &p) const;
    std::string generateSGF() const;
    bool saveToFile(const std::string& filename) const;
    const std::vector<Move>& getMoves() const { return moves; }
    void clear() { moves.clear(); }
};

class SGFParser {
public:
    static std::vector<Move> parseFile(const std::string& filename);
    static std::vector<Move> parseString(const std::string& sgfContent);
    static bool loadGame(Game& game, const std::string& filename);
    
private:
    static std::string extractProperty(const std::string& sgf, const std::string& propName, size_t startPos);
    static Position parsePosition(const std::string& coordStr);
};

class Game {
private:
    Board board;
    Board legalMoves;
    Color currentPlayer = Color::Black;
    int passes = 0;
    bool gameOver = false;
    int moveNumber = 1;
    SGFGame sgf;
    std::vector<Move> moveHistory;
    Rules rules = Rules::Chinese;  // <-- НОВОЕ
    double komi = 6.5;             // <-- НОВОЕ
    
public:
    Game(int n = 9);
    
    // НОВОЕ: правила и коми
    void setRules(Rules r) { rules = r; sgf.setRules(r); }
    Rules getRules() const { return rules; }
    void setKomi(double k) { komi = k; }
    double getKomi() const { return komi; }
    
    bool isOk(Position& p, Board& b, Color playerColor);
    Board rePosMoves(Board& releBoard, Color playerColor);
    Board& getLegalMoves() { return legalMoves; }
    void recordMove(int x, int y, bool isPass = false);
    bool undoLastMove();
    std::string getSGF() const;
    bool saveGame(const std::string& filepath) const;
    bool makeMove(int x, int y, bool isPass = false);
    bool isGameOver() const { return gameOver; }
    Color getCurrentPlayer() const { return currentPlayer; }
    int getMoveNumber() const { return moveNumber; }
    int getPasses() const { return passes; }
    Board& getBoard() { return board; }
    const Board& getBoard() const { return board; }
    void reset(int newSize = 9);
    bool loadFromSGF(const std::string& filename);
};