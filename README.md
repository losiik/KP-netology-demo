# Коммерческие предложения — учебное демо

Менеджер агентства вводит согласованные с клиентом данные, получает черновик КП,
правит его, сохраняет в личную историю и копирует для отправки.

На этом этапе **ИИ не подключён**: черновик собирается на сервере из обычного
текстового шаблона. Всё работает локально, без внешних сервисов и API-ключей.

- Бэкенд: Python 3.12, FastAPI, SQLite (встроенный `sqlite3`)
- Фронтенд: React + Vite

## Запуск

Нужны Python 3.10+ и Node.js 18+. Команды — из корня проекта.

### 1. Бэкенд (терминал 1)

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

### 2. Фронтенд (терминал 2)

```bash
cd frontend
npm install
npm run dev
```

### 3. Открыть в браузере

**http://localhost:5173**

Vite проксирует запросы `/api/*` на бэкенд `http://127.0.0.1:8000`.

> Вариант «одной командой»: выполнить `npm run build` в `frontend`, затем запустить
> только бэкенд — интерфейс будет доступен на http://localhost:8000.
> Для демонстрации правок в Cursor удобнее режим разработки (порт 5173) — он обновляется сразу.

## Учебные аккаунты

| Пользователь  | Логин   | Пароль     |
|---------------|---------|------------|
| Анна Смирнова | `anna`  | `anna123`  |
| Борис Петров  | `boris` | `boris123` |

На странице входа есть кнопки, которые подставляют эти данные.
Аккаунты создаются автоматически при первом запуске бэкенда.

## Где что лежит

| Что | Файл |
|-----|------|
| **Форма** «Новое предложение» | [frontend/src/components/OfferForm.jsx](frontend/src/components/OfferForm.jsx) |
| **Обработчик создания черновика** `POST /api/drafts` | [backend/app/drafts.py](backend/app/drafts.py) |
| **Шаблон** — функция `build_template_draft` | [backend/app/template.py](backend/app/template.py) |
| Проверка полей и расчёт суммы | [backend/app/offers.py](backend/app/offers.py) |
| Сохранение и чтение документов (с проверкой владельца) | [backend/app/documents.py](backend/app/documents.py) |
| Вход и сессии | [backend/app/auth.py](backend/app/auth.py) |
| База SQLite: схема и учебные аккаунты | [backend/app/db.py](backend/app/db.py) |
| Страница предложения: форма + редактор | [frontend/src/pages/OfferPage.jsx](frontend/src/pages/OfferPage.jsx) |
| Редактор черновика | [frontend/src/components/DraftEditor.jsx](frontend/src/components/DraftEditor.jsx) |
| История | [frontend/src/pages/HistoryPage.jsx](frontend/src/pages/HistoryPage.jsx) |
| Данные кнопки «Подставить пример» | [frontend/src/offerFields.js](frontend/src/offerFields.js) |

### Как устроено создание черновика

```
OfferForm ──POST /api/drafts──▶ drafts.create_draft
                                  ├─ validate_offer_fields()   проверка полей и цен
                                  ├─ calculate_total()         сумма считается на сервере
                                  └─ build_template_draft()    текст из шаблона
                         ◀── { text, total, fields } ── в редактор (в базу НЕ пишется)

«Сохранить» ──POST /api/documents (первый раз) / PUT /api/documents/{id} (повторно)
```

Следующий этап — заменить `build_template_draft` на вызов модели.
Форма, проверка полей и хранение документов при этом не меняются.

## API

| Метод | Путь | Что делает |
|-------|------|------------|
| POST | `/api/auth/login` | вход, возвращает токен |
| POST | `/api/auth/logout` | выход |
| GET  | `/api/auth/me` | текущий пользователь |
| POST | `/api/drafts` | проверить поля, посчитать сумму, собрать текст по шаблону |
| GET  | `/api/documents` | история текущего пользователя |
| POST | `/api/documents` | сохранить новый документ |
| GET  | `/api/documents/{id}` | открыть документ (чужой → 404) |
| PUT  | `/api/documents/{id}` | сохранить новую редакцию (чужой → 404) |

Интерактивная документация: http://localhost:8000/docs

## Данные

Документы хранятся в `backend/data/kp.sqlite3` (создаётся автоматически, в Git не попадает).
Исходные поля формы и редактируемый текст лежат в разных колонках таблицы `documents`.

Чтобы начать демонстрацию «с чистого листа», остановите бэкенд и удалите этот файл.

## Тесты

```bash
cd backend
../.venv/bin/python -m pip install -r requirements-dev.txt   # Windows: ..\.venv\Scripts\python ...
../.venv/bin/python -m pytest
```

Тесты проверяют критерии готовности на уровне API: образец «Зерно» → 80 000 ₽,
разработка 60 000 ₽ → итог 90 000 ₽, другой клиент без условий, ошибки полей,
сохранение ручной правки и закрытость документов от второго пользователя.

## Сценарий проверки в браузере

1. Войти как `anna`, нажать «Подставить пример» → «Создать черновик». Итого 80 000 ₽, срок 15 рабочих дней, предоплата 50%.
2. Поменять цену разработки на 60 000 → «Создать черновик». Итого 90 000 ₽.
3. Дописать что-нибудь в редакторе → «Сохранить». Обновить страницу (F5) — правка на месте.
4. «Скопировать текст» → появляется «Текст скопирован», в буфере — отредактированный текст.
5. «Новое предложение» → очистить поле «Клиент» → «Создать черновик». Ошибка у поля, остальные данные на месте.
6. Выйти, войти как `boris`, открыть ссылку на документ Анны (например `/documents/1`) → «Документ недоступен».

## Что сознательно не входит в этот этап

Вызов модели, промпт, API-ключи и выбор провайдера — следующий этап.
CRM, PDF, автоматическая отправка предложений и платежи — вне рамок проекта.
