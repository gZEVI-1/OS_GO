#include <vector>
#include <queue>
#include <Windows.h>
#include <set>
#include <sstream>
#include <fstream>
#include "Board_new.h"
using namespace std;


//КЛЮЧЕВОЕ: НЕТ ПРОВЕРКИ НА КОРРЕКТНОСТЬ ХОДОВ
//МОЖНО ДОБАВИТЬ РАБОТУ С ПИТОНОМ ЧЕРЕЗ ПОТОК

//НОРМ
struct Move {
    Position pos;
    Color color;
    int moveNumber;
    bool isPass;
    
    Move() : pos{-1, -1}, color(Color::None), moveNumber(0), isPass(true) {}
    Move(int x, int y, Color c, int num) : pos{x, y}, color(c), moveNumber(num), isPass(false) {}
    Move(Color c, int num) : pos{-1, -1}, color(c), moveNumber(num), isPass(true) {} // пас
};

//ДОДЕЛАТЬ
class SGFGame {
private:
    vector<Move> moves;
    int boardSize;
    string playerBlack;
    string playerWhite;
    string result;
    string komi;
    string date;
    
public:
    // ПОТОМ ДОРАБОТАТЬ
    SGFGame(int size = 9) : boardSize(size), komi("6.5") {
        // // Установить текущую дату
        // time_t t = time(nullptr);
        // tm* tm = localtime(&t);
        // char buf[16];
        // strftime(buf, sizeof(buf), "%Y-%m-%d", tm);
        // date = buf;
    }
    
    //ПРОВЕРКА
    void addMove(const Move& move) {
        moves.push_back(move);
    }
    
    void setPlayerNames(const string& black, const string& white) {
        playerBlack = black;
        playerWhite = white;
    }
    
    void setResult(const string& res) {
        result = res;
    }
    
    // ПЕРЕДЕЛАТЬ( ДЛЯ ВСЕХ РАЗМЕРОВ ДОСОК(ВКЛЮЧАЯ НЕСТАНДАРНТНЫЕ) УЧИТЫВАЯ ОТСУТСТВИЕ БУКВЫ i)
    string posToSGF(const Position& p) const {
        if (p.x == -1 || p.y == -1) return ""; // пас
        
        char x = 'a' + p.x;
        char y = 'a' + p.y;
        
        // Для досок больше 19 нужно использовать другую схему
        // Но для 9x9 достаточно a-i
        return string(1, x) + string(1, y);
    }
    
    // НОРМ
    string generateSGF() const {
        ostringstream sgf;
        
        // Заголовок
        sgf << "(;GM[1]FF[4]SZ[" << boardSize << "]";
        
        // Информация об игроках
        if (!playerBlack.empty()) sgf << "PB[" << playerBlack << "]";
        if (!playerWhite.empty()) sgf << "PW[" << playerWhite << "]";
        
        // Правила и коми
        sgf << "KM[" << komi << "]";
        sgf << "RU[Chinese]"; // или Japanese
        
        // Дата
        // sgf << "DT[" << date << "]";
        
        // Результат
        if (!result.empty()) sgf << "RE[" << result << "]";
        
        // Ходы
        for (size_t i = 0; i < moves.size(); ++i) {
            const Move& m = moves[i];
            
            if (m.isPass) {
                // Пас
                sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[]";
            } else {
                // Обычный ход
                string coords = posToSGF(m.pos);
                sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[" << coords << "]";
            }
        }
        
        sgf << ")";
        
        return sgf.str();
    }
    
    //НОРМ
    bool saveToFile(const string& filename) const {
        ofstream file(filename);
        if (!file.is_open()) return false;
        
        file << generateSGF();
        file.close();
        return true;
    }
    
    
    const vector<Move>& getMoves() const { return moves; }
    
    void clear() { moves.clear(); }
};

//ДОРАБОТАТЬ
class Game {
private:
    Board board;
    Color currentPlayer;
    int blackCaptured;
    int whiteCaptured;
    int passes;
    bool gameOver;
    int moveNumber;
    const double KOMI = 6.5;
    
    // История игры
    SGFGame sgf;
    vector<Move> moveHistory;
    
public:
    Game(int n = 9) : board(n), currentPlayer(Color::Black), 
                      blackCaptured(0), whiteCaptured(0), 
                      passes(0), gameOver(false), moveNumber(1),
                      sgf(n) {
        
        sgf.setPlayerNames("Human", "GNU Go"); // По умолчанию
    }
    
    // ДОБАВИТЬ ПРОВЕРКУ
    void recordMove(int x, int y, bool isPass = false) {
        Move move;
        if (isPass) {
            move = Move(currentPlayer, moveNumber);
        } else {
            move = Move(x, y, currentPlayer, moveNumber);
        }
        
        moveHistory.push_back(move);
        sgf.addMove(move);
        moveNumber++;
    }
    
