# CRM — Договоры и документооборот

Веб-CRM для ведения клиентов, договоров, оплат и документов. Табличный минималистичный интерфейс 

## Стек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, JWT |
| Frontend | React, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Infra | Docker, docker-compose, nginx |

## Структура

```
CRM/
├── backend/          # API
├── frontend/         # SPA
├── docker/           # nginx config
└── docker-compose.yml
```

## Ошибка авторизации / «Сервер недоступен»

Чаще всего причина в том, что **запущен только frontend**, а **backend не работает**.

1. В терминале Vite будет: `http proxy error: ECONNREFUSED` — это значит, API на порту **8000** не отвечает.
2. Нужны **два процесса**: backend (8000) и frontend (5173).

**Windows (PowerShell):**

```powershell
# Терминал 1 — backend
.\scripts\start-backend.ps1

# Терминал 2 — frontend
cd frontend
npm run dev
```

Перед первым запуском отредактируйте `backend/.env`: укажите `DATABASE_URL` с **вашим** логином и паролем PostgreSQL.  
По умолчанию в примере `crm:crm` — так работает только контейнер из docker-compose.  
Если Postgres установлен локально, создайте БД и пользователя или используйте существующего пользователя, например:

```sql
CREATE DATABASE crm;
CREATE USER crm WITH PASSWORD 'crm';
GRANT ALL PRIVILEGES ON DATABASE crm TO crm;
```

Либо в `.env`:

```
DATABASE_URL=postgresql+asyncpg://postgres:ВАШ_ПАРОЛЬ@localhost:5432/crm
```

После успешного старта backend откройте http://localhost:8000/api/health — должно быть `{"status":"ok"}`.  
Затем зарегистрируйтесь на http://localhost:5173/register или создайте админа:

```bash
cd backend
python -m scripts.seed_admin admin@example.com admin123
```

---

## Деплой на Railway

Один веб-сервис (API + фронтенд) и PostgreSQL.

1. Закоммитьте и запушьте репозиторий на GitHub.
2. [railway.app](https://railway.app) → New Project → **Deploy from GitHub repo**.
3. В настройках сервиса: **Builder = Dockerfile** (не Railpack). Root Directory оставьте пустым (корень репо).
4. **+ Add** → **Database** → **PostgreSQL**.
5. Variables веб-сервиса:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
   - `SECRET_KEY` = длинная случайная строка
   - `UPLOAD_DIR` = `/app/uploads`
6. **Generate Domain** — это URL CRM.
7. В Railway → сервис → **Shell** / one-off:

```bash
python -m scripts.seed_admin admin@example.com ваш_пароль
```

Загрузки без Volume пропадают при редеплое. При необходимости Volume на `/app/uploads`.

---

## Быстрый старт (Docker)

```bash
docker compose up --build -d
```

Приложение: http://localhost

Создать администратора:

```bash
docker compose exec backend python -m scripts.seed_admin admin@example.com yourpassword
```

## Локальная разработка

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
# Запустить PostgreSQL (или docker compose up postgres -d)
uvicorn app.main:app --reload --port 8000
python -m scripts.seed_admin
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173 (прокси `/api` → backend)

## Роли

| Роль | Права |
|------|-------|
| **ADMIN** | Полный доступ, удаление |
| **MANAGER** | Редактирование своих клиентов / ответственных договоров; чужие — только просмотр |
| **VIEWER** | Только просмотр |

## API (основное)

- `POST /api/auth/login`, `/register`, `/refresh`
- `GET /api/auth/me`
- `GET/POST/PUT/DELETE /api/clients`
- `GET/POST/PUT/DELETE /api/contracts` — фильтры в query params
- `GET/POST/PUT /api/payments`
- `POST /api/documents/generate`, `/upload`, `GET /api/documents/{id}`
- `GET /api/dashboard`

### Фильтрация договоров

```
GET /api/contracts?contract_status=OPEN&payment_status=NOT_PAID&production_status=SCAN
GET /api/contracts?search=ООО&client_id=1&contract_number=2024
```

## Закрытие договора

Договор можно закрыть (`CLOSED`) только если:

- `payment_status = PAID`
- `production_status = READY`
- есть документы типов **CONTRACT** и **ACT**

## DaData (find-party / find-bank)

1. Зарегистрируйтесь на [dadata.ru](https://dadata.ru/) и получите API-ключ.
2. В `backend/.env`:
   ```
   DADATA_API_KEY=ваш_токен
   ```
3. При импорте Word подгружаются **организация** по ИНН/ОГРН ([find-party](https://dadata.ru/api/find-party/)) и **банк** по БИК ([find-bank](https://dadata.ru/api/find-bank/)).
4. **Ручной ввод**: блок «Подгрузка из DaData» — ИНН (с КПП для филиала), ОГРН или кнопка «Организация»; БИК → банк. API: `GET /api/clients/lookup-party/{query}`, `GET /api/clients/lookup-inn/{inn}` (алиас).
5. **Р/с** (расчётный счёт клиента) DaData не выдаёт — вводите вручную или из Word.

## Миграция: реквизиты клиента (если БД уже создана)

После обновления кода выполните один раз:

```bash
cd backend
python -m scripts.migrate_client_requisites
```

## MVP этапы

- **Этап 1** ✅ — auth, роли, клиенты, договоры, RBAC
- **Этап 2** ✅ — оплаты, документы, DOCX-генерация
- **Этап 3** — PDF, расширенный audit, уведомления

## Переменные окружения

См. `backend/.env.example`.
