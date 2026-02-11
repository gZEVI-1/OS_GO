#include <vector>
#include <queue>
#include <set>
using namespace std;
enum class Color {
	None, Black, White
};

struct Position {
	int x;
	int y;

	bool operator==(const Position& other) const { return (x == other.x && y == other.y); }
	bool operator!=(const Position& other) const { return !(*this == other); }
};

class Group {
public: 
	vector<Position> stones;
	set<Position> liberties;
 };

 
class Board {
private:
	vector<vector<Color>> grid;
	int blackTer = 0;
	int whiteTer = 0;
	int size;
public:
	Board(int size) {
		this->size = size;
		for (int i = 0; i < size; i++) {
			for (int j = 0; j < size; j++) {
				grid[i][j] = Color::None;
			}
		}
	}
	Color getStoneColor(Position p) const {
		return grid[p.y][p.x];
	}
	Color getOpponentColor(Color c) {
		if (c != Color::None) {
			return (c == Color::White) ? Color::Black : Color::White;
		}
	}
	vector<Position>& getNeighbors(Position p) const {
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

	Group findGroup(Position sP) const {
		Group group;
		Color targetColor = getStoneColor(sP);

		if (targetColor == Color::None) return group;

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
	bool isInBounds(Position p) const {
		return (p.x <= size && p.y <= size);
	}
	bool isEmpty(Position p) const;

	int countLib(Position p) const {
		int lib = 0;
		for (Position nbr : getNeighbors(p)) {
			if (getStoneColor(nbr) == Color::None) {
				lib++;
			}
		}
		return lib;
	}
	bool putStone(Color color, Position p) {
		if (!isInBounds(p) || !isEmpty(p)) return false;
		grid[p.y][p.x] = color;

		bool capOp = false;
		vector<Position> neighbors = getNeighbors(p);
		for (Position sp : neighbors) {
			if (getStoneColor(sp) == getOpponentColor(color)) {
				Group opGroup = findGroup(sp);
				if (opGroup.liberties.empty()) {
					for (Position pos : opGroup.stones) {
						removeStone(pos);
						if (color == Color::Black) {
							blackTer++;
						}
						else if (color == Color::White) {
							whiteTer++;
						}
					}
					capOp = true;
				}
			}
		}

		Group myGroup = findGroup(p);
		if (myGroup.liberties.empty() && !capOp) {
			grid[p.y][p.x] = Color::None;
			return false;
		}
		// ко при помощи хэширования Зобриста

	}

	void removeStone(Position p) {
		if (isInBounds) grid[p.y][p.x] = Color::None;
	}
	void clear(){
		for (int i = 0; i < size; i++) {
			for (int j = 0; j < size; j++) {
				grid[i][j] = Color::None;
			}
		}
	}
	int getSize() const { return size; }

	void print() const;
};