#include <vector>
#include <queue>
#include <set>
#include "../../mango.core/mango.core/mango.core.h"

using namespace std;
class Game {
private:
	Board board;
	Color curPlayer;
	int blackTerritory = 0;
	int whiteTerritory = 0;
	Position lastMove;
	bool gameOver;
public:
	Color getOpponentColor(Color c) {
		if (c == Color::White) return Color::Black;
		if (c == Color::Black) return Color::White;
		return Color::None;
	}

	bool wouldCaptureOp(Position p, Color color) {
		for (Position neighbor : board.getNeighbors(p)) {
			if (board.getStoneColor(neighbor) == getOpponentColor(color)) {
				 const Group* opponentGroup = board.getGroupAt(neighbor);
				if (opponentGroup && opponentGroup->liberties.size() == 1) {
					if (opponentGroup->liberties.find(p) != opponentGroup->liberties.end()) {
						return true;
					}
				}
			}
		}
		return false;
	}
	
	bool hasLibertiesAfterMove(Position p, Color color) {
		for (Position neighbor : board.getNeighbors(p)) {
			if (board.getStoneColor(neighbor) == Color::None) {
				return true;
			}
		}

		for (Position neighbor : board.getNeighbors(p)) {
			if (board.getStoneColor(neighbor) == color) {
				const Group* friendlyGroup = board.getGroupAt(neighbor);
				for (Position lib : friendlyGroup->liberties) {
					if (!(lib.x == p.x && lib.y == p.y)) {
						return true;
					}
				}
			}
		}
		return false;
	}

	bool isSuicide(Position p, Color color) {
		if (wouldCaptureOp(p, color)) {
			return false;
		}
		return !hasLibertiesAfterMove(p, color);
	}

	int captureGroups(Position p, Color color) {
		int captured = 0;
		vector<Position> toRemove;

		for (Position neighbor : board.getNeighbors(p)) {
			Color neighborColor = board.getStoneColor(neighbor);
			if (neighborColor == getOpponentColor(color)) {
				const Group* opponentGroup = board.getGroupAt(neighbor);
				if (opponentGroup && board.getStoneColor(neighbor) != Color::None) {
					if (opponentGroup->liberties.size() == 1 &&
						opponentGroup->liberties.find(p) != opponentGroup->liberties.end()) {
						for (Position stone : opponentGroup->stones) {
							toRemove.push_back(stone);
							captured++;
						}
					}
				}
			}
		}

		for (Position pos : toRemove) {
			board.removeStone(pos);
		}

		return captured;
	}
	bool makeMove(Position p) {
		if (gameOver) return false;
		if (!board.isEmpty(p)) return false;

		if (isSuicide(p, curPlayer)) {
			return false;
		}

		int captured = captureGroups(p, curPlayer);

		if (curPlayer == Color::Black) {
			blackTerritory += captured;
		}
		else {
			whiteTerritory += captured;
		}
		lastMove = p;
		curPlayer = getOpponentColor(curPlayer);
		return true;

	}

	bool pass() {
		if (gameOver) return false;
		curPlayer = getOpponentColor(curPlayer);
		return true;
	}
	void endGame() {
		gameOver = true;
	 }
	const Board& getBoard() const { return board; }
	Color getCurrentPlayer() const { return curPlayer; }
	int getBlackTerritory() const { return blackTerritory; }
	int getWhiteTerritory() const { return whiteTerritory; }
	Position getLastMove() const { return lastMove; }
	bool isGameOver() const { return gameOver; }
};