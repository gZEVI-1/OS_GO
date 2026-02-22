=============РАЗДЕЛ 1===============
1) УСТАНОВКА БИБЛИОТЕКИ GO_ENGINE 

    0. установить msys2 в с:\msys64    (https://www.msys2.org)

    1. отктыть mingw64.exe

    2. выполнить :
        cd /буква диска(маленькая)/Пусть/к/проекту/.../core
    обязательно / вместо \, маленькая буква диска без : и без кирилицы

    3. последовательно выполнить группы команд :
        pacman -S mingw-w64-x86_64-python
        pacman -S mingw-w64-x86_64-python-pip
        pacman -S mingw-w64-x86_64-pybind11
        pacman -S mingw-w64-x86_64-cmake

    потом :
        pacman -Syu

    потом:
        rm -rf build/*
        cmake -S . -B build \
        -DPython3_EXECUTABLE="/mingw64/bin/python.exe" \
        -DPython3_FIND_STRATEGY=LOCATION \
        -G "MinGW Makefiles"
        cmake --build build
    
    потом:
        cd build
        cp go_engine*.pyd /mingw64/lib/python3.14/site-packages/
    если python  не 3.14й то поменять путь 

    (впоследствии pacman команды можно не выполнять )

    в core должна появиться папка build а в ней файл с расширением .pyd

    4. в path выбрать питон из msys64\mingw64\bin
    5. в IDE выбрать тот же питон 
        (с VS code могут быть ошибки, нужно удалить из path все остальные варианты питона, возможно поменять данные в json файле)
    6. запустить core\test_lib.py и убедиться в установке 


