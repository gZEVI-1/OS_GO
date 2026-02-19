#include <vector>
#include <queue>
#include <Windows.h>
#include <set>
#include <sstream>
#include <fstream>
#include "Board_new.h"
using namespace std;

struct Move {
    Position pos;
    Color color;
    int moveNumber;
    bool isPass;
    
    Move() : pos{-1, -1}, color(Color::None), moveNumber(0), isPass(true) {}
    Move(int x, int y, Color c, int num) : pos{x, y}, color(c), moveNumber(num), isPass(false) {}
    Move(Color c, int num) : pos{-1, -1}, color(c), moveNumber(num), isPass(true) {} // пас
};

class SGFGame {
private:
    vector<Move> moves;
    int boardSize;
    string playerBlack;
    string playerWhite;
    string result;
    string komi;
    
public:
    SGFGame(){
        boardSize = 9;
    }

    SGFGame(int size){
       if(size < 9) {cout << "размер доски должен быть не менее 9х9"; 
            return; }
            boardSize = size;
    }

    SGFGame(int size, string playerB, string playerW, string Komi){
        if(size < 9) {cout << "размер доски должен быть не менее 9х9"; 
            return; }
        boardSize = size;
        playerBlack = playerB;
        playerWhite = playerW;
        komi = Komi;

    }
    
    
    void addMove(const Move& move) {// проверка там где метод используется строка 170
        moves.push_back(move);
    }
    
    void setPlayerNames(const string& black, const string& white) {
        playerBlack = black;
        playerWhite = white;
    }
    
    void setResult(const string& res) {
        result = res;
    }
    
    string posToSGF(const Position& p) const {
        if (p.x == -1 || p.y == -1) return ""; // пас
        
        // SGF использует буквы a-z, затем A-Z для больших досок
        // a=0, b=1, ..., z=25, A=26, B=27, ..., Z=51
        
        auto convert = [](int coord) -> char {
            if (coord < 0) return '?';
            else
            if (coord < 26) return 'a' + coord;        // a-z для 0-25
            else
            if (coord < 52) return 'A' + (coord - 26); // A-Z для 26-51
            return '?'; // больше 52 - ошибка
        };
        
        if (p.x >= 52 || p.y >= 52) {
            cout << "Ошибка: координаты выходят за пределы поддерживаемого SGF формата\n";
            return "??";
        }
        
        char x = convert(p.x);
        char y = convert(p.y);
        
        return string(1, x) + string(1, y);
    }
    
    string generateSGF() const {
        ostringstream sgf;
        
        sgf << "(;GM[1]FF[4]SZ[" << boardSize << "]";
        
        if (!playerBlack.empty()) sgf << "PB[" << playerBlack << "]";
        if (!playerWhite.empty()) sgf << "PW[" << playerWhite << "]";

        sgf << "KM[" << komi << "]";
        sgf << "RU[Chinese]"; // !!!!
        
        if (!result.empty()) sgf << "RE[" << result << "]";
        
        for (size_t i = 0; i < moves.size(); ++i) {
            const Move& m = moves[i];
            
            if (m.isPass) {
                sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[]";
            } else {
                string coords = posToSGF(m.pos);
                sgf << ";" << (m.color == Color::Black ? "B" : "W") << "[" << coords << "]";
            }
        }
        
        sgf << ")";
        
        return sgf.str();
    }
    
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
    
    SGFGame sgf;
    vector<Move> moveHistory;
    
public:
    Game(int n = 9) : board(n), currentPlayer(Color::Black), 
                      blackCaptured(0), whiteCaptured(0), 
                      passes(0), gameOver(false), moveNumber(1),
                      sgf(n) {
        
        sgf.setPlayerNames("Игрок1", "Игрок2"); // По умолчанию
    }
    
