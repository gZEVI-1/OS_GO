import sys
print("1. Отображаемая версия:", sys.version)
print("2. Реальный путь:   ", sys.executable)
print("3. Site-packages:   ", sys.path[-1])

try:
    import go_engine
    print("✅ go_engine РАБОТАЕТ!")
except ImportError as e:
    print("❌ go_engine НЕ найден:", e)
