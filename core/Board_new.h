#include <vector>
#include <queue>
#include <set>
#include <iostream>
#include <algorithm>
using namespace std;

enum class Color
{
    None,
    Black,
    White
};
inline ostream &operator<<(ostream &os, const Color &color)
{
    switch (color)
    {
    case Color::None:
        os << "+";
        break;
    case Color::Black:
        os << "B";
        break;
    case Color::White:
        os << "W";
        break;
    }
    return os;
}

//УБРАТЬ ВСЕ НЕНУЖНОЕ, ОСТАВИТЬ ПРОВЕРКУ НА КОРРЕКТНОСТЬ И ЗАПИСЬ ДОСКИ

struct Position
{
    int x;
    int y;

    bool operator==(const Position &other) const { return (x == other.x && y == other.y); }
    bool operator!=(const Position &other) const { return !(*this == other); }
    bool operator<(const Position &other) const
    {
        if (x != other.x)
            return x < other.x;
        return y < other.y;
    }
};

class Group
{
public:
    Color color;
    vector<Position> stones;
    set<Position> liberties;
    Group(Color c = Color::None) : color(c) {}

    bool contains(int x, int y) const
    {
        for (auto &p : stones)
            if (p.x == x && p.y == y)
                return true;
        return false;
    }

    void addStone(int x, int y)
    {
        stones.push_back({x, y});
    }

    void removeStone(int x, int y)
    {
        stones.erase(
            remove_if(stones.begin(), stones.end(),
                      [&](const Position &p)
                      { return p.x == x && p.y == y; }),
            stones.end());
    }

    bool empty() const { return stones.empty(); }
};

class Board
{
private:
    vector<vector<Color>> grid;
    vector<Group> groups;
    int size;

    bool inBounds(const Position &p) const
    {
        return p.x >= 0 && p.x < size && p.y >= 0 && p.y < size;
    }

    vector<Position> neighbors(const Position &p) const
    {
        static const int dx[4] = {1, -1, 0, 0};
        static const int dy[4] = {0, 0, 1, -1};
        vector<Position> res;
        for (int k = 0; k < 4; ++k)
        {
            Position q{p.x + dx[k], p.y + dy[k]};
            if (inBounds(q))
                res.push_back(q);
        }
        return res;
    }

    void countLiberties(Group &g)
    {
        g.liberties.clear();
        set<Position> stoneSet(g.stones.begin(), g.stones.end());
        for (const auto &s : g.stones)
        {
            for (auto &n : neighbors(s))
            {
                if (grid[n.x][n.y] == Color::None &&
                    stoneSet.find(n) == stoneSet.end())
                {
                    g.liberties.insert(n);
                }
            }
        }
    }

    int findGroupIndex(const Position &p) const
    {
        for (int i = 0; i < (int)groups.size(); ++i)
        {
            for (auto &s : groups[i].stones)
            {
                if (s == p)
                    return i;
            }
        }
        return -1;
    }

public:
    Board(int n) : size(n), grid(n, vector<Color>(n, Color::None)) {}

     Color getColor(const Position& p) const {
        if (inBounds(p)) {
            return grid[p.x][p.y];
        }
        return Color::None;
    }

