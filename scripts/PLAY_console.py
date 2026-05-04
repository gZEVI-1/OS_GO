
from console_back import *
from console_PVP import *
from console_PVE import *
from console_analyzer import *



def main_menu():
    """Главное меню"""
    while True:
        clear_screen()
        print("=" * 60)
        print("          ДОБРО ПОЖАЛОВАТЬ В ИГРУ ГО")
        print("=" * 60)
        print()
        print("1. 🎮 Играть против другого игрока (PvP)")
        print("2. 🤖 Играть против GNU Go (PvE)")
        print("3. 🔧 Тест соединения с GNU Go")
        print("4. 📊 Анализ SGF файлов (KataGo)")
        print("5. 🔥 Тест соединения с KataGo")
        print("6. 🚪 Выход")
        print()
        
        choice = input("Ваш выбор (1-6): ")
        
        if choice == '1':
            run_pvp_game()
        elif choice == '2':
            run_pve_game()
        elif choice == '3':
            test_gnugo_connection()
        elif choice == '4':
            run_sgf_analyzer()
        elif choice == '5':
            test_katago_connection()
        elif choice == '6':
            print("\n👋 До свидания!")
            break
        else:
            print("\n❌ Неверный выбор")
            time.sleep(1)


if __name__ == "__main__":
    main_menu()