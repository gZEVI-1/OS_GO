# OS-GO Network PvP — Документация интеграции

## Обзор архитектуры
┌─────────────┐      WebSocket      ┌─────────────┐
│  PySide6    │ ◄─────────────────► │   Server    │
│  Frontend   │    JSON Protocol    │  (Python)   │
│             │                     │  go_engine  │
└─────────────┘                     └─────────────┘
│
▼
┌─────────────┐
│ NetworkClient│  ← Переиспользуйте этот класс
│  (client.py) │
└─────────────┘
