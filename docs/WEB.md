# JobDesk Web (Laravel + Vue SPA)

Веб-версия: **Laravel API** в `backend/`, **Vue 3 SPA** в `frontend/`. Парсеры остаются на Python (`jobdesk/`, вызов через `tools/fetch_worker.py`).

## Требования

- PHP 8.3+, Composer
- Node.js 20+
- Python 3.12+ и зависимости из корневого `requirements.txt`
- Корневой `.env` для Telegram/HH (как у десктопа) — опционально для уведомлений в веб-версии

## Первый запуск

### Backend

```bash
cd backend
copy .env.example .env   # Windows
php artisan key:generate
php artisan migrate
php artisan serve
```

В `backend/.env` для SPA-авторизации:

```env
APP_URL=http://127.0.0.1:8000
SESSION_DOMAIN=localhost
SANCTUM_STATEFUL_DOMAINS=localhost:5173,127.0.0.1:5173
JOBDESK_PYTHON=C:\Python312\python.exe
```

На Windows не используйте голое `python`, если в PATH есть заглушка из Microsoft Store (`WindowsApps`). Laravel выбирает первый реальный `python.exe` через `where`, либо задайте полный путь в `JOBDESK_PYTHON`.

Зависимости парсеров — в **корне** репозитория (лучше тем же интерпретатором, что в `JOBDESK_PYTHON`):

```bash
C:\Python312\python.exe -m pip install -r requirements.txt
```

Laravel передаёт в процесс Python `USERPROFILE` и путь к user site-packages (если `pip` ставил пакеты в `%AppData%`), иначе импорты не находятся.

`fetch_worker.py` проверяет `feedparser`, `certifi`, `beautifulsoup4`, `python-dotenv` и пишет понятную ошибку, если их нет.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Откройте **http://localhost:5173** — без входа доступны только `/login` и `/register`. После регистрации или входа открываются вкладки: вакансии, желаемая работа, подписки.

## Авторизация

- Laravel Sanctum (cookie + CSRF), маршруты `/api/login`, `/api/register`, `/api/logout`, `/api/user`.
- Все `/api/*` кроме login/register — только для авторизованных (`401` → редирект на логин).
- Данные пользователей изолированы по `user_id` (подписки, вакансии, настройки).

## Опрос сайтов

Кнопка «Обновить с сайтов» → `POST /api/fetch` → PHP запускает `tools/fetch_worker.py` с конфигом подписок пользователя.

Установите Python-зависимости в корне проекта:

```bash
pip install -r requirements.txt
```

## Production (кратко)

- Собрать фронт: `cd frontend && npm run build`, отдавать `frontend/dist` через nginx или Laravel.
- Настроить `SANCTUM_STATEFUL_DOMAINS` и `SESSION_DOMAIN` под ваш домен.
- HTTPS обязателен для cookie в production.
