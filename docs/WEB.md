# JobDesk Web (Laravel + Vue SPA)

Веб-версия: **Laravel** в `backend/`, **Vue 3 SPA** в `frontend/`. Парсеры — Python (`jobdesk/`, `tools/fetch_worker.py`).

## Требования

- PHP 8.3+, Composer, расширения Laravel (pdo_mysql, openssl, mbstring, …)
- Node.js 20+ — **только для сборки** (`npm run build`), не dev-сервер на VPS
- Python 3.11+ и `requirements-web.txt` или `requirements.txt`
- MySQL (production) или SQLite (локально)

---

## Локальная разработка

### Backend

```bash
cd backend
copy .env.example .env   # Windows
php artisan key:generate
php artisan migrate
php artisan serve
```

Sanctum (dev с Vite на :5173):

```env
APP_URL=http://127.0.0.1:8000
SESSION_DOMAIN=localhost
SANCTUM_STATEFUL_DOMAINS=localhost:5173,127.0.0.1:5173
JOBDESK_PYTHON=C:\Python312\python.exe
```

### Frontend (dev)

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173 (proxy на Laravel для `/api` и `/sanctum`).

### Сборка SPA в Laravel public (как на VPS)

Из корня репозитория:

```bash
python tools/deploy_web.py
```

Копирует `frontend/dist` → `backend/public/assets/` и `backend/public/spa-index.html`. Laravel отдаёт SPA через [`SpaController`](../backend/app/Http/Controllers/SpaController.php).

Проверка: `php artisan serve` → http://127.0.0.1:8000/login (без Vite).

---

## VPS: Apache, MySQL, без dev-sерверов

### Вариант A: document root = `backend/public`

Каталог репозитория **выше** web root (рекомендуется, если панель позволяет указать путь).

### Вариант B: document root = `public_html` (job.saintweb.ru и аналоги)

Корень сайта на диске, например `~/job.saintweb.ru/`:

```text
job.saintweb.ru/
  backend/          # Laravel (не открывается напрямую из браузера)
  jobdesk/
  tools/
  .venv/
  public_html/      # ← сюда смотрит домен job.saintweb.ru
    index.php       # вход в Laravel (../backend)
    .htaccess
    spa-index.html
    assets/
```

**Не кладите** весь репозиторий внутрь `public_html` — наружу должны попасть только файлы из списка выше.

Сборка и синхронизация:

```bash
python tools/deploy_web.py
python tools/sync_public_html.py
```

Для **job.saintweb.ru** в `backend/.env`:

```env
APP_URL=https://job.saintweb.ru
SESSION_DOMAIN=job.saintweb.ru
SANCTUM_STATEFUL_DOMAINS=job.saintweb.ru
FRONTEND_URL=https://job.saintweb.ru
JOBDESK_PYTHON=/home/ВАШ_ЛОГИН/job.saintweb.ru/.venv/bin/python
```

(подставьте реальный путь к домашней папке с сайтом.)

---

Document root по умолчанию в доке: **`backend/public`** (вариант A).

```text
/var/www/jobdesk/
  jobdesk/              # парсеры
  tools/fetch_worker.py
  .venv/                # python3 -m venv .venv
  .env                  # опционально HH/Telegram (не в public)
  backend/
    .env
    storage/            # writable
    bootstrap/cache/    # writable
    public/             # ← document root
      index.php
      spa-index.html
      assets/
```

### 1. Сборка (локально или один раз по SSH)

```bash
cd backend && composer install --no-dev --optimize-autoloader
cd .. && python tools/deploy_web.py
```

На VPS **не** запускать `npm run dev`, `php artisan serve`, `vite`.

### 2. `backend/.env`

Шаблон: [`backend/.env.production.example`](../backend/.env.production.example).

```env
APP_ENV=production
APP_DEBUG=false
APP_URL=https://your-domain.example

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_DATABASE=jobdesk
DB_USERNAME=...
DB_PASSWORD=...

SESSION_DRIVER=database
SESSION_SECURE_COOKIE=true
SESSION_DOMAIN=your-domain.example

SANCTUM_STATEFUL_DOMAINS=your-domain.example
FRONTEND_URL=https://your-domain.example

JOBDESK_PYTHON=/var/www/jobdesk/.venv/bin/python
JOBDESK_ALLOW_REGISTRATION=false
```

