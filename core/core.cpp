// core.cpp
#include "core.h"
#include <iostream>
#include <filesystem>
#include <regex>

std::vector<Move> SGFParser::parseString(const std::string& sgfContent) {
    std::vector<Move> moves;
    
    //ищем ;
    size_t pos = sgfContent.find(';');
    if (pos == std::string::npos) return moves;
    
    // GM[1] FF[4] SZ[19] PB[Black] PW[White] KM[6.5] RE[B+12.5]
    
    int boardSize = 19;
    std::string playerBlack, playerWhite, komi = "6.5", result;
    Rules pRules = Rules::Chinese;
    
    
    //размер
    std::regex szRegex(R"(SZ\[(\d+)\])");
    std::smatch match;
    std::string sgfStr(sgfContent);
    if (std::regex_search(sgfStr, match, szRegex)) {
        boardSize = std::stoi(match[1]);
    }

     std::regex ruRegex(R"(RU\[([^\]]*)\])");
    if (std::regex_search(sgfStr, match, ruRegex)) {
        pRules = rulesFromString(match[1].str());
    }
    
    //имена
    std::regex pbRegex(R"(PB\[([^\]]*)\])");
    if (std::regex_search(sgfStr, match, pbRegex)) {
        playerBlack = match[1];
    }
    
    std::regex pwRegex(R"(PW\[([^\]]*)\])");
    if (std::regex_search(sgfStr, match, pwRegex)) {
        playerWhite = match[1];
    }
    
    //коми
    std::regex kmRegex(R"(KM\[([^\]]*)\])");
    if (std::regex_search(sgfStr, match, kmRegex)) {
        komi = match[1];
    }
    
    //результат
    std::regex reRegex(R"(RE\[([^\]]*)\])");
    if (std::regex_search(sgfStr, match, reRegex)) {
        result = match[1];
    }
    
    //;B[dd] ;W[ab] ;B[] пас
    std::regex moveRegex(R"(;([BW])\[([a-z]{0,2})\])");
    auto movesBegin = std::sregex_iterator(sgfContent.begin(), sgfContent.end(), moveRegex);
    auto movesEnd = std::sregex_iterator();
    
    int moveNum = 1;
    for (auto it = movesBegin; it != movesEnd; ++it) {
        std::smatch moveMatch = *it;
        std::string colorStr = moveMatch[1].str();
        std::string coordStr = moveMatch[2].str();
        
        Color color = (colorStr == "B") ? Color::Black : Color::White;
        
        if (coordStr.empty()) {
            //пас
            moves.emplace_back(color, moveNum);
        } else if (coordStr.length() == 2) {
            Position pos = parsePosition(coordStr);
            moves.emplace_back(pos.x, pos.y, color, moveNum);
        }
        moveNum++;
    }
    
    return moves;
}

std::vector<Move> SGFParser::parseFile(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cout << "Не удалось открыть файл: " << filename << std::endl;
        return {};
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    return parseString(buffer.str());
}

Position SGFParser::parsePosition(const std::string& coordStr) {
    Position pos{-1, -1};
    
    if (coordStr.length() >= 1) {
        char xChar = coordStr[0];
        if (xChar >= 'a' && xChar <= 'z') {
            int val = xChar - 'a';
            if (val >= 8) val--; //без i
            pos.x = val;
        }
    }
    
    if (coordStr.length() >= 2) {
        char yChar = coordStr[1];
        if (yChar >= 'a' && yChar <= 'z') {
            int val = yChar - 'a';
            if (val >= 8) val--;
            pos.y = val;
        }
    }
    
    return pos;
}

bool SGFParser::loadGame(Game& game, const std::string& filename) {
    std::vector<Move> moves = parseFile(filename);
    if (moves.empty()) {
        std::cout << "Не найдено ходов в SGF файле" << std::endl;
        return false;
    }
    
    game.reset();
    
    //делаем ходы
    for (const auto& move : moves) {
        if (move.isPass) {
            game.makeMove(-1, -1, true);
        } else {
            game.makeMove(move.pos.x, move.pos.y, false);
        }
    }
    
    return true;
}
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
    sgf << "RU[" << rulesToString(rules) << "]";
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

bool Game::makeMove(int x, int y, bool isPass)
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
            legalMoves = rePosMoves(board, currentPlayer);
        }
        return true;
    }

    Position p{x, y};
    if (board.addStone(p, currentPlayer))
    {   
        recordMove(x, y, false);
        passes = 0;
        currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
        legalMoves = rePosMoves(board, currentPlayer);
        return true;  // ход успешен
    }
    return false;  // ход отклонён
}

void Game::reset(int newSize ) {
    board = Board(newSize);
    legalMoves = Board(newSize);
    currentPlayer = Color::Black;
    passes = 0;
    gameOver = false;
    moveNumber = 1;
    sgf = SGFGame(newSize);
    sgf.setRules(rules);
    sgf.setKomi(std::to_string(komi));
    moveHistory.clear();
    sgf.setPlayerNames("Player1", "Player2");
}

bool Game::loadFromSGF(const std::string& filename) {
    std::vector<Move> loadedMoves = SGFParser::parseFile(filename);
    if (loadedMoves.empty()) {
        std::cout << "Не удалось загрузить SGF файл" << std::endl;
        return false;
    }
    
    //размер
    int loadedSize = getBoardSizeFromSGF(filename);
    reset(loadedSize);
    
    //делаем ходы
    for (const auto& move : loadedMoves) {
        if (move.isPass) {
            makeMove(-1, -1, true);
        } else {
            makeMove(move.pos.x, move.pos.y, false);
        }
    }
    
    return true;
}

int getBoardSizeFromSGF(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) return 19;
    
    std::string content((std::istreambuf_iterator<char>(file)),
                         std::istreambuf_iterator<char>());
    
    std::regex szRegex(R"(SZ\[(\d+)\])");
    std::smatch match;
    if (std::regex_search(content, match, szRegex)) {
        return std::stoi(match[1]);
    }
    return 19;
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