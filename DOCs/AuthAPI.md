# Документация API аутентификации

## Обзор архитектуры

Система аутентификации построена на **FastAPI** с использованием:
- **Async SQLAlchemy** + **aiosqlite** для асинхронной работы с БД
- **JWT** (внутренние токены) + **Auth0** (внешний SSO)
- **Argon2id / bcrypt** для хеширования паролей
- **TOTP** (RFC 6238) для двухфакторной аутентификации
- **Fernet** (AES-128-CBC + HMAC) для шифрования секретов 2FA
- **SMTP** для email-уведомлений

Все эндпоинты сгруппированы под префиксом `/auth`.

---

## Модель данных

### User (таблица `users`)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | `Integer PK` | Уникальный идентификатор |
| `email` | `String(255) UNIQUE` | Email пользователя |
| `hashed_password` | `LargeBinary NULL` | Хеш пароля (NULL для гостей и Auth0-пользователей) |
| `auth0_id` | `String(255) UNIQUE NULL` | ID из Auth0 |
| `totp_secret` | `LargeBinary NULL` | Зашифрованный TOTP-секрет |
| `totp_enabled` | `Boolean DEFAULT FALSE` | Включена ли 2FA |
| `totp_verified` | `Boolean DEFAULT FALSE` | Подтверждена ли настройка 2FA |
| `backup_codes` | `LargeBinary NULL` | Зашифрованные backup-коды |
| `is_active` | `Boolean DEFAULT TRUE` | Активен ли аккаунт |
| `is_verified` | `Boolean DEFAULT FALSE` | Подтвержден ли email |
| `reset_password_token` | `String(255) NULL` | Токен сброса пароля |
| `reset_password_expires` | `DateTime TZ NULL` | Срок действия токена сброса |
| `verification_token` | `String(255) NULL` | Токен верификации email |
| `verification_token_expires` | `DateTime TZ NULL` | Срок действия токена верификации |
| `created_at` | `DateTime TZ` | Дата создания |
| `updated_at` | `DateTime TZ` | Дата обновления |
| `last_login` | `DateTime TZ NULL` | Последний вход |

---

## Схемы запросов/ответов (Pydantic)

### `RegisterRequest`
```json
{
  "email": "user@example.com",
  "password": "string",
  "first_name": "string | null",
  "last_name": "string | null"
}
```