### 3. Python на сервере

**VPS с sudo** (venv):

```bash
cd /var/www/jobdesk
python3 -m venv .venv
.venv/bin/pip install -r requirements-web.txt
```

**Shared-хостинг без sudo** (нет `python3-venv`, `apt` недоступен):

```bash
cd ~/job
python3 -m pip install --user -r requirements-web.txt
```

В `backend/.env`:

```env
JOBDESK_PYTHON=/usr/bin/python3
```

(путь уточните: `which python3`.)

Если `--user` не срабатывает или пакеты не видны из PHP, установка в каталог проекта:

```bash
cd ~/job
mkdir -p python_packages
python3 -m pip install --target "$HOME/job/python_packages" -r requirements-web.txt
```

```env
JOBDESK_PYTHON=/usr/bin/python3
JOBDESK_PYTHONPATH=/home/s/sashjam/job/python_packages
```

Venv создавайте в **корне** `~/job/.venv`, не в `backend/.venv`.

Проверка:

```bash
echo '{"subscriptions":[{"name":"t","source":"habr_rss","query":"python","enabled":true}],"settings":{}}' \
  | .venv/bin/python tools/fetch_worker.py | head -c 300
```

### 4. Laravel (однократно по SSH)

```bash
cd backend
php artisan key:generate    # новый сервер
php artisan migrate --force
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

Права: `storage/`, `bootstrap/cache/` — запись для пользователя PHP-FPM.

PHP: `max_execution_time` ≥ 300 (опрос сайтов до ~5 мин).

### 5. Apache

- `DocumentRoot /var/www/jobdesk/backend/public`
- `AllowOverride All` для `.htaccess`
- HTTPS обязателен для cookie Sanctum

### 6. Проверка `proc_open`

Кнопка «Обновить с сайтов» вызывает Python через `proc_open`. Временный файл в `public/` (удалить после проверки):

```php
<?php
// public/_probe.php — НЕ оставлять на production
header('Content-Type: text/plain; charset=utf-8');
echo function_exists('proc_open') ? "proc_open: yes\n" : "proc_open: no\n";
echo 'disable_functions: '.ini_get('disable_functions')."\n";
```

Откройте `https://your-domain/_probe.php`. Если `proc_open` в `disable_functions` — UI-fetch не сработает.

**Запасной вариант — cron** (раз в 15 мин, пример):

```cron
*/15 * * * * cd /var/www/jobdesk/backend && php artisan jobdesk:fetch >> /var/log/jobdesk-fetch.log 2>&1
```

Для одного пользователя:

```bash
php artisan jobdesk:fetch --user=1
```

### 7. Чеклист после выкладки

1. `https://your-domain/login` — SPA, не Laravel welcome
2. Вход / регистрация (если `JOBDESK_ALLOW_REGISTRATION=true`)
3. Подписка + «Обновить с сайтов» → вакансии в MySQL
4. `storage/logs/laravel.log` без ошибок Python
5. Удалить `_probe.php`, `APP_DEBUG=false`

### 8. Обновление версии

```bash
git pull
cd backend && composer install --no-dev
cd .. && python tools/deploy_web.py
cd backend && php artisan migrate --force && php artisan config:cache && php artisan route:cache
```

---

## Авторизация

- Sanctum (cookie + CSRF): `/api/login`, `/api/register`, `/api/logout`, `/api/user`, `/sanctum/csrf-cookie`
- Остальные `/api/*` — только для авторизованных
- Данные изолированы по `user_id`

## Опрос сайтов

- UI: `POST /api/fetch` → `JobDeskFetchService` → `tools/fetch_worker.py`
- Cron: `php artisan jobdesk:fetch`

Корневой `.env` (Telegram, HH) — см. `.env.example` в корне; не публикуйте в web.
