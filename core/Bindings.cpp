// bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>

#include "Board_new.h"
#include "core.h"

namespace py = pybind11;

PYBIND11_MODULE(go_engine, m) {
    m.doc() = "Go game engine with SGF support";
    
    // Color enum
    // py::enum_<Color>(m, "Color")
    //     .value("None", Color::None)
    //     .value("Black", Color::Black)
    //     .value("White", Color::White);
    
    // Position struct
    py::class_<Position>(m, "Position")
        .def(py::init<>())
        .def(py::init<int, int>())
        .def_readwrite("x", &Position::x)
        .def_readwrite("y", &Position::y)
        .def("__eq__", &Position::operator==)
        .def("__ne__", &Position::operator!=)
        .def("__lt__", &Position::operator<)
        .def("__repr__", [](const Position& p) {
            return "<Position(" + std::to_string(p.x) + ", " + std::to_string(p.y) + ")>";
        });
    
    // Group class
    py::class_<Group>(m, "Group")
        .def(py::init<>())
        .def(py::init<Color>())
        .def_readwrite("color", &Group::color)
        .def_readwrite("stones", &Group::stones)
        .def_readwrite("liberties", &Group::liberties)
        .def("contains", &Group::contains)
        .def("add_stone", &Group::addStone)
        .def("remove_stone", &Group::removeStone)
        .def("empty", &Group::empty);
    
    // Board class
    py::class_<Board>(m, "Board")
        .def(py::init<int>())
        .def("get_size", &Board::getSize)
        .def("get_color", py::overload_cast<const Position&>(&Board::getColor, py::const_))
        .def("get_color", py::overload_cast<int, int>(&Board::get_color, py::const_))
        .def("add_stone", py::overload_cast<const Position&, Color>(&Board::addStone))
        .def("add_stone", py::overload_cast<int, int, Color>(&Board::add_stone))
        .def("remove_stone", py::overload_cast<const Position&>(&Board::removeStone))
        .def("remove_stone", py::overload_cast<int, int>(&Board::remove_stone))
        .def("simple_print", &Board::simple_print)
        .def("find_group_index", &Board::findGroupIndex);
    
    // Move struct
    py::class_<Move>(m, "Move")
        .def(py::init<>())
        .def(py::init<int, int, Color, int>())
        .def(py::init<Color, int>())
        .def_readwrite("pos", &Move::pos)
        .def_readwrite("color", &Move::color)
        .def_readwrite("move_number", &Move::moveNumber)
        .def_readwrite("is_pass", &Move::isPass);
    
    // SGFGame class
    py::class_<SGFGame>(m, "SGFGame")
        .def(py::init<>())
        .def(py::init<int>())
        .def("add_move", &SGFGame::addMove)
        .def("set_player_names", &SGFGame::setPlayerNames)
        .def("set_result", &SGFGame::setResult)
        .def("pos_to_sgf", &SGFGame::posToSGF)
        .def("generate_sgf", &SGFGame::generateSGF)
        .def("save_to_file", &SGFGame::saveToFile)
        .def("get_moves", &SGFGame::getMoves)
        .def("clear", &SGFGame::clear);
    
    // Game class
    py::class_<Game>(m, "Game")
        .def(py::init<int>(), py::arg("size") = 9)
        .def("record_move", &Game::recordMove, py::arg("x"), py::arg("y"), py::arg("is_pass") = false)
        .def("undo_last_move", &Game::undoLastMove)
        .def("get_sgf", &Game::getSGF)
        .def("save_game", &Game::saveGame)
        .def("make_move", &Game::makeMove, py::arg("x"), py::arg("y"), py::arg("is_pass") = false)
        .def("is_game_over", &Game::isGameOver)
        .def("get_current_player", &Game::getCurrentPlayer)
        .def("get_move_number", &Game::getMoveNumber)
        .def("get_passes", &Game::getPasses)
        .def("get_board", py::overload_cast<>(&Game::getBoard), py::return_value_policy::reference)
        .def("get_board_const", py::overload_cast<>(&Game::getBoard, py::const_));
    
    // Utility functions
    m.def("get_opponent_color", &getOpponentColor);
}