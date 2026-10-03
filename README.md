# FitBuddy — AI Fitness Plan Generator

## What is FitBuddy?

FitBuddy is an **AI-powered personalized fitness planning web application** that uses Google Gemini to generate customized 7-day workout plans based on individual user information.

The application is designed to provide a complete fitness-planning experience instead of a generic workout routine.

A user can create an account, provide a detailed fitness assessment, receive a personalized 7-day workout plan, view nutrition and recovery guidance, complete daily workouts, submit feedback, receive an updated plan, track progress, and view previous plans.

FitBuddy also provides a protected **Admin / Coach Monitoring Dashboard** for monitoring registered users, workout plans, feedback, progress, and workout completion.

## 🌐 Project Links

**Live Demo:**  
https://fitbuddy-ai-fitness-plan-generator-pe4k.onrender.com

**GitHub Repository:**  
https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator

**Live API Documentation:**  
https://fitbuddy-ai-fitness-plan-generator-pe4k.onrender.com/docs

**Local Application:**  
http://127.0.0.1:8000

**Local API Documentation:**  
http://127.0.0.1:8000/docs

**Project README:**  
https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/README.md

**Testing Documentation:**  
https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/TESTING.md

**Requirements:**  
https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/requirements.txt

**Environment Template:**  
https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/.env.example

---

The project is built using:

- Python
- FastAPI
- Jinja2
- HTML
- CSS
- JavaScript
- SQLite
- SQLAlchemy
- Google Gemini
- Pydantic
- Uvicorn
- Pytest

---

# 📁 Project Folder

The complete FitBuddy project is organized as follows:


FitBuddy_Final_Enhanced_v2/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   ├── services.py
│   ├── ai_service.py
│   ├── errors.py
│   ├── templating.py
│   │
│   └── routes/
│       ├── __init__.py
│       ├── api.py
│       └── pages.py
│
├── templates/
│   ├── _macros.html
│   ├── admin.html
│   ├── admin_login.html
│   ├── base.html
│   ├── dashboard.html
│   ├── error.html
│   ├── feedback.html
│   ├── history.html
│   ├── landing.html
│   ├── login.html
│   ├── nutrition.html
│   ├── onboarding.html
│   ├── profile.html
│   ├── progress.html
│   ├── result.html
│   └── signup.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── tests/
│   ├── conftest.py
│   └── test_app.py
│
├── requirements.txt
├── pytest.ini
├── run.py
├── list_models.py
├── .env.example
├── .gitignore
├── README.md
└── TESTING.md
