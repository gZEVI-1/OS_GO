// Board_new.h
#pragma once
#include <vector>
#include <queue>
#include <set>
#include <iostream>
#include <algorithm>

enum class Color
{
    None,
    Black,
    White
};

inline Color getOpponentColor(Color c)
{
    if (c == Color::White) return Color::Black;
    if (c == Color::Black) return Color::White;
    return Color::None;
}

inline std::ostream &operator<<(std::ostream &os, const Color &color)
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
    std::vector<Position> stones;
    std::set<Position> liberties;

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
            std::remove_if(stones.begin(), stones.end(),
                      [&](const Position &p)
                      { return p.x == x && p.y == y; }),
            stones.end());
    }

    bool empty() const { return stones.empty(); }
};

class Board
{
private:
    std::vector<std::vector<Color>> grid;
    std::vector<Group> groups;
    int size;

    Position koPoint;
    bool hasKo;

    bool inBounds(const Position &p) const
    {
        return p.x >= 0 && p.x < size && p.y >= 0 && p.y < size;
    }

    std::vector<Position> neighbors(const Position &p) const
    {
        static const int dx[4] = {1, -1, 0, 0};
        static const int dy[4] = {0, 0, 1, -1};
        std::vector<Position> res;
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
        std::set<Position> stoneSet(g.stones.begin(), g.stones.end());
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

public:
    Board(int n)
        : grid(n, std::vector<Color>(n, Color::None)),
          size(n),
          koPoint{-1, -1},
          hasKo(false)
    {
    }

    int getSize() const { return size; }

    Color getColor(const Position &p) const
    {
        if (inBounds(p))
            return grid[p.x][p.y];
        return Color::None;
    }

    Color get_color(int x, int y) const {
        return inBounds({x, y}) ? grid[x][y] : Color::None;
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

    bool addStone(const Position &p, Color c)
    {
        if (!inBounds(p))
            return false;
        if (grid[p.x][p.y] != Color::None)
            return false;

        if (hasKo && p.x == koPoint.x && p.y == koPoint.y)
            return false;

        auto oldGrid = grid;
        auto oldGroups = groups;
        Position oldKoPoint = koPoint;
        bool oldHasKo = hasKo;

        hasKo = false;
        koPoint = {-1, -1};

        grid[p.x][p.y] = c;

        std::vector<int> sameColorGroupIdx;
        std::set<int> viewed;
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

        Group newGroup(c);
        newGroup.stones.push_back(p);
        for (auto &n : neighbors(p))
        {
            if (grid[n.x][n.y] == Color::None)
            {
                newGroup.liberties.insert(n);
            }
        }

        for (int gi : sameColorGroupIdx)
        {
            Group &g = groups[gi];
            newGroup.stones.insert(newGroup.stones.end(),
                                   g.stones.begin(), g.stones.end());
        }

        std::sort(sameColorGroupIdx.begin(), sameColorGroupIdx.end());
        for (int i = (int)sameColorGroupIdx.size() - 1; i >= 0; --i)
        {
            groups.erase(groups.begin() + sameColorGroupIdx[i]);
        }

        countLiberties(newGroup);
        groups.push_back(newGroup);

        Color opp = getOpponentColor(c);
        std::vector<int> oppGroupsToCheck;
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

        int capturedStones = 0;
        Position singleCaptured{-1, -1};

        std::sort(oppGroupsToCheck.begin(), oppGroupsToCheck.end());
        for (int idx = (int)oppGroupsToCheck.size() - 1; idx >= 0; --idx)
        {
            int gi = oppGroupsToCheck[idx];
            if (gi < 0 || gi >= (int)groups.size())
                continue;
            Group &g = groups[gi];
            if (g.color != opp)
                continue;

            countLiberties(g);
            if (g.liberties.empty())
            {
                capturedStones += (int)g.stones.size();
                if (g.stones.size() == 1)
                {
                    singleCaptured = g.stones[0];
                }

                for (auto &s : g.stones)
                {
                    grid[s.x][s.y] = Color::None;
                }
                groups.erase(groups.begin() + gi);
            }
        }

        if (capturedStones == 1)
        {
            int myGroupIdx = findGroupIndex(p);
            if (myGroupIdx >= 0)
            {
                Group &myGroup = groups[myGroupIdx];
                if (myGroup.stones.size() == 1)
                {
                    hasKo = true;
                    koPoint = singleCaptured;
                }
            }
        }

        int myGroupIdx2 = findGroupIndex(p);
        if (myGroupIdx2 >= 0)
        {
            Group &g = groups[myGroupIdx2];
            countLiberties(g);
            if (g.liberties.empty())
            {
                grid = oldGrid;
                groups = oldGroups;
                koPoint = oldKoPoint;
                hasKo = oldHasKo;
                return false;
            }
        }

        return true;
    }

    bool add_stone(int x, int y, Color c) { return addStone({x,y}, c); }

    bool removeStone(const Position &p)
    {
        if (!inBounds(p))
            return false;
        if (grid[p.x][p.y] == Color::None)
            return false;

        grid[p.x][p.y] = Color::None;

        int gi = findGroupIndex(p);
        if (gi >= 0)
        {
            Group &g = groups[gi];
            auto it = std::remove(g.stones.begin(), g.stones.end(), p);
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

        hasKo = false;
        koPoint = {-1, -1};

        return true;
    }

    bool remove_stone(int x, int y) { return removeStone({x,y}); }

    void simple_print() const
    {
        std::cout << "  ";
        for (int x = 0; x < size; ++x)
            std::cout << x + 1 << " ";
        std::cout << "\n";
        for (int y = 0; y < size; ++y)
        {
            std::cout << y + 1 << " ";
            for (int x = 0; x < size; ++x)
            {
                std::cout << grid[x][y] << " ";
            }
            std::cout << "\n";
        }
    }
};