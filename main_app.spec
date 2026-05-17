# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main_app.py'],
    pathex=[],
    binaries=[
        # C++ МОДУЛЬ (pybind11)
        ('venv/Lib/site-packages/go_engine.pyd', '.'),
        
        # GNU GO
        ('bot/gnugo-3.8/gnugo.exe', 'bot/gnugo-3.8'),
        ('bot/gnugo-3.8/cygwin1.dll', 'bot/gnugo-3.8'),
        ('bot/gnugo-3.8/cyggcc_s-1.dll', 'bot/gnugo-3.8'),
        ('bot/gnugo-3.8/cygncurses-10.dll', 'bot/gnugo-3.8'),
        
        # KataGo и все его DLL (каждый файл отдельно)
        ('bot/KataGo-1.16.4-OpenCL/katago.exe', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/msvcp140.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/msvcp140_1.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/msvcp140_2.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/vcruntime140.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/vcruntime140_1.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/libcrypto-3-x64.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/libssl-3-x64.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/libz.dll', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/libzip.dll', 'bot/KataGo-1.16.4-OpenCL'),
    ],
    datas=[
        # UI-файлы (целые папки)
        ('interface/Go_app/ui', 'interface/Go_app/ui'),
        ('interface/Go_app/themes', 'interface/Go_app/themes'),
        ('interface/Go_app/icons', 'interface/Go_app/icons'),
        ('interface/Go_app/generated', 'interface/Go_app/generated'),
        ('interface/Go_app/windows', 'interface/Go_app/windows'),
        
        # Модели KataGo (целые папки)
        ('bot/KataGo-1.16.4-OpenCL/models', 'bot/KataGo-1.16.4-OpenCL/models'),
        ('bot/KataGo-1.16.4-OpenCL/KataGoData', 'bot/KataGo-1.16.4-OpenCL/KataGoData'),
        
        # Конфиги KataGo
        ('bot/KataGo-1.16.4-OpenCL/*.cfg', 'bot/KataGo-1.16.4-OpenCL'),
        ('bot/KataGo-1.16.4-OpenCL/cacert.pem', 'bot/KataGo-1.16.4-OpenCL'),
        
        # GNU GO README
        ('bot/gnugo-3.8/COPYING', 'bot/gnugo-3.8'),
        ('bot/gnugo-3.8/README', 'bot/gnugo-3.8'),
        
        # Web-файлы для auth
        ('auth/app/static', 'auth/app/static'),
        
        # Шрифты (конкретные файлы)
        #('venv/Lib/site-packages/customtkinter/assets/fonts/Roboto-Medium.ttf', 'customtkinter/assets/fonts'),
        #('venv/Lib/site-packages/customtkinter/assets/fonts/Roboto-Regular.ttf', 'customtkinter/assets/fonts'),
        #('venv/Lib/site-packages/customtkinter/assets/fonts/CustomTkinter_shapes_font.otf', 'customtkinter/assets/fonts'),
        
        # Темы customtkinter
        ('venv/Lib/site-packages/customtkinter/assets/themes', 'customtkinter/assets/themes'),
        
        # Иконка приложения
        ('interface/Go_app/ui/icona.ico', '.'),

        ('scripts', 'scripts'),
        ('scripts/network_pvp', 'scripts/network_pvp'),
    ],
    hiddenimports=[
        # PySide6
        'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtQml', 'PySide6.QtQuick', 'shiboken6',
        
        # Auth
        'auth.app.main', 'auth.app.config', 'auth.app.database',
        'auth.app.models.user', 'auth.app.routers.auth',
        'auth.app.services.email_service', 'auth.app.services.totp_service',
        'auth.app.services.password_service', 'auth.app.dependencies.auth',
        
        # Core и game
        'core.core', 'core.Board_new', 'core.KataGoAnalyzer',
        'scripts.core_adapter', 'scripts.game_controller',
        'scripts.unified_game_loop', 'scripts.config',
        'scripts.gnugo_adapter', 'scripts.KataGoAdapter',
        'scripts.GnuGo_Analyzer', 'scripts.KataGoAnalyzer',
        'scripts.sgf_analyzer', 'scripts.console_PVE', 'scripts.console_PVP',
        
        # Network
        'scripts.network_pvp.client', 'scripts.network_pvp.server',
        'scripts.network_pvp.protocol', 'scripts.network_pvp.pyside_npvp',
        
        # UI
        'customtkinter', 'darkdetect', 'PIL', 'PIL._tkinter_finder',
        'interface.Go_app.core.go_board_widget',
        'interface.Go_app.windows.base_window',
        'interface.Go_app.windows.game_windowPvE',
        'interface.Go_app.windows.game_windowPvP',
        'interface.Go_app.windows.game_windowOnline',
        'interface.Go_app.windows.online_lobby',
        'interface.Go_app.windows.profile_window',
        'interface.Go_app.windows.acc_profile_window',
        'interface.Go_app.windows.app_settings',
        'interface.Go_app.windows.settings_dialog',
        'interface.Go_app.windows.rules_window',
        'interface.Go_app.game_timer',
        'interface.Go_app.navigation',
        
        # Database
        'alembic', 'alembic.config', 'alembic.command',
        'sqlalchemy', 'sqlalchemy.ext.asyncio', 'asyncpg',
        'aiosqlite',
        
        # Web framework
        'fastapi', 'fastapi.routing', 'fastapi.applications',
        'uvicorn', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
        'starlette', 'starlette.routing', 'starlette.middleware',
        'starlette.middleware.cors', 'starlette.middleware.base',
        'httpx', 'aiohttp', 'websockets',
        
        # Security
        'jose', 'jose.backends', 'jwt', 'passlib', 'passlib.handlers',
        'passlib.context', 'pyotp', 'qrcode', 'cryptography',
        'cryptography.hazmat.backends', 'argon2', 'bcrypt',
        
        # Utils
        'yaml', 'click', 'watchfiles', 'multidict', 'yarl',
        'frozenlist', 'aiosignal', 'propcache', 'charset_normalizer',
        'certifi', 'idna', 'urllib3', 'email_validator',
        'python_multipart', 'pydantic', 'pydantic_settings',
        'pydantic_core', 'typing_extensions', 'annotated_types',
        'anyio', 'sniffio', 'h11', 'httpcore', 'httptools',
    ],
    hookspath=[],
    hooksconfig={
        'PySide6': {
            'excludes': [
                'PySide6.Qt3DAnimation',
                'PySide6.Qt3DCore', 
                'PySide6.Qt3DExtras',
                'PySide6.Qt3DInput',
                'PySide6.Qt3DLogic',
                'PySide6.Qt3DRender',
                'PySide6.QtCharts',
                'PySide6.QtDataVisualization',
                'PySide6.QtGraphs',
                'PySide6.QtLocation',
                'PySide6.QtMultimedia',
                'PySide6.QtNfc',
                'PySide6.QtPdf',
                'PySide6.QtPositioning',
                'PySide6.QtRemoteObjects',
                'PySide6.QtScxml',
                'PySide6.QtSensors',
                'PySide6.QtSerialBus',
                'PySide6.QtSerialPort',
                'PySide6.QtSpatialAudio',
                'PySide6.QtStateMachine',
                'PySide6.QtTextToSpeech',
                'PySide6.QtWebChannel',
                'PySide6.QtWebEngineCore',
                'PySide6.QtWebEngineQuick',
                'PySide6.QtWebEngineWidgets',
                'PySide6.QtWebSockets',
                'PySide6.QtXml',
            ]
        },
    },
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'pdb', 'doctest', 'pytest',
        'distutils.tests', 'unittest.mock', 'test',
        'PyQt5', 'PyQt6', 'PySide2',
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'IPython', 'jupyter', 'notebook',
        'trio', 'curio',
    ],
    noarchive=False,
    cipher=None,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OS_GO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Временно True для отладки, потом можно False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='interface/Go_app/ui/icona.ico',
)