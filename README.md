# AI Content Factory

Production-ready hackathon foundation for an AI content operations SaaS: FastAPI async backend, Next.js App Router frontend, OTP email verification, JWT auth, project CRUD, brandbook CRUD with logo upload, and multilingual UI in Kazakh, Russian, and English.

## Быстрый запуск на Windows

Нужен установленный и запущенный Docker Desktop.

1. Открой PowerShell в папке проекта `steppetech`.
2. Первый запуск или запуск после изменений:

```powershell
docker compose up --build
```

3. Открой в браузере:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

Остановить проект: нажми `Ctrl+C` в окне PowerShell.

Запустить уже собранный проект без пересборки:

```powershell
docker compose up
```

## Запуск без Docker

Открой два окна PowerShell.

В первом окне запусти backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
copy .env.example .env
uvicorn app.main:app --reload
```

Во втором окне запусти frontend:

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

После этого открой `http://localhost:3000`.

## Local Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
copy .env.example .env
uvicorn app.main:app --reload
```

The local default uses SQLite at `backend/storage/app.db` and creates tables on startup.

## Local Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## PostgreSQL Stack

```bash
docker compose up --build
```

Backend API: `http://localhost:8000`

Frontend: `http://localhost:3000`

## API Surface

Auth:

`POST /api/v1/auth/register`

`POST /api/v1/auth/verify-email`

`POST /api/v1/auth/login`

`GET /api/v1/auth/me`

Brandbooks:

`GET /api/v1/brandbooks`

`POST /api/v1/brandbooks`

`PUT /api/v1/brandbooks/{id}`

`DELETE /api/v1/brandbooks/{id}`

Projects:

`GET /api/v1/projects`

`POST /api/v1/projects`

`GET /api/v1/projects/{id}`

`DELETE /api/v1/projects/{id}`
