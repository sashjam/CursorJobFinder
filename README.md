# JobDesk

Десктоп-приложение для мониторинга вакансий: подписки, периодическая проверка, уведомления.

**Инструкция пользователя:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md) (в приложении — вкладка **Справка**)

**Техническая документация:** [docs/JobDesk.md](docs/JobDesk.md)

После изменения парсеров или версии:

```bash
python tools/update_docs.py
```

## Запуск (десктоп)

```bash
pip install -r requirements.txt
python main.py
```

Данные: `%LOCALAPPDATA%\JobDesk\jobdesk.db`

## Запуск (веб: Laravel + Vue SPA)

Инструкция: [docs/WEB.md](docs/WEB.md)

```bash
# API
cd backend && composer install && php artisan migrate && php artisan serve

# SPA (другой терминал)
cd frontend && npm install && npm run dev
```

Откройте http://localhost:5173 — без входа доступны только логин и регистрация; интерфейс JobDesk после авторизации.

## Подключённые источники (20)

| Регион | Сайт | ID в приложении |
|--------|------|-----------------|
| RU | Хабр Карьера RSS / HTML | `habr_rss`, `habr_html` |
| RU | hh.ru HTML | `hh_html` |
| RU | hh.ru API | `hh_api` |
| RU | Zarplata.ru | `zarplata_html` |
| RU | SuperJob | `superjob_html` |
| RU | Rabota.ru | `rabota_html` |
| RU | Работа России (Трудвсем API) | `trudvsem_api` |
| RU | GeekJob | `geekjob_html` |
| UA | DOU HTML / RSS | `dou_html`, `dou_rss` |
| UA | Djini | `djini_html` |
| BY | Dev.by | `devby_html` |
| World | Remote OK, Remotive, Jobicy, Arbeitnow, Himalayas | `*_api` |
| World | We Work Remotely RSS | `wwr_rss` |
| Any | Произвольный RSS | `rss_custom` |

Подсказки по полю «Запрос» — во вкладке **Источники** в приложении.

### HeadHunter API

Если `hh_api` отвечает 403, задайте переменную окружения (как требует [документация hh.ru](https://github.com/hhru/api)):

```powershell
$env:JOBDESK_HH_USER_AGENT = "JobDesk/1.0 (your@email.com)"
```

Или используйте источник **HeadHunter (HTML)**.

### Пока без встроенного парсера

Getmatch, LinkedIn, Indeed, Jooble — SPA/антибот. Их можно подключить через **Произвольный RSS**, если есть готовая лента.

## Новый сайт

Класс-парсер в `jobdesk/parsers/` + `register.py` + `source_notes.py` + `python tools/update_docs.py`.
