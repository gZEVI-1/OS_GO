
# 📋 Содержание
>- [Предварительная настройка системы](#предварительная-настройка-системы)
>- [Настройка VSCode](#настройка-vscode)
>- [Сборка проекта](#сборка-проекта)
>- [Ежедневная работа](#ежедневная-работа)
>- [Полезные команды (шпаргалка)](#полезные-команды-шпаргалка)

---

## Предварительная настройка системы
### 1. Установка Python
**Важно:** Используйте официальную версию Python с python.org, НЕ из Microsoft Store!

1. Перейдите на [python.org/downloads](https://python.org/downloads)
2. Скачайте Python 3.14.3 или новее
3. **ОБЯЗАТЕЛЬНО** отметьте галочку **"Add Python to PATH"** при установке
4. Выберите "Customize installation" . Убедитесь, что отмечены все опции
5. После установки проверьте в **Git Bash/cmd/PowerShell**:

```bash
python --version
pip --version
```

6. Если pip меньше 26ой версии пропишите 

```bash
python -m pip install --upgrade pip
```

### 2. Установка Git Bash

Git Bash даст вам привычные unix-команды на Windows.

1. Скачайте Git для Windows: [git-scm.com/downloads/win](https://git-scm.com/downloads/win)
2. При установке выберите:
	- **"Git from the command line and also from 3rd-party software"**
	- **"Use MinTTY"** (терминал по умолчанию)
	- **"Checkout Windows-style, commit Unix-style line endings"**
3. Остальные опции оставьте по умолчанию

### 3. Установка компилятора C++

#### Вариант 1 (если у вас уже есть Visual Studio):
Если у вас уже установлена Visual Studio 2019, 2022 или новее, дополнительных действий не требуется. Просто убедитесь, что при установке Visual Studio был выбран компонент **"Desktop development with C++"** .

**Как проверить:**
1. Откройте Visual Studio Installer
2. Найдите вашу установку Visual Studio
3. Нажмите "Modify" (Изменить)
4. Проверьте, что в списке Workloads отмечен **"Desktop development with C++"**
5. Если нет - отметьте его и нажмите "Modify"

#### Вариант 2 (если Visual Studio НЕ установлена):
Скачайте Visual Studio Build Tools: 
[visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

Запустите установщик и выберите **"Desktop development with C++"** .
**Для обоих вариантов:**
- Убедитесь, что установлены компоненты:
- MSVC v143 - VS 2022 C++ x64/x86 build tools
- Windows 10/11 SDK

### 4. Установка CMake

1. Скачайте CMake: [cmake.org/download](https://cmake.org/download)
2. Выберите **"Windows x64 Installer"**
3. При установке ОБЯЗАТЕЛЬНО выберите **"Add CMake to system PATH"**

---



## Настройка VSCode

### 1. Установка расширений

Откройте VSCode и установите следующие расширения (Ctrl+Shift+X):

**Обязательные:**

- **Python** (Microsoft) - поддержка Python
- **C/C++** (Microsoft) - подсветка C++ кода
- **CMake Tools** (Microsoft) - интеграция с CMake

**Рекомендуемые:**

- **GitLens** - улучшенная работа с Git
- **Bracket Pair Colorizer** - подсветка скобок

### 2. Настройка терминала

Откройте настройки VSCode (Ctrl+,) и добавьте (строка №2 добавляет git bash по умолчанию, опциональна ):

```json
{
    "terminal.integrated.defaultProfile.windows": "Git Bash",
    "terminal.integrated.profiles.windows": {
        "Git Bash": {
            "path": "C:\\Program Files\\Git\\bin\\bash.exe",
            "args": ["--login"]
        }
    },
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true
}
```

### 3. Настройка для работы с проектом

Создайте (если еще нет) в корне проекта папку `.vscode` и файл `settings.json`:

```json
{
	"python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "cmake.sourceDirectory": "${workspaceFolder}/core",
    "cmake.buildDirectory": "${workspaceFolder}/core/build",
    "files.associations": {
        "*.cpp": "cpp",
        "*.h": "cpp"
    }
}
```




---


## Сборка проекта

### 1. Структура проекта
### 2. Пошаговая сборка

#### 1) Открыть проект в VSCode

```bash
cd /c/путь/к/вашему/проекту
code .
```
#### 2) Создать виртуальное окружение

В терминале VSCode (именно Git Bash):
```bash
python -m venv venv
source venv/Scripts/activate
```
#### 3) Установить библиотеки


```bash
deactivate 
python -m pip install --upgrade pip
pip install pybind11

source venv/Scripts/activate
pip install pyside6
pip install cmake
```
#### 4) Собрать библиотеку GO_ENGINE

Выберите нужную версию Visual Studio
```bash
cd core
rm -rf build

PYBIND11_PATH=$(python -c "import pybind11; print(pybind11.get_cmake_dir())")
echo "pybind11 found at: $PYBIND11_PATH"


#-G "Visual Studio 16 2019" -A x64 \
#-G "Visual Studio 17 2022" -A x64 \
#-G "Visual Studio 18 2026" -A x64 \ 
cmake -S . -B build \
    -G "Visual Studio 18 2026" -A x64 \ 
    -Dpybind11_DIR="$PYBIND11_PATH"

cmake --build build --config Release
cp build/Release/go_engine*.pyd ../venv/Lib/site-packages/
cd ..
```

#### 5) Быстрый тест
Запустите:
```
source venv/Scripts/activate
python core/test_lib_con.py
```
Если все хорошо, потом :
```bash
python core/test_bind.py
```

---
## Ежедневная работа

### Стандартный workflow при каждом открытии проекта

1. **Открыть проект в VSCode:**
```bash
cd /c/путь/к/проекту
code .
```

2. **Активировать виртуальное окружение** (в терминале VSCode):
```bash
source venv/Scripts/activate
```

3. **Начать разработку**
### Альтернатива (без пересборки)

1. **Открыть проект в VSCode**
2. **В правом нижнем углу выбрать enviroment и интерпретатор из venv**
3.  **Начать разработку**

### После изменений в C++ коде

```bash
cd core
rm -rf build
#"Visual Studio 16 2019"  
#"Visual Studio 17 2022" 
#"Visual Studio 18 2026" 
cmake -S . -B build -G "Visual Studio 18 2026" -A x64
cmake --build build --config Release
cp build/Release/go_engine*.pyd ../venv/Lib/site-packages/
cd ..
```
---
## Полезные команды (шпаргалка)
```bash
# Активация venv
source venv/Scripts/activate

# Деактивация venv
deactivate

# Показать установленные пакеты
pip list

# Сохранить текущие зависимости
pip freeze > requirements.txt

# Удалить venv (если нужно пересоздать)
rm -rf venv

# Пересоздать venv с нуля
rm -rf venv
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

# Очистить сборку
cd core && rm -rf build && cd ..

# Полная пересборка
cd core && rm -rf build && \
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 && \
cmake --build build --config Release && \
cp build/Release/go_engine*.pyd ../venv/Lib/site-packages/ && \
cd ..
```
---