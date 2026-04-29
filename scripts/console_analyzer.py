# scripts/console_analyzer.py
"""
Консольное меню для анализа SGF файлов
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sgf_analyzer import SGFAnalyzer


def clear_screen():
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    """Печать заголовка"""
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def format_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def show_file_list(analyzer: SGFAnalyzer):
    """Показать список файлов"""
    clear_screen()
    print_header("СПИСОК SGF ФАЙЛОВ")
    
    files = analyzer.get_sgf_files()
    
    if not files:
        print(f"\n📭 Папка пуста")
        print(f"📁 Добавьте SGF файлы в: {analyzer.sgf_dir}")
        return
    
    print(f"\n📁 Папка: {analyzer.sgf_dir}")
    print(f"📄 Найдено файлов: {len(files)}")
    print()
    print("-" * 60)
    
    for i, info in enumerate(files, 1):
        print(f"{i:2}. {info.filename}")
        if info.valid:
            print(f"    ⚫ {info.player_black or '?'} vs ⚪ {info.player_white or '?'}")
            print(f"    📐 {info.board_size}x{info.board_size} | 🎯 {info.move_count} ходов")
            if info.result:
                print(f"    🏆 {info.result}")
        print(f"    💾 {format_size(info.file_size)}")
        print()
    
    print("-" * 60)


def select_and_analyze(analyzer: SGFAnalyzer):
    """Выбрать файл и проанализировать"""
    clear_screen()
    print_header("ВЫБОР ФАЙЛА ДЛЯ АНАЛИЗА")
    
    files = analyzer.get_sgf_files()
    
    if not files:
        print(f"\n📭 Нет SGF файлов для анализа")
        print(f"📁 Добавьте файлы в: {analyzer.sgf_dir}")
        input("\nНажмите Enter...")
        return
    
    print(f"\n📁 Доступно файлов: {len(files)}")
    print()
    
    for i, info in enumerate(files, 1):
        status = "✅" if info.valid else "⚠️"
        players = f"{info.player_black or '?'} vs {info.player_white or '?'}" if info.valid else "?"
        print(f"{i:2}. {status} {info.filename}")
        print(f"    {players} | {info.move_count} ходов")
    
    print()
    print("0. Отмена")
    
    try:
        choice = input("\n📎 Выберите номер файла: ").strip()
        if choice == '0':
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(files):
            print("❌ Неверный номер")
            input("\nНажмите Enter...")
            return
        
        selected = files[idx]
        
        # Анализ
        clear_screen()
        print_header("АНАЛИЗ ФАЙЛА")
        
        result = analyzer.analyze_file(selected.full_path)
        
        if result and result.success:
            print("\n" + "=" * 60)
            print("📊 РЕЗУЛЬТАТ")
            print("=" * 60)
            print(f"🏆 Победитель: {result.winner}")
            print(f"📈 Счет: {result.full_result}")
            print(f"⚫ Черные: {result.black_score:.1f}")
            print(f"⚪ Белые: {result.white_score:.1f}")
            print(f"📊 Отрыв: {result.margin:.1f}")
            
            if result.best_move:
                print(f"\n💡 Лучший ход: {result.best_move}")
            
            if result.top_moves:
                print(f"\n🎯 Топ-5 ходов:")
                for i, move in enumerate(result.top_moves[:5], 1):
                    print(f"   {i}. {move}")
            
            # Сохранение
            save = input("\n💾 Сохранить результат? (y/n) [y]: ").strip().lower()
            if save != 'n':
                saved_path = analyzer.save_result(Path(selected.full_path).stem, result)
                if saved_path:
                    print(f"✅ Сохранено: {saved_path}")
        else:
            print(f"\n❌ Анализ не выполнен")
            if result:
                print(f"   {result.error_message}")
        
        input("\nНажмите Enter...")
        
    except ValueError:
        print("❌ Введите число")
        input("\nНажмите Enter...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        input("\nНажмите Enter...")


def open_sgf_folder(analyzer: SGFAnalyzer):
    """Открыть папку в проводнике"""
    os.startfile(analyzer.sgf_dir)
    print(f"\n📁 Папка открыта: {analyzer.sgf_dir}")
    input("\nНажмите Enter...")


def run_sgf_analyzer():
    """Главная функция анализатора"""
    analyzer = SGFAnalyzer()
    
    try:
        while True:
            clear_screen()
            print_header("АНАЛИЗ SGF ФАЙЛОВ (KATAGO)")
            
            files = analyzer.get_sgf_files()
            file_count = len(files)
            
            print(f"\n📁 Папка: {analyzer.sgf_dir}")
            print(f"📄 Найдено файлов: {file_count}")
            print()
            print("1. 📋 Показать список файлов")
            print(f"2. 🔍 Выбрать файл для анализа ({file_count} доступно)")
            print("3. 📂 Открыть папку с SGF файлами")
            print("0. 🚪 Назад в главное меню")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '1':
                show_file_list(analyzer)
                input("\nНажмите Enter...")
            elif choice == '2':
                select_and_analyze(analyzer)
            elif choice == '3':
                open_sgf_folder(analyzer)
            elif choice == '0':
                break
            else:
                print("\n❌ Неверный выбор")
                input("\nНажмите Enter...")
    
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    run_sgf_analyzer()