### `LoginResponse`
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 900,
  "requires_2fa": false
}
```

### `TOTPSetupResponse`
```json
{
  "secret": "string",           // Для ручного ввода
  "qr_code": "string",          // base64 PNG
  "backup_codes": ["XXXX-XXXX-XXXX", ...]  // 10 кодов
}
```

### `TOTPVerifyRequest`
```json
{
  "token": "123456"  // 6-значный код
}
```

### `ChangePasswordRequest`
```json
{
  "old_password": "string",
  "new_password": "string"  // min 12 символов
}
```

### `DeleteAccountRequest`
```json
{
  "password": "string"
}
```

### `ForgotPasswordRequest`
```json
{
  "email": "user@example.com"
}
```

### `ResetPasswordRequest`
```json
{
  "token": "string",
  "new_password": "string"  // min 12 символов
}
```

---

## Эндпоинты

### 🔓 Открытые эндпоинты (не требуют авторизации)

#### `POST /auth/register`
Регистрация нового пользователя с локальным паролем.

**Flow:**
1. Хеширует пароль через `PasswordService`
2. Генерирует `verification_token` (24ч валидность)
3. Сохраняет пользователя в БД
4. Отправляет письмо верификации через `BackgroundTasks`

**Ответы:**
- `201 Created` — "Registration successful. Please check your email..."
- `409 Conflict` — Email уже зарегистрирован (`IntegrityError`)

---

#### `POST /auth/login`
Локальный вход с поддержкой 2FA.

**Flow:**
1. Ищет пользователя по `email` (поле `username` из `OAuth2PasswordRequestForm`)
2. Проверяет пароль через `PasswordService`
3. Проверяет `is_verified` → `403` если не подтвержден
4. Если `totp_enabled=True` → возвращает **временный токен** с `requires_2fa: true`
5. Иначе → полноценные `access_token` + `refresh_token`

**Ответы:**
- `200 OK` — `LoginResponse`
- `401 Unauthorized` — Неверные credentials
- `403 Forbidden` — Email не подтвержден (header: `X-Email-Verification-Required: true`)

---

#### `POST /auth/auth0/callback`
Обработка callback от Auth0.

**Flow:**
1. Верифицирует JWT от Auth0 через JWKS (RS256)
2. Ищет пользователя по `auth0_id` → связывает существующего по `email` → создаёт нового
3. Проверяет 2FA аналогично локальному входу

**Ответы:**
- `200 OK` — `LoginResponse`
- `401 Unauthorized` — Невалидный Auth0 токен

---

#### `POST /auth/guest-login`
Гостевой вход без пароля.

**Flow:**
1. Генерирует `guest_{uuid}@osgo.local`
2. Создаёт пользователя с `hashed_password=NULL`, `is_verified=True`
3. Выдаёт токен без 2FA

**Ограничения гостей:**
- Нельзя сменить пароль (`403` для `@osgo.local`)
- Нельзя настроить 2FA

**Ответ:**
- `200 OK` — `LoginResponse`

---

#### `GET /auth/verify-email?token={token}`
Подтверждение email по ссылке из письма.

**Flow:**
1. Ищет пользователя по `verification_token`
2. Проверяет срок (с учётом naive datetime от SQLite)
3. Устанавливает `is_verified=True`, очищает токен

**Ответы:**
- `200 OK` — "Email verified successfully"
- `400 Bad Request` — Невалидный или просроченный токен

---

#### `POST /auth/resend-verification`
Повторная отправка письма верификации.

**Тело:** `{"email": "user@example.com"}`

**Ответы:**
- `200 OK` — "Verification email sent"
- `400 Bad Request` — Пользователь не найден или уже верифицирован

---

#### `POST /auth/forgot-password`
Запрос на сброс пароля.

**Flow:**
1. Генерирует `reset_password_token` (1ч валидность)
2. Отправляет письмо со ссылкой на `/static/reset-password.html?token=...`
3. **Всегда возвращает успех** (не раскрывает существование email)

**Ответ:**
- `200 OK` — "If email exists, reset link sent"

---

#### `GET /auth/reset-password?token={token}`
Проверка токена сброса пароля (для фронтенда).

**Ответы:**
- `200 OK` — `{"valid": true, "token": "..."}`
- `400 Bad Request` — Невалидный или просроченный токен

---

#### `POST /auth/reset-password`
Установка нового пароля по токену.

**Flow:**
1. Проверяет токен и срок
2. Хеширует новый пароль через `PasswordService`
3. Очищает токен сброса

**Ответы:**
- `200 OK` — "Password reset successful"
- `400 Bad Request` — Невалидный или просроченный токен

---

#### `POST /auth/2fa/verify`
Верификация 2FA при входе (временный токен).

**Авторизация:** `Authorization: Bearer <temp_token>` (получен при `/login`)

**Flow:**
1. Декодирует временный JWT (проверяет `totp_verified=False`)
2. Проверяет TOTP код (±1 окно времени) или backup-код
3. Если backup-код — удаляет его из списка
4. Выдаёт полноценный `access_token` + `refresh_token`

**Ответы:**
- `200 OK` — `{"access_token": "...", "refresh_token": "...", ...}`
- `400 Bad Request` — Невалидный код или 2FA не настроена
- `401 Unauthorized` — Невалидный временный токен

---

### 🔒 Защищённые эндпоинты (требуют `Authorization: Bearer <access_token>`)

#### `GET /auth/me`
Получение данных текущего пользователя.

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_verified": true,
  "totp_enabled": false
}
```

---

#### `POST /auth/2fa/setup`
Настройка TOTP 2FA.

**Flow:**
1. Генерирует TOTP-секрет (`pyotp.random_base32()`)
2. Шифрует секрет через `Fernet`
3. Генерирует 10 backup-кодов (SHA256-хеши, зашифрованные)
4. Сохраняет в БД (но **не активирует** — требуется подтверждение)
5. Возвращает QR-код (base64 PNG) + секрет + backup-коды

**Ограничения:**
- Гости (`@osgo.local`) — `403`
- Уже включённая 2FA — `400`

**Ответ:** `200 OK` — `TOTPSetupResponse`

---

#### `POST /auth/2fa/verify-setup`
Подтверждение настройки 2FA первым кодом.

**Flow:**
1. Проверяет TOTP код по сохранённому (но ещё не активированному) секрету
2. Устанавливает `totp_enabled=True`, `totp_verified=True`

**Ответ:**
- `200 OK` — "2FA enabled successfully"
- `400 Bad Request` — Невалидный код или настройка не начата

---

#### `POST /auth/2fa/disable`
Отключение 2FA.

**Flow:**
1. Требует валидный TOTP код для подтверждения
2. Очищает `totp_secret`, `totp_enabled`, `totp_verified`, `backup_codes`

**Ответ:**
- `200 OK` — "2FA disabled successfully"
- `400 Bad Request` — 2FA не включена или невалидный код

---

#### `POST /auth/change-password`
Смена пароля (когда знаешь старый).