    bool addStone(const Position &p, Color c)
    {
        if (!inBounds(p))
            return false;
        if (grid[p.x][p.y] != Color::None)
            return false;

        grid[p.x][p.y] = c;

        // поиск групп того же цвета
        vector<int> sameColorGroupIdx;
        set<int> viewed;
        for (auto &n : neighbors(p))
        {
            if (grid[n.x][n.y] == c)
            {
                int gi = findGroupIndex(n);
                if (gi >= 0 && !viewed.count(gi))
                {
                    sameColorGroupIdx.push_back(gi);
                    viewed.insert(gi);
                }
            }
        }

        // делаем новую группу из одного камня
        Group newGroup(c);
        newGroup.stones.push_back(p);
        for (auto &n : neighbors(p))
        {
            if (grid[n.x][n.y] == Color::None)
            {
                newGroup.liberties.insert(n);
            }
        }

        // сливаем соседними группами того же цвета
        for (int gi : sameColorGroupIdx)
        {
            Group &g = groups[gi];
            newGroup.stones.insert(newGroup.stones.end(),
                                   g.stones.begin(), g.stones.end());
        }
        // удаляем слитые группы
        sort(sameColorGroupIdx.begin(), sameColorGroupIdx.end());
        for (int i = (int)sameColorGroupIdx.size() - 1; i >= 0; --i)
        {
            groups.erase(groups.begin() + sameColorGroupIdx[i]);
        }

        // пересчет свобод объединённой группы
        countLiberties(newGroup);
        groups.push_back(newGroup);

        // обновление свобод соседних групп противоположного цвета
        Color opp = (c == Color::Black ? Color::White : c == Color::White ? Color::Black
                                                                          : Color::None);

        vector<int> oppGroupsToCheck;
        viewed.clear();
        for (auto &n : neighbors(p))
        {
            if (grid[n.x][n.y] == opp)
            {
                int gi = findGroupIndex(n);
                if (gi >= 0 && !viewed.count(gi))
                {
                    oppGroupsToCheck.push_back(gi);
                    viewed.insert(gi);
                }
            }
        }

        // для каждой вражеской группы пересчитать свободы
        //  и если нет свобод — снять её с доски
        sort(oppGroupsToCheck.begin(), oppGroupsToCheck.end());
        for (int idx = (int)oppGroupsToCheck.size() - 1; idx >= 0; --idx)
        {

            int gi = oppGroupsToCheck[idx];
            Group &g = groups[gi];

            // доп защита
            if (gi >= (int)groups.size())
                continue; //
            if (g.color != opp)
                continue; //
            //

            countLiberties(g);
            if (g.liberties.empty())
            {

                for (auto &s : g.stones)
                {
                    grid[s.x][s.y] = Color::None;
                }
                groups.erase(groups.begin() + gi);
            }
        }

        // проверка на самоубийство
        int myGroupIdx = findGroupIndex(p);
        if (myGroupIdx >= 0)
        {
            Group &g = groups[myGroupIdx];
            countLiberties(g);
            if (g.liberties.empty())
            {

                for (auto &s : g.stones)
                {
                    grid[s.x][s.y] = Color::None;
                }
                groups.erase(groups.begin() + myGroupIdx);
                return false;
            }
        }

        return true;
    }

    bool removeStone(const Position &p)
    {
        if (!inBounds(p))
            return false;
        if (grid[p.x][p.y] == Color::None)
            return false;

        Color c = grid[p.x][p.y];
        grid[p.x][p.y] = Color::None;

        int gi = findGroupIndex(p);
        if (gi >= 0)
        {
            Group &g = groups[gi];

            auto it = remove(g.stones.begin(), g.stones.end(), p);
            g.stones.erase(it, g.stones.end());

            if (g.stones.empty())
            {
                groups.erase(groups.begin() + gi);
            }
            else
            {
                countLiberties(g);
            }
        }

        // обновить свободы соседних групп
        for (auto &n : neighbors(p))
        {
            if (grid[n.x][n.y] == Color::None)
                continue;
            int gni = findGroupIndex(n);
            if (gni >= 0)
            {
                countLiberties(groups[gni]);
            }
        }

        return true;
    }


//УЖЕ НЕ НУЖНО, ( ЗАЛИВКУ ОСТАВИТЬ НА ВСЯКИЙ ) ПОДСЧЕТ ТЕРРИТОРИЙ И МЕРТВЫХ КАМНЕЙ МОЖНО СДЕЛАТЬ ЧЕРЕЗ GNU GO 
    // Метод 1: Простая заливка для получения списка территорий
    vector<vector<Position>> getTerritories() const {
        vector<vector<Position>> territories;
        vector<vector<bool>> visited(size, vector<bool>(size, false));
        
        for (int x = 0; x < size; ++x) {
            for (int y = 0; y < size; ++y) {
                // Если нашли пустую клетку
                if (grid[x][y] == Color::None && !visited[x][y]) {
                    vector<Position> territory;
                    queue<Position> q;
                    
                    q.push({x, y});
                    visited[x][y] = true;
                    
                    // Заливка
                    while (!q.empty()) {
                        Position current = q.front();
                        q.pop();
                        
                        territory.push_back(current);
                        
                        // Проверяем всех соседей
                        for (const Position& n : neighbors(current)) {
                            if (grid[n.x][n.y] == Color::None && !visited[n.x][n.y]) {
                                visited[n.x][n.y] = true;
                                q.push(n);
                            }
                        }
                    }
                    
                    territories.push_back(territory);
                }
            }
        }
        
        return territories;
    }

