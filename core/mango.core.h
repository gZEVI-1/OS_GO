#include <vector>
#include <queue>
#include <set>
#include <iostream>
using namespace std;

enum class Color {
    None, Black, White 
};
inline std::ostream& operator<<(std::ostream& os, const Color& color) {
    switch (color) {
    case Color::None:
        os << "0";
        break;
    case Color::Black:
        os << "2";  // или "X" или "B"
        break;
    case Color::White:
        os << "1";  // или "O" или "W"
        break;
    }
    return os;
}

struct Position {
    int x;
    int y;

    bool operator==(const Position& other) const { return (x == other.x && y == other.y); }
    bool operator!=(const Position& other) const { return !(*this == other); }
    bool operator<(const Position& other) const {
        if (x != other.x) return x < other.x;
        return y < other.y;
    }
};

class Group {
public:
    Color color;
    vector<Position> stones;
    set<Position> liberties;

    Group(Color c = Color::None) : color(c) {}
};

class Board {
private:
    vector<vector<Color>> grid;
    vector<Group> groups;
    int size;

    void updateGroups() {
        groups.clear();
        set<Position> visited;

        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                Position pos{ x, y };
                if (getStoneColor(pos) != Color::None && visited.find(pos) == visited.end()) {
                    Group newGroup = findGroup(pos);
                    for (const auto& stone : newGroup.stones) {
                        visited.insert(stone);
                    }
                    groups.push_back(newGroup);
                }
            }
        }
    }

    Group findGroup(Position sP) const {
        Group group;
        Color targetColor = getStoneColor(sP);

        if (targetColor == Color::None) return group;

        group.color = targetColor;
        queue<Position> toVisit;
        set<Position> visited;

        toVisit.push(sP);
        visited.insert(sP);

        while (!toVisit.empty()) {
            Position cur = toVisit.front();
            toVisit.pop();

            group.stones.push_back(cur);

            for (Position neighbor : getNeighbors(cur)) {
                if (getStoneColor(neighbor) == targetColor && visited.find(neighbor) == visited.end()) {
                    toVisit.push(neighbor);
                    visited.insert(neighbor);
                }
                else if (getStoneColor(neighbor) == Color::None) {
                    group.liberties.insert(neighbor);
                }
            }
        }
        return group;
    }

public:
    Board(int size) : size(size) {
        grid.resize(size, vector<Color>(size, Color::None));
    }

    Color getStoneColor(Position p) const {
        if (!isInBounds(p)) return Color::None;
        return grid[p.y][p.x];
    }

    vector<Position> getNeighbors(Position p) const {
        vector<Position> neighbors;

        Position directions[4] = {
            {p.x - 1, p.y},
            {p.x + 1, p.y},
            {p.x, p.y - 1},
            {p.x, p.y + 1}
        };

        for (const auto& neighbor : directions) {
            if (isInBounds(neighbor)) {
                neighbors.push_back(neighbor);
            }
        }
        return neighbors;
    }

    bool isInBounds(Position p) const {
        return (p.x >= 0 && p.x < size && p.y >= 0 && p.y < size);
    }

    bool isEmpty(Position p) const {
        return isInBounds(p) && getStoneColor(p) == Color::None;
    }

    bool placeStone(Position p, Color color) {
        if (!isInBounds(p) || !isEmpty(p)) return false;

        grid[p.y][p.x] = color;
        updateGroups();
        return true;
    }

    void removeStone(Position p) {
        if (isInBounds(p)) {
            grid[p.y][p.x] = Color::None;
            updateGroups();
        }
    }

    void clear() {
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                grid[i][j] = Color::None;
            }
        }
        groups.clear();
    }

    int getSize() const { return size; }

    const vector<Group>& getAllGroups() const {
        return groups;
    }


    const Group* getGroupAt(Position p) const {
        Color color = getStoneColor(p);
        if (color == Color::None) return nullptr;

        for (const auto& group : groups) {
            for (Position stone : group.stones) {
                if (stone.x == p.x && stone.y == p.y) {
                    return &group;
                }
            }
        }
        return nullptr;
    }
    void print() {
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                cout << grid[i][j];
            }
            cout << '\n';
        }
    }
};