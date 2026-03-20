// core.cpp
#include "core.h"
#include <iostream>
#include <filesystem>

SGFGame::SGFGame(int size)
{
    if (size < 9)
    {
        std::cout << "размер доски должен быть не менее 9х9";
        boardSize = 9;
    }
    else
    {
        boardSize = size;
    }
    komi = "6.5";
}

void SGFGame::addMove(const Move& move)
{
    moves.push_back(move);
}

void SGFGame::setPlayerNames(const std::string& black, const std::string& white)
{
    playerBlack = black;
    playerWhite = white;
}

void SGFGame::setResult(const std::string& res)
{
    result = res;
}

std::string SGFGame::posToSGF(const Position &p) const
{
    if (p.x == -1 || p.y == -1)
        return "";

    auto convert = [](int coord) -> char
    {
        if (coord < 0)
            return '?';
        else if (coord < 26)
            return 'a' + coord;
        else if (coord < 52)
            return 'A' + (coord - 26);
        return '?';
    };

    if (p.x >= 52 || p.y >= 52)
    {
        std::cout << "Ошибка: координаты выходят за пределы поддерживаемого SGF формата\n";
        return "??";
    }

    char x = convert(p.x);
    char y = convert(p.y);
    return std::string(1, x) + std::string(1, y);
}

std::string SGFGame::generateSGF() const
{
    std::ostringstream sgf;
    sgf << "(;GM[1]FF[4]SZ[" << boardSize << "]";
    if (!playerBlack.empty())
        sgf << "PB[" << playerBlack << "]";
    if (!playerWhite.empty())
        sgf << "PW[" << playerWhite << "]";
    sgf << "KM[" << komi << "]";
    sgf << "RU[Chinese]";
    if (!result.empty())
        sgf << "RE[" << result << "]";
    for (size_t i = 0; i < moves.size(); ++i)
    {
        const Move &m = moves[i];
        if (m.isPass)
        {
            sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[]";
        }
        else
        {
            std::string coords = posToSGF(m.pos);
            sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[" << coords << "]";
        }
    }
    sgf << ")";
    return sgf.str();
}

bool SGFGame::saveToFile(const std::string& filename) const
{
    std::ofstream file(filename); 
    if (!file.is_open())
        return false;
    file << generateSGF();
    file.close();
    return true;
}

Game::Game(int n)
    : board(n),
      legalMoves(n),
      currentPlayer(Color::Black),
      passes(0),
      gameOver(false),
      moveNumber(1),
      sgf(n)
{
    sgf.setPlayerNames("Игрок1", "Игрок2");
}

void Game::recordMove(int x, int y, bool isPass)
{
    Move move;
    if (isPass)
    {
        move = Move(currentPlayer, moveNumber);
    }
    else
    {
        move = Move(x, y, currentPlayer, moveNumber);
    }

    moveHistory.push_back(move);
    sgf.addMove(move);
    moveNumber++;
}

bool Game::undoLastMove()
{
    if (moveHistory.empty())
    {
        std::cout << "Нет ходов для отмены\n";
        return false;
    }

    Move lastMove = moveHistory.back();
    if (!lastMove.isPass)
    {
        if (!board.removeStone(lastMove.pos))
        {
            std::cout << "Ошибка при удалении камня\n";
            return false;
        }
    }

    moveHistory.pop_back();

    SGFGame newSgf(board.getSize());
    for (size_t i = 0; i < moveHistory.size(); ++i)
    {
        newSgf.addMove(moveHistory[i]);
    }
    sgf = newSgf;

    moveNumber--;
    currentPlayer = lastMove.color;
    if (lastMove.isPass)
    {
        passes--;
        if (passes < 0)
            passes = 0;
    }

    return true;
}

std::string Game::getSGF() const
{
    return sgf.generateSGF();
}

bool Game::saveGame(const std::string& filepath) const
{
    // Создаём директории если нужно
    std::filesystem::path p(filepath);
    if (!p.parent_path().empty())
    {
        std::filesystem::create_directories(p.parent_path());
    }
    
    // Передаём полный путь в sgf.saveToFile
    return sgf.saveToFile(filepath);
}

// bool Game::isOk(Position& p, Board& b)
// {
//     // Проверка: не занята ли клетка
//     if (b.getColor(p) != Color::None)
//         return false;
    
//     // Проверка: не является ли ход запрещенным правилом ко
//     if (b.hasKo && p.x == b.koPoint.x && p.y == b.koPoint.y)
//         return false;
    
//     Board tempBoard = b;  // Предполагается, что у Board есть конструктор копирования
    
//     return tempBoard.addStone(p, getCurrentPlayer());// addStone сама проверит не приводит ли ход к самоубийству
// }




// Board Game::rePosMoves(Board& releBoard)
// {///////////////////
//     int bSize = releBoard.getSize();
//     Board posMoves(bSize);
//     Position pos;
//     for(int i = 0; i < bSize; i++)
//     {
//         for(int j =0; j < bSize; j++)
//         {
//             pos.x = i;
//             pos.y = j;
//         posMoves.grid[i][j] = (isOk(pos,releBoard)) ? Color::Black : Color::None;
//             }
//         }
//     return posMoves;
// }

bool Game::isOk(Position& p, Board& b, Color playerColor)
{
    // Проверка: не занята ли клетка
    if (b.getColor(p) != Color::None)
        return false;
    
    // Проверка: не является ли ход запрещенным правилом ко
    if (b.hasKo && p.x == b.koPoint.x && p.y == b.koPoint.y)
        return false;
    
    // Проверка на самоубийство через временную копию
    // addStone вернет false, если после хода группа игрока будет без дамэ
    Board tempBoard = b;
    return tempBoard.addStone(p, playerColor);
}

Board Game::rePosMoves(Board& releBoard, Color playerColor)
{
    int bSize = releBoard.getSize();
    Board posMoves(bSize);
    Position pos;
    
    for(int i = 0; i < bSize; i++)
    {
        for(int j = 0; j < bSize; j++)
        {
            pos.x = i;
            pos.y = j;
            // Явно передаем цвет игрока для проверки
            bool isLegal = isOk(pos, releBoard, playerColor);
            posMoves.grid[i][j] = isLegal ? Color::Black : Color::None;
        }
    }
    return posMoves;
}

void Game::makeMove(int x, int y, bool isPass)
{
    if (isPass || (x == -1 && y == -1))
    {
        recordMove(-1, -1, true);
        passes++;
        if (passes >= 2)
        {
            gameOver = true;
            sgf.setResult("Void");
        }
        else
        {
            currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
            // Обновляем legalMoves для нового текущего игрока
            legalMoves = rePosMoves(board, currentPlayer);
        }
        return;
    }

    Position p{x, y};
    if (board.addStone(p, currentPlayer))
    {   
        recordMove(x, y, false);
        passes = 0;
        // Переключаем игрока ПЕРЕД вычислением ходов
        currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
        // Теперь legalMoves содержит ходы для нового текущего игрока
        legalMoves = rePosMoves(board, currentPlayer);
    }
}
// void Game::makeMove(int x, int y, bool isPass)
// {
//     if (isPass || (x == -1 && y == -1))
//     {
//         recordMove(-1, -1, true);
//         passes++;
//         if (passes >= 2)
//         {
//             gameOver = true;
//             sgf.setResult("Void");
//         }
//         else
//         {
//             currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
//         }
//         return;
//     }

//     Position p{x, y};
//     if (board.addStone(p, currentPlayer))
//     {   legalMoves = rePosMoves(board);
//         recordMove(x, y, false);
//         passes = 0;
//         currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
//     }
//}