// bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include <pybind11/stl_bind.h>

#include "Board_new.h"
#include "core.h"
#include "KataGoAnalyzer.h"

#ifndef PROJECT_VERSION
#define PROJECT_VERSION "1.1.7"
#endif

namespace py = pybind11;

//конвертации KataGoResult в Python dict
py::dict kataGoResultToDict(const KataGoResult& result) {
    py::dict d;
    d["success"] = result.success;
    d["winrate"] = result.winrate;
    d["score_lead"] = result.scoreLead;
    d["winner"] = result.winner;
    d["black_score"] = result.blackScore;
    d["white_score"] = result.whiteScore;
    d["komi"] = result.komi;
    d["best_move"] = result.bestMove;
    d["top_moves"] = result.topMoves;
    d["ownership"] = result.ownership;
    d["visits"] = result.visits;
    d["error_message"] = result.errorMessage;
    return d;
}

PYBIND11_MODULE(go_engine, m) {
    m.doc() = "Go game engine with SGF support and KataGo analysis";
    m.attr("__version__") = PROJECT_VERSION;
    
    py::enum_<Color>(m, "Color")
        .value("None", Color::None)
        .value("Black", Color::Black)
        .value("White", Color::White);
    
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
        
        .def("get_board_array", py::overload_cast<>(&Board::getBoardArray, py::const_))
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

    // SGFParser class
    py::class_<SGFParser>(m, "SGFParser")
        .def_static("parse_file", &SGFParser::parseFile)
        .def_static("parse_string", &SGFParser::parseString)
        .def_static("load_game", &SGFParser::loadGame);
    
    // Game class
    py::class_<Game>(m, "Game")
        .def(py::init<int>(), py::arg("size") = 9)
        .def("is_ok", &Game::isOk, py::arg("pos"), py::arg("board"), py::arg("player_color"))
        .def("re_pos_moves", &Game::rePosMoves, py::arg("rele_board"), py::arg("player_color"))
        .def("get_legal_moves", &Game::getLegalMoves, py::return_value_policy::reference)
        .def("record_move", &Game::recordMove, py::arg("x"), py::arg("y"), py::arg("is_pass") = false)
        .def("undo_last_move", &Game::undoLastMove)
        .def("get_sgf", &Game::getSGF)
        .def("save_game", [](Game& self, const std::string& filepath) {
                return self.saveGame(filepath);
            }, py::arg("filepath"), "Сохраняет игру в SGF файл по указанному пути (создаёт директории при необходимости)")        
        .def("make_move", &Game::makeMove, py::arg("x"), py::arg("y"), py::arg("is_pass") = false, "Делает ход. Возвращает True если ход принят, False если отклонён")
        .def("is_game_over", &Game::isGameOver)
        .def("get_current_player", &Game::getCurrentPlayer)
        .def("get_move_number", &Game::getMoveNumber)
        .def("get_passes", &Game::getPasses)
        .def("get_board", py::overload_cast<>(&Game::getBoard), py::return_value_policy::reference)
        .def("get_board_const", py::overload_cast<>(&Game::getBoard, py::const_))
        .def("reset", &Game::reset, py::arg("newSize") = 9)
        .def("load_from_sgf", &Game::loadFromSGF);

    // Структура конфигурации KataGo
    py::class_<KataGoConfig>(m, "KataGoConfig")
        .def(py::init<>())
        .def_readwrite("katago_path", &KataGoConfig::katagoPath)
        .def_readwrite("model_path", &KataGoConfig::modelPath)
        .def_readwrite("config_path", &KataGoConfig::configPath)
        .def_readwrite("max_visits", &KataGoConfig::maxVisits)
        .def_readwrite("max_time", &KataGoConfig::maxTime)
        .def_readwrite("komi", &KataGoConfig::komi)
        .def_readwrite("board_size", &KataGoConfig::boardSize)
        .def_readwrite("log_to_stdout", &KataGoConfig::logToStdout)
        .def_readwrite("analysis_mode", &KataGoConfig::analysisMode)
        .def("__repr__", [](const KataGoConfig& cfg) {
            return "<KataGoConfig(katago_path='" + cfg.katagoPath + 
                   "', model_path='" + cfg.modelPath + 
                   "', max_visits=" + std::to_string(cfg.maxVisits) + 
                   ", board_size=" + std::to_string(cfg.boardSize) + ")>";
        });
    
    // Результат анализа (будет возвращаться как dict, но можно и как объект)
    py::class_<KataGoResult>(m, "KataGoResult")
        .def(py::init<>())
        .def_readwrite("winrate", &KataGoResult::winrate)
        .def_readwrite("score_lead", &KataGoResult::scoreLead)
        .def_readwrite("winner", &KataGoResult::winner)
        .def_readwrite("black_score", &KataGoResult::blackScore)
        .def_readwrite("white_score", &KataGoResult::whiteScore)
        .def_readwrite("komi", &KataGoResult::komi)
        .def_readwrite("best_move", &KataGoResult::bestMove)
        .def_readwrite("top_moves", &KataGoResult::topMoves)
        .def_readwrite("ownership", &KataGoResult::ownership)
        .def_readwrite("visits", &KataGoResult::visits)
        .def_readwrite("success", &KataGoResult::success)
        .def_readwrite("error_message", &KataGoResult::errorMessage)
        .def("to_dict", &kataGoResultToDict)
        .def("__repr__", [](const KataGoResult& res) {
            if (res.success) {
                return "<KataGoResult(winner='" + res.winner + 
                       "', score_lead=" + std::to_string(res.scoreLead) + 
                       ", best_move='" + res.bestMove + "')>";
            } else {
                return "<KataGoResult(success=false, error='" + res.errorMessage + "')>";
            }
        });
    
    // Основной класс анализатора
    py::class_<KataGoAnalyzer>(m, "KataGoAnalyzer")
        .def(py::init<>())
        .def("initialize", 
            py::overload_cast<const KataGoConfig&>(&KataGoAnalyzer::initialize),
            py::arg("config"),
            "Инициализирует KataGo с конфигурацией")
        .def("initialize",
            py::overload_cast<const std::string&, const std::string&, const std::string&>(&KataGoAnalyzer::initialize),
            py::arg("katago_path"), py::arg("model_path"), py::arg("config_path") = "",
            "Инициализирует KataGo с путями к файлам")
        .def("analyze_sgf", 
            py::overload_cast<const std::string&>(&KataGoAnalyzer::analyzeSGF),
            py::arg("sgf_content"),
            "Анализирует SGF файл и возвращает результат партии")
        .def("analyze_sgf",
            py::overload_cast<const std::string&, int, double>(&KataGoAnalyzer::analyzeSGF),
            py::arg("sgf_content"), py::arg("board_size"), py::arg("komi"),
            "Анализирует SGF файл с указанным размером доски и коми")
        .def("analyze_position",
            py::overload_cast<const std::vector<std::string>&>(&KataGoAnalyzer::analyzePosition),
            py::arg("moves"),
            "Анализирует позицию по списку ходов")
        .def("analyze_position",
            py::overload_cast<const std::vector<std::string>&, int, double, int>(&KataGoAnalyzer::analyzePosition),
            py::arg("moves"), py::arg("board_size"), py::arg("komi"), py::arg("max_visits"),
            "Анализирует позицию с указанными параметрами")
        .def("load_sgf", &KataGoAnalyzer::loadSGF,
            py::arg("sgf_content"),
            "Загружает SGF в KataGo без анализа")
        .def("send_gtp_command", &KataGoAnalyzer::sendGTPCommand,
            py::arg("command"),
            "Отправляет произвольную GTP команду")
        .def("clear_board", &KataGoAnalyzer::clearBoard,
            "Очищает доску в KataGo")
        .def("shutdown", &KataGoAnalyzer::shutdown,
            "Завершает работу KataGo")
        .def("is_available", &KataGoAnalyzer::isAvailable,
            py::arg("katago_path"),
            "Статический метод: проверяет доступность KataGo по пути")
        .def("__enter__", [](KataGoAnalyzer& self) -> KataGoAnalyzer& { return self; },
            "Поддержка контекстного менеджера")
        .def("__exit__", [](KataGoAnalyzer& self, py::object, py::object, py::object) {
            self.shutdown();
        }, "Автоматический вызов shutdown при выходе из контекста");
    
    // // Утилитарные функции для работы с KataGo
    // m.def("get_winner_katago", [](const std::string& sgf_content, int board_size = 19) -> int {
    //     KataGoAnalyzer analyzer;
    //     // Пути нужно настроить или передавать
    //     return -1;  // Заглушка - нужно реализовать
    // }, "Определяет победителя через KataGo (требует настройки путей)");
    
    // m.def("get_score_katago", [](const std::string& sgf_content, int board_size = 19) -> py::dict {
    //     KataGoAnalyzer analyzer;
    //     // Заглушка
    //     py::dict result;
    //     result["black"] = 0.0;
    //     result["white"] = 0.0;
    //     result["diff"] = 0.0;
    //     result["komi"] = 6.5;
    //     return result;
    // }, "Подсчитывает очки через KataGo (требует настройки путей)");
    
    // Utility functions
    m.def("get_opponent_color", &getOpponentColor);
}