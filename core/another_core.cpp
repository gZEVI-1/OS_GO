#include <vector>
#include <queue>
#include <set>
#include "Board_new.h"
class Game
{
private:
    Board board;
    Color currentPlayer;

public:
    Game(int n = 9) : board(n), currentPlayer(Color::Black) {}

    void switchPlayer()
    {
        currentPlayer = (currentPlayer == Color::Black) ? Color::White
                                                        : Color::Black;
    }

    void printBoard_console() const
    {
        board.simple_print();
    }

    void printCurrentPlayer_console() const
    {
        cout << "Ходят: "
             << (currentPlayer == Color::Black ? "черные" : "белые ")
             << "\n";
    }


    void makeMove_console()
    {
        int x, y;
        while (true)
        {
            cout << "Введите (x y), или 0 0 для паса: ";
            cin >> x >> y;
            x -= 1;
            y -= 1;
            if (!cin)
            {
                cin.clear();
                cin.ignore(10000, '\n');
                cout << "Неверный ввод\n";
                continue;
            }
            if (x == -1 && y == -1)
            {
                cout << "Игрок пасует\n";
                break;
            }
            Position p{x, y};
            if (board.addStone(p, currentPlayer))
            {
                break;
            }
            else
            {
                cout << "Ход недопустим, попробуйте еще раз.\n";
            }
        }
        switchPlayer();
    }

    void loop()
    {
        while (true)
        {
            printBoard_console();
            printCurrentPlayer_console();
            makeMove_console();
        }
    }
};

int main()
{
    setlocale(LC_ALL, ".UTF8");
    Game game(9);
    game.loop();
    return 0;
}