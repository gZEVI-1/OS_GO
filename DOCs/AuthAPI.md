# OS_GO AuthApi

Краткое описание проекта.

Сервис аутентификации на FastAPI с поддержкой локальной регистрации, Auth0, двухфакторной аутентификации (TOTP) и управления паролями. Включает десктопный клиент на PySide6.

## Содержание

- [Технологии](#технологии)
- [Архитектура](#архитектура)
- [Установка](#установка)
- [Запуск](#запуск)
- [API Endpoints](#api-endpoints)
- [Переменные окружения](#переменные-окружения)
- [Миграции базы данных](#миграции-базы-данных)
- [Десктопный клиент](#десктопный-клиент)
- [Безопасность](#безопасность)
- [Примеры использования](#примеры-использования)

---

## Технологии

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Uvicorn |
| База данных | SQLite (async via aiosqlite) |
| ORM | SQLAlchemy 2.0 (async) |
| Миграции | Alembic |
| Хеширование паролей | Argon2id / BCrypt |
| JWT | python-jose |
| 2FA | pyotp (TOTP) + qrcode |
| Шифрование | cryptography (Fernet) |
| Email | smtplib (SMTP) |
| Десктопный клиент | PySide6 |
| Валидация | Pydantic v2 |

---

## Архитектура

OS_GO/
├── app/
│   ├── config.py              # Конфигурация через Pydantic Settings
│   ├── database.py            # Async SQLAlchemy engine + session
│   ├── main.py                # FastAPI приложение, CORS, static files
│   ├── models/
│   │   ├── init.py
│   │   └── user.py            # Модель User (SQLAlchemy ORM)
│   ├── routers/
│   │   ├── init.py
│   │   └── auth.py            # API endpoints (/auth/*)
│   ├── services/
│   │   ├── init.py
│   │   ├── email_service.py   # Отправка писем (SMTP / консоль)
│   │   ├── password_service.py # Хеширование Argon2/BCrypt
│   │   └── totp_service.py     # TOTP, QR-коды, backup codes
│   └── dependencies/
│       ├── init.py
│       └── auth.py            # JWT: создание, верификация, Auth0
├── alembic/
│   ├── env.py                 # Async-совместимая конфигурация Alembic
│   ├── script.py.mako
│   └── versions/
│       └── init.py        # Миграционные файлы (.py)
├── auth/
│   └── desktop/
│       └── main.py            # PySide6 GUI клиент
├── static/                    # Статические файлы (index.html)
├── .env                       # Переменные окружения
├── .env.example               # Шаблон .env
├── alembic.ini                # Конфигурация Alembic
├── requirements.txt           # Зависимости Python
├── run.py                     # Точка входа: uvicorn
└── test_env.py                # Проверка загрузки конфигурации

---

## Установка

```bash
# Клонирование
git clone <repo-url>
cd OS_GO/auth

# Виртуальное окружение
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Зависимости
pip install -r requirements.txt


---
## Запуск

&lt;!-- Как запустить сервер и клиент --&gt;

### Проверка конфигурации

&lt;!-- python test_env.py
Ожидаемый вывод
✅ Settings loaded! DB: sqlite+aiosqlite:///./auth.db... --&gt;

### Миграции базы данных

&lt;!-- alembic revision --autogenerate -m "описание изменений"

# Применение
alembic upgrade head

# История
alembic history--&gt;

### Запуск сервера

&lt;!-- python run.py

# Или напрямую
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (без reload, многопоточность)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --&gt;

Сервер доступен по адресам:
API: http://localhost:8000
Документация Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

Примечание: такой адресс сервера для сугубо локального использования, если вы хотите использовать сервер удаленно, то следует обращаться к нему по адресу: http://51.250.64.161:8000

### Запуск десктопного клиента

&lt;!-- cd auth/desktop
        python main.py.. --&gt;
Клиент будет подключаться или к http://localhost:8000 или http://51.250.64.161:8000 в зависимости от переменной API_BASE в auth/desktop/main.py

## API Endpoints

&lt;!-- Таблица или список всех API endpoints. Подзаголовки ниже — по желанию. --&gt;

### Аутентификация

&lt;!-- Метод	Путь	        Описание	                       Требует авторизации
        POST	/auth/register	Регистрация нового пользователя	        Нет
        POST	/auth/login	    Вход по email + пароль (OAuth2 form)	Нет
        POST	/auth/auth0/callback	Callback от Auth0	Bearer Auth0 token
        GET	    /auth/me	    Данные текущего пользователя	Bearer --&gt;

### Управление паролями

&lt;!-- Метод	Путь	Описание	Требует авторизации
POST	/auth/change-password	Смена пароля (нужен старый)	Bearer
POST	/auth/forgot-password	Запрос сброса пароля (email)	Нет
GET	/auth/reset-password?token=	Проверка валидности токена сброса	Нет
POST	/auth/reset-password	Установка нового пароля по токену	Нет --&gt;

### Двухфакторная аутентификация

&lt;!-- Метод	Путь	Описание	Требует авторизации
POST	/auth/2fa/setup	Начало настройки TOTP (генерация секрета, QR)	Bearer
POST	/auth/2fa/verify-setup	Подтверждение настройки первым кодом	Bearer
POST	/auth/2fa/verify	Верификация TOTP при входе (временный токен)	Bearer temp
POST	/auth/2fa/disable	Отключение 2FA (требует код)	Bearer --&gt;

### Верификация email

&lt;!-- Метод	Путь	Описание	Требует авторизации
GET	/auth/verify-email?token=	Подтверждение email по ссылке	Нет
POST	/auth/resend-verification	Повторная отправка письма	Нет --&gt;

### Управление аккаунтом

&lt;!-- DELETE	/auth/delete-account	Удаление аккаунта (с подтверждением пароля)	Bearer
GET	/auth/protected	Тестовый защищённый маршрут	Bearer --&gt;

### Служебные

&lt;!-- Метод	Путь	Описание
GET	/health	Проверка работоспособности
GET	/	Главная страница (static/index.html)
--&gt;

---

## Переменные окружения

&lt;!-- Описание .env файла, примеры переменных. --&gt;

# === Application ===
APP_NAME=Auth Service
DEBUG=false
SECRET_KEY=your-super-secret-key-change-in-production

# === Database ===
DATABASE_URL=sqlite+aiosqlite:///./auth.db

# === JWT ===
JWT_SECRET=your-jwt-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# === Password Hashing ===
PASSWORD_HASH_SCHEME=argon2          # или bcrypt
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4
BCRYPT_ROUNDS=12

# === 2FA ===
TOTP_ISSUER_NAME=OS_GO
TOTP_DIGITS=6
TOTP_INTERVAL=30

# === Email / SMTP ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@os-go.com
SMTP_USE_TLS=true

# === Verification ===
VERIFICATION_TOKEN_EXPIRE_HOURS=24
APP_URL=http://localhost:8000

# === Auth0 (опционально) ===
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-identifier
AUTH0_ISSUER=https://your-domain.auth0.com/
AUTH0_ALGORITHMS=["RS256"]

## Миграции базы данных

&lt;!-- Как работать с Alembic. Подзаголовки ниже — по желанию. --&gt;

### Инициализация

&lt;!-- ... --&gt;

### Создание миграций

&lt;!-- ... --&gt;

### Откат

&lt;!-- ... --&gt;

---

## Десктопный клиент

&lt;!-- Описание GUI. Подзаголовки ниже — по желанию. --&gt;

### Экраны приложения

&lt;!-- ... --&gt;

### Функционал смены пароля

&lt;!-- ... --&gt;

---

## Безопасность

&lt;!-- Таблица или список мер безопасности. --&gt;

---

## Примеры использования

&lt;!-- curl-примеры или другие примеры. Подзаголовки ниже — по желанию. --&gt;

### Регистрация

&lt;!-- ... --&gt;

### Логин

&lt;!-- ... --&gt;

### Смена пароля

&lt;!-- ... --&gt;

### Запрос сброса пароля

&lt;!-- ... --&gt;

### Сброс пароля по токену

&lt;!-- ... --&gt;

### Настройка 2FA

&lt;!-- ... --&gt;

---

## Лицензия

&lt;!-- Лицензия проекта. --&gt;