**Ограничения:**
- Гости (`@osgo.local`) — `403`
- Неверный старый пароль — `400`

**Ответ:**
- `200 OK` — "Password changed successfully"

---

#### `DELETE /auth/delete-account`
Удаление аккаунта с подтверждением пароля.

**Flow:**
1. Проверяет пароль
2. Удаляет пользователя из БД (`cascade` если настроены связи)

**Ответ:**
- `200 OK` — "Account deleted successfully"
- `400 Bad Request` — Неверный пароль

---

#### `GET /auth/protected`
Пример защищённого маршрута.

**Ответ:**
```json
{
  "message": "Access granted",
  "user": "user@example.com"
}
```

---

## Система токенов

### Внутренний JWT

Генерируется функцией `create_internal_token()` в `dependencies/auth.py`.

**Access Token:**
```json
{
  "sub": "1",           // user_id
  "email": "user@example.com",
  "totp_verified": true,
  "totp_enabled": false,
  "type": "access",
  "iat": "2026-05-17T20:55:00",
  "exp": "2026-05-17T21:10:00"  // +15 мин
}
```

**Refresh Token:**
```json
{
  "sub": "1",
  "type": "refresh",
  "iat": "2026-05-17T20:55:00",
  "exp": "2026-05-17T20:55:00"  // +7 дней
}
```

**Подпись:** HS256, секрет из `JWT_SECRET`

### Временный токен (для 2FA)

Выдаётся при входе, если `totp_enabled=True`. Содержит `totp_verified=False`.
Используется только для `/auth/2fa/verify`.

---

## Зависимости авторизации

### `get_current_user`

Извлекает пользователя из `Authorization: Bearer <token>`.

**Проверки:**
1. Валидность JWT (подпись, срок)
2. `type == "access"`
3. Если `totp_enabled=True` и `totp_verified=False` → `403` (header: `X-2FA-Required: true`)

### `get_verified_user`

Расширяет `get_current_user` проверкой `is_verified` в БД.

**Ответ при неподтверждённом email:**
- `403 Forbidden` (header: `X-Email-Verification-Required: true`)

### `verify_auth0_token`

Верифицирует токен Auth0:
1. Загружает JWKS с `https://{auth0_domain}/.well-known/jwks.json`
2. Проверяет подпись RS256
3. Проверяет `audience` и `issuer`

---

## Сервисы

### `PasswordService` (`password_service.py`)

Поддерживает два алгоритма хеширования (конфигурируется через `PASSWORD_HASH_SCHEME`):

**Argon2id** (по умолчанию):
- `time_cost=3`, `memory_cost=65536`, `parallelism=4`
- Автоматическая проверка `check_needs_rehash()`

**bcrypt**:
- `rounds=12`

**API:**
- `hash_password(password: str) -> str`
- `verify_password(plain: str, hashed: str) -> bool`
- `needs_rehash(hashed: str) -> bool`

---

### `TOTPService` (`totp_service.py`)

**Шифрование:** Fernet (AES-128-CBC + HMAC-SHA256), ключ derived from `SECRET_KEY` через SHA256.

**API:**
- `generate_secret() -> str` — случайный base32
- `encrypt_secret(secret) -> bytes` / `decrypt_secret(encrypted) -> str`
- `generate_provisioning_uri(secret, email) -> str` — URI для Google Authenticator
- `generate_qr_code(uri) -> str` — base64 PNG
- `verify_totp(secret, token) -> bool` — проверка с окном ±1 (90 сек)
- `generate_backup_codes(count=10) -> (codes, encrypted)` — формат `XXXX-XXXX-XXXX`
- `verify_backup_code(code, encrypted) -> (valid, new_encrypted)` — одноразовые

---

### `EmailService` (`email_service.py`)

**SMTP:** Поддерживает TLS (`STARTTLS`), fallback на консольный вывод если SMTP не настроен.

**Шаблоны:** HTML + plain text для:
- Верификация email (`create_verification_email`)
- Сброс пароля (`create_reset_password_email`)

**API:**
- `generate_verification_token() -> str` — `secrets.token_urlsafe(32)`
- `send_verification_email(email, token) -> bool`
- `send_reset_password_email(email, reset_url) -> bool`

---

## Конфигурация (.env)

