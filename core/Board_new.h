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
        os << "B"; // или "X" или "B"
        break;
    case Color::White:
        os << "W"; // или "O" или "W"
        break;
    }
    return os;
}

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