    void recordMove(int x, int y, bool isPass = false) {
        Move move;
        if (isPass) {
            move = Move(currentPlayer, moveNumber);
        } else {
            move = Move(x, y, currentPlayer, moveNumber);
        }
        
        moveHistory.push_back(move);
        Position h;
        h.x = x;
        h.y = y;
        if(!isSuicide(h,currentPlayer))
        {
        sgf.addMove(move);
        moveNumber++;
    }
        else{
            return;
        }
        
    }
    
    
     bool wouldCaptureOpponent(Position p, Color color) const {
        for (Position neighbor : board.neighbors(p)) {
            if (board.getColor(neighbor) == getOpponentColor(color)) {
                const Group opponentGroup = board.groups[board.findGroupIndex(neighbor)];
                // Если у группы противника только одно дыхание - это наша позиция
                if (opponentGroup.liberties.size() == 1) {
                    if (opponentGroup.liberties.find(p) != opponentGroup.liberties.end()) {
                        return true;
                    }
                }
            }
        }
        return false;
    }
    
    bool hasLibertiesAfterMove(Position p, Color color) const {
        for (Position neighbor : board.neighbors(p)) {
            if (board.getColor(neighbor) == Color::None) {
                return true;
            }
        }
        
        for (Position neighbor : board.neighbors(p)) {
            if (board.getColor(neighbor) == color) {
                const Group friendlyGroup = board.groups[board.findGroupIndex(neighbor)];
                // У союзной группы есть дыхания, не считая нашу позицию?
                for (Position lib : friendlyGroup.liberties) {
                    if (!(lib.x == p.x && lib.y == p.y)) {
                        return true;
                    }
                }
            }
        }
        
        return false;
    }
    
    bool isSuicide(Position p, Color color) const {
        // Если ход захватывает камни противника - разрешен
        if (wouldCaptureOpponent(p, color)) {
            return false;
        }
        
        // Иначе проверяем, будут ли дыхания после хода
        return !hasLibertiesAfterMove(p, color);
    }

   bool undoLastMove() {
        if (moveHistory.empty()) {
            cout << "Нет ходов для отмены\n";
            return false;
        }
        
        Move lastMove = moveHistory.back();
        
        if (!lastMove.isPass) {
            if (!board.removeStone(lastMove.pos)) {
                cout << "Ошибка при удалении камня\n";
                return false;
            }
            cout << "Удален камень с позиции (" << lastMove.pos.x + 1 << "," 
                 << lastMove.pos.y + 1 << ")\n";
        } else {
            cout << "Отменен пас\n";
        }
        
        moveHistory.pop_back();
        SGFGame newSgf(board.getSize());
        // newSgf.setPlayerNames("хз", "хз");
        
        // Перекопируем все ходы кроме последнего
        for (size_t i = 0; i < moveHistory.size(); ++i) {
            newSgf.addMove(moveHistory[i]);
        }
        sgf = newSgf;
        moveNumber--;
        currentPlayer = lastMove.color;
        
        if (lastMove.isPass) {
            passes--;
            if (passes < 0) passes = 0;
        }
        
        cout << "Ход отменен. Текущий игрок: " 
             << (currentPlayer == Color::Black ? "Черные" : "Белые") << "\n";
        
        // saveGame("temp_undo.sgf");
        
        return true;
    }
    
    string getSGF() const {
        return sgf.generateSGF();
    }
    
    bool saveGame(const string& filename) const {
        return sgf.saveToFile(filename);
    }
    
    void sendToFile() {
        string sgfContent = getSGF();
        
        // Можно сохранить во временный файл
        ofstream temp("temp_game.sgf");
        temp << sgfContent;
        temp.close();
        
        cout << "Игра сохранена в temp_game.sgf для GnuGo\n";
    }
    
    void makeMove_console() {// пусть пока останется для тестов
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
            
            x--; y--;
            Position p{x, y};
            
            if (board.addStone(p, currentPlayer)) {
                recordMove(x, y, false);
                passes = 0;
                currentPlayer = (currentPlayer == Color::Black) ? Color::White : Color::Black;
                break;
            } else {
                cout << "Недопустимый ход!\n";
            }
        }
    }
    void showScore(){}// через питон
    
    void loop() {
        while (!gameOver) {
            board.simple_print();
            cout << "Ход #" << moveNumber << ": " 
                 << (currentPlayer == Color::Black ? "Черные" : "Белые") << "\n";
            makeMove_console();
        }
    }
};
int main(){// тоже наверно через питон
    Game game;
    game.loop();
    return 0;
}