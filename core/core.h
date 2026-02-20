// core.h
#pragma once
#include <vector>
#include <string>
#include <sstream>
#include <fstream>
#include "Board_new.h"

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
    
public:
    SGFGame() = default;
    SGFGame(int size);
    void addMove(const Move& move);
    void setPlayerNames(const std::string& black, const std::string& white);
    void setResult(const std::string& res);
    std::string posToSGF(const Position &p) const;
    std::string generateSGF() const;
    bool saveToFile(const std::string& filename) const;
    const std::vector<Move>& getMoves() const { return moves; }
    void clear() { moves.clear(); }
};

class Game {
private:
    Board board;
    Color currentPlayer = Color::Black;
    int passes = 0;
    bool gameOver = false;
    int moveNumber = 1;
    SGFGame sgf;
    std::vector<Move> moveHistory;
    
public:
    Game(int n = 9);
    void recordMove(int x, int y, bool isPass = false);
    bool undoLastMove();
    std::string getSGF() const;
    bool saveGame(const std::string& filename) const;
    void makeMove(int x, int y, bool isPass = false);
    bool isGameOver() const { return gameOver; }
    Color getCurrentPlayer() const { return currentPlayer; }
    int getMoveNumber() const { return moveNumber; }
    int getPasses() const { return passes; }
    Board& getBoard() { return board; }
    const Board& getBoard() const { return board; }
};