    // НЕТ ПЕРЕЗАПИСИ SGF. ИЛИ ДОБАВИТЬ, ИЛИ УБРАТЬ В recordMove И ДОБАВИТЬ З
    bool undoLastMove() {
        if (moveHistory.empty()) return false;
        
        Move lastMove = moveHistory.back();
        
        // Удаляем камень с доски
        if (!lastMove.isPass) {
            board.removeStone(lastMove.pos);
        }
        
        moveHistory.pop_back();
        moveNumber--;
        
        // Меняем игрока обратно
        currentPlayer = lastMove.color;
        
        return true;
    }
    
    // НОРМ
    string getSGF() const {
        return sgf.generateSGF();
    }
    
    //ВРОДЕ НОРМ (ПРОВЕРИТЬ)
    bool saveGame(const string& filename) const {
        return sgf.saveToFile(filename);
    }
    
    
    // ПОСМОТРЕТЬ БОЛЬШЕ( МБ ЭТО НЕ БУДЕТ РАБОТАТЬ, НО ИДЕЯ С ВРЕМЕННЫМ ФАЙЛОМ ХОРОШАЯ)
    void sendToFile() {
        // Сохраняем текущую позицию в SGF
        string sgfContent = getSGF();
        
        // Можно сохранить во временный файл
        ofstream temp("temp_game.sgf");
        temp << sgfContent;
        temp.close();
        
        // Здесь можно вызвать GnuGo с этим файлом
        // system("gnugo -l temp_game.sgf --mode gtp");
        
        cout << "Игра сохранена в temp_game.sgf для GnuGo\n";
    }
    
    
    
    // НЕТ СМЫСЛА (У НАС СВЯЗЬ С ПИТОНОМ ЧЕРЕЗ МЕТОДЫ , НО НЕ ЧЕРЕЗ КОНСОЛЬ)(МОЖНО ОСТАВИТЬ ДЛЯ ТЕСТОВ)(ПЕРЕДЕЛАТЬ ДЛЯ ПИТОНА)
    void makeMove_console() {
        int x, y;
        while (true) {
            cout << "Введите x y (0 0 для паса, u для отмены, s для сохранения): ";
            string input;
            cin >> input;
            
            if (input == "u" || input == "U") {
                if (undoLastMove()) {
                    cout << "Ход отменен\n";
                    board.simple_print();
                    continue;
                } else {
                    cout << "Нечего отменять\n";
                    continue;
                }
            }
            
            if (input == "s" || input == "S") {
                saveGame("game_record.sgf");
                cout << "Игра сохранена в game_record.sgf\n";
                continue;
            }
            
            // Пробуем преобразовать в числа
            try {
                x = stoi(input);
                cin >> y;
            } catch (...) {
                cout << "Неверный ввод\n";
                cin.clear();
                cin.ignore(10000, '\n');
                continue;
            }
            
            if (x == 0 && y == 0) {
                cout << "Пас\n";
                recordMove(-1, -1, true); // Записываем пас
                passes++;
                
                if (passes >= 2) {
                    gameOver = true;
                    showScore();
                    
                    // Сохраняем результат в SGF
                    string result = (blackCaptured > whiteCaptured) ? "B+" : "W+";
                    sgf.setResult(result);
                    saveGame("final_game.sgf");
                }
                break;
            }
            
            x--; y--; // в 0-индексацию
            Position p{x, y};
            
            if (board.addStone(p, currentPlayer)) {
                recordMove(x, y, false); // Записываем обычный ход
                passes = 0;
                
                // Здесь можно обновить счет захваченных
                currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
                break;
            } else {
                cout << "Недопустимый ход!\n";
            }
        }
    }
    
    //БУДЕТ ЧЕРЕЗ ПИТОН
    void showScore() {
        cout << "In progress";
        // auto [black, white] = board.countScore();
        
        // cout << "\n=== СЧЕТ ===\n";
        // cout << "Территория черных: " << black << "\n";
        // cout << "Территория белых: " << white << "\n";
        
        // double finalBlack = black + whiteCaptured;
        // double finalWhite = white + blackCaptured + KOMI;
        
        // cout << "ИТОГО:\n";
        // cout << "Черные: " << finalBlack << "\n";
        // cout << "Белые: " << finalWhite << "\n";
        
        // if (finalBlack > finalWhite) {
        //     cout << "Победили черные!\n";
        //     sgf.setResult("B+" + to_string(finalBlack - finalWhite));
        // } else {
        //     cout << "Победили белые!\n";
        //     sgf.setResult("W+" + to_string(finalWhite - finalBlack));
        // }
    }
    
    void loop() {
        while (!gameOver) {
            board.simple_print();
            cout << "Ход #" << moveNumber << ": " 
                 << (currentPlayer == Color::Black ? "Черные" : "Белые") << "\n";
            makeMove_console();
        }
    }
};
//ОЧЕВИДНО АДАПТИРОВАТЬ
int main(){
    Game game;
    game.loop();
    return 0;
}