     pair<set<Position>, set<Position>> findDeadStones() const {
        set<Position> deadBlack;
        set<Position> deadWhite;
        
        // Проверяем каждую группу на доске
        for (const Group& group : groups) {
            if (!group.empty()) {
                bool isAlive = isGroupAlive(group);
                
                if (!isAlive) {
                    // Группа мертва, все ее камни считаются захваченными
                    for (const Position& stone : group.stones) {
                        if (group.color == Color::Black) {
                            deadBlack.insert(stone);
                        } else {
                            deadWhite.insert(stone);
                        }
                    }
                }
            }
        }
        
        return {deadBlack, deadWhite};
    }

    // Метод 2: Определение владельца территории
   Color getTerritoryOwner(const vector<Position>& territory, 
                                   const set<Position>& deadBlackStones,
                                   const set<Position>& deadWhiteStones) const {
        
        set<Color> surroundingColors;
        
        // Проверяем все соседние точки территории
        for (const Position& p : territory) {
            for (const Position& n : neighbors(p)) {
                if (grid[n.x][n.y] != Color::None) {
                    // Проверяем, жив ли камень, который окружает территорию
                    Color stoneColor = grid[n.x][n.y];
                    bool isStoneDead = (stoneColor == Color::Black && 
                                        deadBlackStones.count(n) > 0) ||
                                       (stoneColor == Color::White && 
                                        deadWhiteStones.count(n) > 0);
                    
                    // Если камень мертв, он не считается при определении территории
                    if (!isStoneDead) {
                        surroundingColors.insert(stoneColor);
                    }
                }
            }
        }
        
        // Территория принадлежит тому цвету, чьи живые камни ее окружают
        if (surroundingColors.size() == 1) {
            return *surroundingColors.begin();
        }
        
        return Color::None; // Нейтральная или спорная территория
    }
    
    // Проверка жива ли группа
     bool isGroupAlive(const Group& group) const {
        if (group.liberties.size() >= 2) {
            // Проверяем, являются ли свободы настоящими глазами
            int eyeCount = 0;
            set<Position> checkedLiberties;
            
            for (const Position& liberty : group.liberties) {
                if (isRealEye(liberty, group.color)) {
                    eyeCount++;
                }
            }
            
            // Если есть два настоящих глаза - группа точно жива
            if (eyeCount >= 2) return true;
            
            // Проверяем форму группы (может жить и без двух явных глаз)
            // return hasGoodShape(group);
        }
        
        return false; // Нет свобод или одна свобода (в атари)
    }
    
    bool isRealEye(const Position& p, Color groupColor) const {
        // Проверяем все соседние точки
        for (const Position& n : neighbors(p)) {
            if (grid[n.x][n.y] != groupColor && grid[n.x][n.y] != Color::None) {
                return false; // Есть камень противника рядом
            }
        }
        
        // Проверяем диагонали для предотвращения ложных глаз
        int diagonalCount = 0;
        int diagonalFriendly = 0;
        
        int dx[] = {-1, -1, 1, 1};
        int dy[] = {-1, 1, -1, 1};
        
        for (int i = 0; i < 4; ++i) {
            Position d{p.x + dx[i], p.y + dy[i]};
            if (inBounds(d)) {
                diagonalCount++;
                if (grid[d.x][d.y] == groupColor) {
                    diagonalFriendly++;
                }
            }
        }
        
        // В зависимости от позиции (центр/край/угол) проверяем диагонали
        if (neighbors(p).size() == 4) { // В центре
            return diagonalFriendly >= 3; // Нужны свои на 3 из 4 диагоналей
        } else if (neighbors(p).size() == 3) { // На краю
            return diagonalFriendly >= 2;
        } else { // В углу
            return diagonalFriendly >= 1;
        }
    }

    // ПОТОМ УБРАТЬ
    void simple_print() const
    {
        cout << "  ";
        for (int x = 0; x < size; ++x)
            cout << x + 1 << " ";
        cout << "\n";
        for (int y = 0; y < size; ++y)
        {
            cout << y + 1 << " ";
            for (int x = 0; x < size; ++x)
            {
                cout << grid[x][y] << " ";
            }
            cout << "\n";
        }
    }
};
