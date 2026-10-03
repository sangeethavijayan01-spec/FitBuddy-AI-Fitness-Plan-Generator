# FitBuddy — AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite/SQLAlchemy application that uses Google Gemini to generate personalized 7-day workout plans, nutrition/recovery guidance, feedback-based revisions, user history, progress tracking and a protected admin/coach view.

## Features
- Account signup/login/logout with signed sessions and password hashing
- Private user ownership checks
- Deep fitness assessment
- Structured Gemini output with Pydantic validation
- Safe local fallback when Gemini is unavailable
- Professional 7-day plan UI (not a raw AI `<pre>` dump)
- Nutrition, hydration and recovery guidance
- Feedback controls + preserved original plan + feedback history
- User history and progress records
- Protected admin/coach dashboard
- FastAPI `/docs` and JSON APIs
- Responsive desktop/tablet/mobile UI
- Windows PowerShell setup
- No secrets in the repository

## Architecture
FastAPI → route/service layer → SQLAlchemy/SQLite; Gemini is server-side only; Jinja2 renders the UI.

## Requirements
Python 3.11+ is recommended on Windows. Python 3.11 is a safe choice for college/demo environments.

## Windows PowerShell setup
```powershell
py -3.11 -m venv venv
.env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python run.py
```
Open http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

If PowerShell blocks activation, use:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.env\Scripts\Activate.ps1
```

## Gemini setup
Create a Gemini API key in Google AI Studio. Put it only in `.env`:
```text
GEMINI_API_KEY=your_real_key
GEMINI_MODEL=gemini-3.8-flash
```
Gemini 3.8 Flash is the default production model in this version. It is configurable through `.env`; do not commit `.env`.

The app uses Google's current `google-genai` SDK and structured JSON output. If Gemini is unavailable, FitBuddy logs the problem and displays a clearly conservative fallback plan rather than crashing.


## New product features

- Personalized 7-day workout + daily food habits (breakfast, lunch, snack and dinner)
- Approximate daily food calories, protein and fibre for each suggested meal
- Searchable nutrition library covering familiar fruits, vegetables, rice/grains and protein foods
- Professional progress cockpit with weight, workout-completion, energy and difficulty check-ins
- Dedicated admin/coach login and monitoring console
- Admin user count, plan count, AI-update count and progress-check-in count
- Admin per-user monitoring of profile, plans, feedback and progress history
- Original plan preservation alongside feedback-updated plans
- Animated responsive UI with mobile layouts and interactive food filters

## Admin setup
Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`. The environment admin is a separate protected monitoring account. Use the **Coach / Admin** link or `/admin/login` for the web console; the normal user `/login` is intentionally separate. For a demo, use:
```text
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-own-admin-password
```
The admin dashboard never displays passwords or authentication secrets.

## API
- `GET /api/health`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/me`
- `POST /api/assessment`
- `POST /api/plans`
- `GET /api/plans/{plan_id}`
- `POST /api/plans/{plan_id}/feedback`
- `GET /api/history`
- `POST /api/progress`
- `GET /api/progress`
- `GET /api/admin/users`

## Database
SQLite is the default and `fitbuddy.db` is created automatically. Tables include users, profiles, fitness_assessments, workout_plans, plan_feedback and progress_records. User IDs are used on all private records and every page/API checks ownership.

## Testing
With the virtual environment active:
```powershell
pytest
```
The test suite uses a temporary SQLite database and mocks Gemini, so it does not require a real API key.

## Troubleshooting
- `ModuleNotFoundError`: activate `venv` and run `python -m pip install -r requirements.txt`.
- Gemini configuration errors: check `.env`, restart the server, and confirm `GEMINI_MODEL`.
- Old local database: stop the server and delete `fitbuddy.db` for a clean demo database.
- Port busy: `$env:PORT=8001; python run.py`.

## Security
Never commit `.env`, real API keys, passwords or tokens. `.gitignore` excludes secrets and local databases. Passwords are salted and hashed with Python's scrypt. Session cookies are HTTP-only and SameSite=Lax. Fitness data is private to the signed-in user.

## Wellness disclaimer
FitBuddy provides general fitness and wellness guidance and is not a substitute for professional medical advice. User-reported limitations are not diagnosed by the application; seek appropriate professional advice where relevant.

## Project structure
```text
fitbuddy/
├── app/
│   ├── main.py config.py database.py models.py schemas.py security.py
│   ├── ai_service.py services.py errors.py templating.py
│   └── routes/ api.py pages.py
├── templates/
├── static/css/style.css
├── static/js/app.js
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── run.py
```

## UI and access behavior

- There is one login page for everyone. The configured `ADMIN_USERNAME` + `ADMIN_PASSWORD` are recognized by the same `/login` form and redirect directly to `/admin`.
- There is no Admin/Coach login link on public login or signup pages.
- Food Guide is shown only to authenticated users and authenticated admins, not to public login/signup visitors.
- Admin navigation is shown only while an admin session is active. Normal user profiles cannot open the admin console.
- Navigation highlights only the page currently being viewed.
- Every generated 7-day plan includes a day-by-day completion checklist. Checking a day saves immediately and recalculates weekly completion.
- Admin monitoring shows the latest plan's seven-day completion state and percentage.
- Feedback has a dedicated, structured adjustment interface. Original plans remain preserved while updated versions and feedback history are stored.
- Food Guide contains a larger reference library covering fruits, vegetables, staples, protein foods and drinks with approximate serving, calories, protein and fibre values.
