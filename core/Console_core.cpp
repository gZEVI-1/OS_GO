#include <vector>
#include <queue>
#include <Windows.h>
#include <set>
#include <sstream>
#include <fstream>
#include <iostream>

#include "Board_new.h"
#include "core.h"
using namespace std;

struct Move
{
    Position pos;
    Color color;
    int moveNumber;
    bool isPass;

    Move() : pos{-1, -1}, color(Color::None), moveNumber(0), isPass(true) {}
    Move(int x, int y, Color c, int num) : pos{x, y}, color(c), moveNumber(num), isPass(false) {}
    Move(Color c, int num) : pos{-1, -1}, color(c), moveNumber(num), isPass(true) {} // пас
};

class SGFGame
{
private:
    vector<Move> moves;
    int boardSize;
    string playerBlack;
    string playerWhite;
    string result;
    string komi;

public:
    SGFGame()
    {
        boardSize = 9;
        komi = "6.5";
    }

    SGFGame(int size)
    {
        if (size < 9)
        {
            cout << "размер доски должен быть не менее 9х9";
            boardSize = 9;
        }
        else
        {
            boardSize = size;
        }
        komi = "6.5";
    }

    SGFGame(int size, string playerB, string playerW, string Komi)
    {
        if (size < 9)
        {
            cout << "размер доски должен быть не менее 9х9";
            boardSize = 9;
        }
        else
        {
            boardSize = size;
        }
        playerBlack = playerB;
        playerWhite = playerW;
        komi = Komi;
    }

    void addMove(const Move &move)
    {
        moves.push_back(move);
    }

    void setPlayerNames(const string &black, const string &white)
    {
        playerBlack = black;
        playerWhite = white;
    }

    void setResult(const string &res)
    {
        result = res;
    }

    string  posToSGF(const Position &p) const
    {
        if (p.x == -1 || p.y == -1)
            return ""; // пас

        auto convert = [](int coord) -> char
        {
            if (coord < 0)
                return '?';
            else if (coord < 26)
                return 'a' + coord; // a-z для 0-25
            else if (coord < 52)
                return 'A' + (coord - 26); // A-Z для 26-51
            return '?';                   // больше 52 - ошибка
        };

        if (p.x >= 52 || p.y >= 52)
        {
            cout << "Ошибка: координаты выходят за пределы поддерживаемого SGF формата\n";
            return "??";
        }

        char x = convert(p.x);
        char y = convert(p.y);
        return string(1, x) + string(1, y);
    }

    string generateSGF() const
    {
        ostringstream sgf;
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
                string coords = posToSGF(m.pos);
                sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[" << coords << "]";
            }
        }
        sgf << ")";
        return sgf.str();
    }

    bool    saveToFile(const string &filename) const
    {
        ofstream file(filename);
        if (!file.is_open())
            return false;
        file << generateSGF();
        file.close();
        return true;
    }

    const vector<Move> &getMoves() const { return moves; }
    void clear() { moves.clear(); }
};

class Game
{
private:
    Board board;
    Color currentPlayer;
    int passes;
    bool gameOver;
    int moveNumber;
    SGFGame sgf;
    vector<Move> moveHistory;

public:
    Game(int n = 9)
        : board(n),
          currentPlayer(Color::Black),
          passes(0),
          gameOver(false),
          moveNumber(1),
          sgf(n)
    {
        sgf.setPlayerNames("Игрок1", "Игрок2");
    }

    void recordMove(int x, int y, bool isPass = false)
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

    bool undoLastMove()
    {
        if (moveHistory.empty())
        {
            cout << "Нет ходов для отмены\n";
            return false;
        }

        Move lastMove = moveHistory.back();
        if (!lastMove.isPass)
        {
            if (!board.removeStone(lastMove.pos))
            {
                cout << "Ошибка при удалении камня\n";
                return false;
            }
            cout << "Удален камень с позиции (" << lastMove.pos.x + 1 << ","
                 << lastMove.pos.y + 1 << ")\n";
        }
        else
        {
            cout << "Отменен пас\n";
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

        cout << "Ход отменен. Текущий игрок: "
             << (currentPlayer == Color::Black ? "Черные" : "Белые") << "\n";
        return true;
    }

    string getSGF() const
    {
        return sgf.generateSGF();
    }

    bool saveGame(const string &filename) const
    {
        return sgf.saveToFile(filename);
    }

    void sendToFile()
    {
        string sgfContent = getSGF();
        ofstream temp("temp_game.sgf");
        temp << sgfContent;
        temp.close();
        cout << "Игра сохранена в temp_game.sgf для GnuGo\n";
    }

    void makeMove_console()
    {
        int x, y;
        while (true)
        {
            cout << "Введите x y (0 0 для паса, u для отмены, s для сохранения): ";
            string input;
            cin >> input;

            if (input == "u" || input == "U")
            {
                if (undoLastMove())
                {
                    board.simple_print();
                    continue;
                }
                else
                {
                    cout << "Нечего отменять\n";
                    continue;
                }
            }

            if (input == "s" || input == "S")
            {
                saveGame("game_record.sgf");
                cout << "Игра сохранена в game_record.sgf\n";
                continue;
            }

            try
            {
                x = stoi(input);
                cin >> y;
            }
            catch (...)
            {
                cout << "Неверный ввод\n";
                cin.clear();
                cin.ignore(10000, '\n');
                continue;
            }

            if (x == 0 && y == 0)
            {
                cout << "Пас\n";
                recordMove(-1, -1, true);
                passes++;
                if (passes >= 2)
                {
                    gameOver = true;
                    cout << "Партия окончена двумя пасами подряд.\n";
                    sgf.setResult("Void");
                    saveGame("final_game.sgf");
                }
                else
                {
                    currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
                }
                break;
            }

            x--;
            y--;
            Position p{x, y};
            if (board.addStone(p, currentPlayer))
            {
                recordMove(x, y, false);
                passes = 0;
                currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
                break;
            }
            else
            {
                cout << "Недопустимый ход!\n";
            }
        }
    }

   

    void loop()
    {
        while (!gameOver)
        {
            board.simple_print();
            cout << "Ход #" << moveNumber << ": "
                 << (currentPlayer == Color::Black ? "Черные" : "Белые") << "\n";
            makeMove_console();
        }
    }
};

