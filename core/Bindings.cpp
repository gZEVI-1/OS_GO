// bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include <pybind11/stl_bind.h>

#include "Board_new.h"
#include "core.h"
#include "KataGoAnalyzer.h"

#ifndef PROJECT_VERSION
#define PROJECT_VERSION "1.1.8"
#endif

namespace py = pybind11;

// Конвертация KataGoResult в Python dict
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
        .value("NONE", Color::None)
        .value("Black", Color::Black)
        .value("White", Color::White);
    
    // НОВОЕ: enum Rules — объявляем ДО использования
    py::enum_<Rules>(m, "Rules")
        .value("Chinese", Rules::Chinese)
        .value("Japanese", Rules::Japanese);
    
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
        .def("set_rules", &SGFGame::setRules)      // <-- НОВОЕ
        .def("get_rules", &SGFGame::getRules)      // <-- НОВОЕ
        .def("set_komi", &SGFGame::setKomi)        // <-- НОВОЕ
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
            }, py::arg("filepath"), "Save game to SGF file")
        .def("make_move", &Game::makeMove, py::arg("x"), py::arg("y"), py::arg("is_pass") = false)
        .def("is_game_over", &Game::isGameOver)
        .def("get_current_player", &Game::getCurrentPlayer)
        .def("get_move_number", &Game::getMoveNumber)
        .def("get_passes", &Game::getPasses)
        .def("get_board", py::overload_cast<>(&Game::getBoard), py::return_value_policy::reference)
        .def("get_board_const", py::overload_cast<>(&Game::getBoard, py::const_))
        .def("reset", &Game::reset, py::arg("newSize") = 9)
        .def("load_from_sgf", &Game::loadFromSGF)
        // НОВОЕ: правила и коми
        .def("set_rules", &Game::setRules, py::arg("rules"), "Set game rules (Chinese/Japanese)")
        .def("get_rules", &Game::getRules, "Get current game rules")
        .def("set_komi", &Game::setKomi, py::arg("komi"), "Set komi value")
        .def("get_komi", &Game::getKomi, "Get current komi value");
        
    // KataGoConfig struct
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
        .def_readwrite("rules", &KataGoConfig::rules, "Game rules: Rules.Chinese or Rules.Japanese");
    
    // KataGoResult struct
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
                       "', score_lead=" + std::to_string(res.scoreLead) + ")>";
            } else {
                return "<KataGoResult(success=false, error='" + res.errorMessage + "')>";
            }
        });
    
    // SGFInfo
    py::class_<SGFInfo>(m, "SGFInfo")
        .def(py::init<>())
        .def_readwrite("filename", &SGFInfo::filename)
        .def_readwrite("full_path", &SGFInfo::fullPath)
        .def_readwrite("player_black", &SGFInfo::playerBlack)
        .def_readwrite("player_white", &SGFInfo::playerWhite)
        .def_readwrite("result", &SGFInfo::result)
        .def_readwrite("komi", &SGFInfo::komi)
        .def_readwrite("board_size", &SGFInfo::boardSize)
        .def_readwrite("move_count", &SGFInfo::moveCount)
        .def_readwrite("date", &SGFInfo::date)
        .def_readwrite("file_size", &SGFInfo::fileSize)
        .def_readwrite("valid", &SGFInfo::valid)
        .def("__repr__", [](const SGFInfo& info) {
            return "<SGFInfo(filename='" + info.filename + 
                "', players='" + info.playerBlack + " vs " + info.playerWhite + 
                "', moves=" + std::to_string(info.moveCount) + ")>";
        });
    
    // KataGoAnalyzer class — без изменений, как у вас было
    py::class_<KataGoAnalyzer>(m, "KataGoAnalyzer")
        .def(py::init<>())
        .def("initialize", 
            [](KataGoAnalyzer& self) -> bool {
                return self.initialize();
            },
            "Initialize KataGo with auto-detected paths")
        .def("initialize", 
            [](KataGoAnalyzer& self, const KataGoConfig& config) -> bool {
                return self.initialize(config);
            },
            py::arg("config"),
            "Initialize KataGo with configuration")
        .def("initialize",
            [](KataGoAnalyzer& self, const std::string& katago_path, 
               const std::string& model_path, const std::string& config_path) -> bool {
                return self.initialize(katago_path, model_path, config_path);
            },
            py::arg("katago_path"), py::arg("model_path"), 
            py::arg("config_path") = std::string(""),
            "Initialize KataGo with paths")
        .def_static("set_default_paths", &KataGoAnalyzer::setDefaultPaths,
            py::arg("katago_path"), py::arg("model_path"), 
            py::arg("config_path") = std::string(""),
            "Set default KataGo paths")
        .def_static("auto_detect_paths", &KataGoAnalyzer::autoDetectPaths,
            "Auto-detect KataGo paths")
        .def_static("is_available", 
            [](const std::string& path) -> bool {
                return KataGoAnalyzer::isAvailable(path);
            },
            py::arg("katago_path") = std::string(""),
            "Check if KataGo is available")
        .def("analyze_sgf", 
            [](KataGoAnalyzer& self, const std::string& sgf_content, 
               int board_size, double komi) -> KataGoResult {
                return self.analyzeSGF(sgf_content, board_size, komi);
            },
            py::arg("sgf_content"), py::arg("board_size") = 19, py::arg("komi") = 6.5,
            "Analyze SGF file")
        .def("analyze_sgf_file", &KataGoAnalyzer::analyzeSGFFile,
         py::arg("filepath"), 
         py::arg("board_size") = -1, 
         py::arg("komi") = -1.0,
         "Analyze SGF file")
        .def_static("get_loaded_sgf_path", &KataGoAnalyzer::getLoadedSGFPath,
         "Get path to games/loaded folder")
        .def_static("list_sgf_files", &KataGoAnalyzer::listSGFFiles,
         py::arg("directory") = std::string(""),
         "List all SGF files in the loaded folder")
        .def_static("parse_sgf_info", &KataGoAnalyzer::parseSGFInfo,
         py::arg("filepath"),
         "Parse SGF file info")
        .def_static("read_sgf_file", &KataGoAnalyzer::readSGFFile,
         py::arg("filepath"),
         "Read SGF file content")
        .def("shutdown", &KataGoAnalyzer::shutdown,
            "Shutdown KataGo")
        .def("__enter__", [](KataGoAnalyzer& self) -> KataGoAnalyzer& { 
            return self; 
        })
        .def("__exit__", [](KataGoAnalyzer& self, py::object, py::object, py::object) {
            self.shutdown();
        });
    
    // Utility functions
    m.def("get_opponent_color", &getOpponentColor);
    m.def("getBoardSize",&getBoardSizeFromSGF);
}