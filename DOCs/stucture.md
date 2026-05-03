OS_GO/                          # Корень проекта
├── auth/                       
│   ├── app/                  
│   │   ├── main.py             
│   │   ├── config.py        
│   │   ├── database.py        
│   │   │
│   │   ├── models/            
│   │   │   └── user.py       
│   │   │
│   │   ├── schemas/            
│   │   │   └── auth.py        
│   │   │
│   │   ├── services/           
│   │   │   ├── password_service.py   
│   │   │   └── totp_service.py       
│   │   │
│   │   ├── routers/           
│   │   │   └── auth.py        
│   │   │
│   │   └── dependencies/     
│   │       └── auth.py        
│   │
│   ├── .env                   
│   └── requirements.txt        
│
│  
│  
├── bot/                        
│   ├── KataGo-1.16.4-OpenCL/
│   └── gnugo-3.8/               
│
├── core/                       #  Ядро для игры в ГО
│   ├── build/
│   ├── Bindings.cpp           
│   ├── Board_new.h  
│   ├── CMakeLists.txt
│   ├── core.cpp
│   ├── core.h
│   ├── pyproject.toml 
│   └── test_lib_conection.py              
│
├── games/                     # Сохраненные партии в sgf формате                   
│   ├── autosave/
│   ├── loaded/
│   ├── puzzles/
│   ├── pvp/                
│   ├── pve/                 
│   └── reviews/                   
│  
├── interface/                  #  Интерфейс
│   ├── core/
│   ├── generated/                    
│   ├── ui/    
│   ├── windows/         
│   └── main.py                  
│  
├── scripts/                    #  Основные части программы
│   ├──network_pvp/
│   │   ├── client.py
│   │   ├── console_network.py
│   │   ├── output_interface.py
│   │   ├── protocol.py
│   │   └── server.py
│   ├── config.py
│   ├── console_analyzer.py
│   ├── console_back.py            
│   ├── console_PVE.py
│   ├── console_PVP.py
│   ├── core_adapter.py
│   ├── game_controller.py
│   ├── gnugo_adapter.py
│   ├── GnuGo_Analyzer.py 
│   ├── KataGoAdapter.py
│   ├── KataGoAnalyzer.py
│   ├── sgf_analyzer.py 
│   ├── unified_game_loop.py              
│   └── PLAY_console.py           
│  
├── docker-compose.yml
│
├── Dockerfile
│
└── venv/                       # Виртуальное окружение Python