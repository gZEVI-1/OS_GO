try:
    import go_engine
    print("✅ go_engine работает!")
    print("Доступные функции:", dir(go_engine))
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
# 