| Переменная | Значение по умолчанию | Описание |
|-----------|----------------------|----------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./fallback.db` | URL БД |
| `SECRET_KEY` | `default-secret-change-me` | Ключ для шифрования 2FA |
| `JWT_SECRET` | `default-jwt-secret` | Секрет подписи JWT |
| `JWT_ALGORITHM` | `HS256` | Алгоритм JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Время жизни access токена |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Время жизни refresh токена |
| `PASSWORD_HASH_SCHEME` | `argon2` | `argon2` или `bcrypt` |
| `AUTH0_DOMAIN` | `""` | Домен Auth0 |
| `AUTH0_API_AUDIENCE` | `""` | Audience Auth0 |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP сервер |
| `SMTP_PORT` | `587` | SMTP порт |
| `SMTP_USER` | `""` | Логин SMTP |
| `SMTP_PASSWORD` | `""` | Пароль SMTP |
| `APP_URL` | `http://localhost:8000` | Базовый URL приложения |
| `TOTP_ISSUER_NAME` | `YourApp` | Имя в приложении-аутентификаторе |

---

## Безопасность

### Защита от атак

| Угроза | Мера защиты |
|--------|------------|
| **Timing attacks** | Константное время сравнения в Argon2/bcrypt |
| **Password brute-force** | Argon2id с высокими параметрами |
| **TOTP time drift** | Окно проверки ±1 (90 секунд) |
| **Backup code reuse** | Удаление использованного кода |
| **Token enumeration** | Одинаковый ответ при forgot-password |
| **JWT tampering** | Подпись HS256, проверка claims |
| **Secret exposure** | Шифрование TOTP-секретов через Fernet |
| **SQL Injection** | SQLAlchemy ORM, параметризованные запросы |

### Guest-изоляция

Пользователи с доменом `@osgo.local`:
- Не могут менять пароль (`403`)
- Не могут настраивать 2FA (`403`)
- Не требуют верификации email

---

## Коды ошибок

| Код | Эндпоинт | Причина |
|-----|----------|---------|
| `400` | `/2fa/verify-setup` | Невалидный TOTP код |
| `400` | `/2fa/disable` | 2FA не включена |
| `400` | `/reset-password` | Просроченный токен |
| `400` | `/change-password` | Неверный старый пароль |
| `401` | `/login` | Неверные credentials |
| `401` | `/2fa/verify` | Невалидный временный токен |
| `403` | `/login` | Email не подтвержден |
| `403` | `/2fa/setup` | Гостевой пользователь |
| `403` | `/change-password` | Гостевой пользователь |
| `409` | `/register` | Email уже зарегистрирован |

---

## Примеры использования

### Регистрация и вход

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Верификация email (переход по ссылке из письма)
curl http://localhost:8000/auth/verify-email?token=xxx

# Вход
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123!"
```

### Настройка 2FA

```bash
# Получить QR-код
curl -X POST http://localhost:8000/auth/2fa/setup \
  -H "Authorization: Bearer <access_token>"
# Ответ: {"secret":"...","qr_code":"base64...","backup_codes":["..."]}

# Подтвердить настройку первым кодом
curl -X POST http://localhost:8000/auth/2fa/verify-setup \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"token":"123456"}'
```

### Вход с 2FA

```bash
# Шаг 1: Логин → получаем временный токен
curl -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=..."
# Ответ: {"access_token":"TEMP_TOKEN","requires_2fa":true}

# Шаг 2: Верификация 2FA
curl -X POST http://localhost:8000/auth/2fa/verify \
  -H "Authorization: Bearer TEMP_TOKEN" \
  -d '{"token":"123456"}'
# Ответ: полноценные access + refresh токены
```

### Сброс пароля

```bash
# Запрос сброса
curl -X POST http://localhost:8000/auth/forgot-password \
  -d '{"email":"user@example.com"}'

# Проверка токена (фронтенд)
curl http://localhost:8000/auth/reset-password?token=xxx

# Установка нового пароля
curl -X POST http://localhost:8000/auth/reset-password \
  -d '{"token":"xxx","new_password":"NewSecurePass123!"}'
```

---

## Диаграмма потока аутентификации

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Клиент    │────▶│  /register   │────▶│   Email     │
└─────────────┘     └──────────────┘     │  Service    │
                                         └──────┬──────┘
                                                │
┌─────────────┐     ┌──────────────┐           ▼
│  Подтвержд. │◀────│/verify-email │◀──── Письмо с ссылкой
│   Email     │     └──────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   /login    │────▶│  Проверка    │────▶│  2FA нужна? │
│  (OAuth2)   │     │ credentials  │     └──────┬──────┘
└─────────────┘     └──────────────┘            │
                                                │
                       ┌────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ 2FA enabled?   │
              └───────┬────────┘
                      │
         ┌────────────┴────────────┐
         │ Yes                     │ No
         ▼                         ▼
┌─────────────────┐      ┌──────────────────┐
│ Временный токен │      │ Access + Refresh │
│ totp_verified=0 │      │ totp_verified=1  │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│  /2fa/verify    │
│ (TOTP/backup)   │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ Access + Refresh │
│ totp_verified=1  │
└──────────────────┘
```

---

