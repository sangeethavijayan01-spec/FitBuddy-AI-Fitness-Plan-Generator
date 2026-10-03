# FitBuddy — AI Fitness Plan Generator

## 1. Project Name

# FitBuddy — AI Fitness Plan Generator

FitBuddy is an **AI-powered personalized fitness planning web application** that uses Google Gemini to generate customized 7-day workout plans based on the user's fitness information.

The application combines **Python, FastAPI, Jinja2, HTML, CSS, JavaScript, SQLite, SQLAlchemy, Pydantic, and Google Gemini** into one complete fitness planning system.

FitBuddy is designed to provide a personalized workout experience rather than a fixed or generic workout routine.

---

# 2. Project Description

FitBuddy collects detailed fitness and lifestyle information from the user and uses that information to create a personalized 7-day workout plan.

The system can provide:

- Personalized workout plans
- Daily workout schedules
- Warm-up guidance
- Main exercises
- Sets and repetitions
- Workout duration
- Rest guidance
- Cool-down
- Recovery guidance
- Nutrition guidance
- Daily food habits
- Daily workout completion tracking
- User feedback
- Updated workout plans
- Original plan preservation
- Workout history
- Progress tracking
- Food Guide
- Admin / Coach monitoring

The application is built as a complete web application with a FastAPI backend, Jinja2 frontend, SQLite database, and Google Gemini AI integration.

---

# 3. User Inputs

FitBuddy collects the following information from the user during the fitness assessment.

### Personal Information

- Name
- Username
- Age
- Height
- Weight

### Fitness Information

- Fitness goal
- Workout experience
- Activity level
- Workout intensity
- Workout location
- Available equipment

### Schedule Information

- Days available per week
- Workout duration
- Preferred workout time

### Nutrition and Recovery Information

- Dietary preference
- Allergies / restrictions
- Sleep hours
- Rest-day preference

### Exercise Preference

- Exercises the user enjoys
- Exercises the user wants to avoid

### Limitation Information

- User-reported exercise limitations

The limitation field is treated as user-reported information and is not used as a medical diagnosis.

---

# 4. How FitBuddy Works

The application follows this sequence:

### Step 1 — Create Account

The user creates an account using:

- Name
- Username
- Email
- Password
- Confirm password

### Step 2 — Login

The user logs into FitBuddy using their account credentials.

### Step 3 — Fitness Assessment

The user completes the detailed fitness assessment.

### Step 4 — Generate Plan

The application takes the assessment information and sends the relevant information to the AI service.

### Step 5 — Gemini AI Processing

Google Gemini processes the user's fitness information and generates a structured 7-day workout plan.

### Step 6 — Validation

The generated structured response is validated using Pydantic.

### Step 7 — Database Storage

The workout plan and related information are stored using SQLAlchemy and SQLite.

### Step 8 — Display Personalized Plan

The user receives a structured 7-day workout plan through the Jinja2 web interface.

### Step 9 — Daily Workout Completion

The user can mark individual workout days as completed.

### Step 10 — Feedback

The user can provide feedback about:

- Workout difficulty
- Energy
- Cardio
- Strength
- Rest
- Session duration
- Home / gym preference
- Stretching
- Additional requirements

### Step 11 — Updated Plan

The feedback is processed and used to generate an updated version of the plan.

### Step 12 — Progress Tracking

The user can record:

- Weight
- Workout completion
- Energy
- Difficulty
- Notes

### Step 13 — History

Previous workout plans remain available in the user's History section.

### Step 14 — Admin Monitoring

The protected administrator dashboard can monitor users, plans, feedback, progress, and workout completion.

---

# 5. 🔗 Project Links

## Live Application

https://fitbuddy-ai-fitness-plan-generator-pe4k.onrender.com

## GitHub Repository

https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator

## Live API Documentation

https://fitbuddy-ai-fitness-plan-generator-pe4k.onrender.com/docs

## Local Application

http://127.0.0.1:8000

## Local API Documentation

http://127.0.0.1:8000/docs

## Project README

https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/README.md

## Testing Documentation

https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/TESTING.md

## Requirements File

https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/requirements.txt

## Environment Template

https://github.com/sangeethavijayan01-spec/FitBuddy-AI-Fitness-Plan-Generator/blob/main/.env.example

---

# 6. 📚 Project Reference Document

The project was developed using the reference document:

**FitBuddy – AI Fitness Plan Generator using Gemini Models**

The reference document defines the original FitBuddy concept and its main scenarios:

### Scenario 1

User provides personal information and the system generates a personalized 7-day workout plan.

### Scenario 2

User provides feedback such as:

- More cardio
- More rest days

The system updates the workout plan according to the feedback.

### Scenario 3

The system provides nutrition or recovery guidance based on the user's fitness goal.

### Scenario 4

An administrator or coach can view registered users, workout plans, progress, and activity.

The reference architecture uses:

- HTML
- CSS
- Jinja2
- FastAPI
- Google Gemini
- SQLite
- SQLAlchemy

These core concepts were preserved in the final FitBuddy application. :contentReference[oaicite:2]{index=2}

---

# 7. 🛠️ What We Implemented from the Project Document

The original reference document provided the foundation of the project.

The final application keeps those core requirements and extends them into a more complete application.

## Original Functions Implemented

- Personalized 7-day workout generation
- Workout warm-up
- Main workout
- Sets and repetitions
- Cool-down / recovery guidance
- Nutrition guidance
- Feedback-based plan updates
- Original plan preservation
- Updated plan storage
- User and plan storage
- Admin / Coach monitoring
- FastAPI backend
- Jinja2 frontend
- Google Gemini integration
- SQLite / SQLAlchemy database

These functions correspond to the original project specification. :contentReference[oaicite:3]{index=3}

## Additional Functions Implemented

### Authentication

- Signup
- Login
- Logout
- Password hashing
- Session authentication
- Protected pages
- Admin protection

### Deep Fitness Assessment

The original basic input collection was expanded into a more detailed fitness assessment for personalization.

### Structured AI Output

Instead of displaying raw AI text, the application uses structured data and Pydantic validation.

### Local AI Fallback

A local fallback mechanism was added so the application can continue operating when Gemini is temporarily unavailable.

### Enhanced Workout Interface

The original workout result concept was expanded into a structured day-by-day interface.

### Feedback Interface

A dedicated feedback interface was added with structured adjustment options.

### Plan History

A separate History section was added.

### Progress Tracking

A complete Progress section was added for user-entered progress information.

### Daily Completion

A seven-day workout checklist was added with automatic completion percentage.

### Food Guide

A searchable food reference library was added.

### Enhanced Admin Dashboard

The original admin concept was expanded into a monitoring dashboard.

### Responsive Design

The application was enhanced for desktop, tablet, and mobile screen sizes.

---

# 8. 🧰 Technologies and Libraries Used

| Area | Technology / Library |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| ASGI Server | Uvicorn |
| Frontend | HTML, CSS, JavaScript |
| Template Engine | Jinja2 |
| Database | SQLite |
| ORM | SQLAlchemy |
| AI Platform | Google Gemini |
| Gemini SDK | google-genai |
| Data Validation | Pydantic |
| Environment Configuration | python-dotenv |
| Authentication Sessions | itsdangerous / Starlette Sessions |
| Password Security | Python scrypt |
| HTTP Client / Testing Support | httpx |
| Multipart Form Handling | python-multipart |
| Testing Framework | Pytest |
| Version Control | Git |
| Repository Hosting | GitHub |
| Deployment | Render |

---

                         ┌───────────────────────┐
                         │         USER          │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     JINJA2 WEB UI     │
                         │    HTML / CSS / JS    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │       FASTAPI         │
                         │      ROUTE LAYER      │
                         └───────────┬───────────┘
                                     │
                   ┌─────────────────┼─────────────────┐
                   │                 │                 │
                   ▼                 ▼                 ▼
          ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
          │ SERVICE LAYER  │ │ SECURITY     │ │   JSON API   │
          └───────┬────────┘ └──────────────┘ └──────────────┘
                  │
                  ▼
          ┌──────────────────┐
          │   GOOGLE GEMINI  │
          │     AI LAYER     │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ PYDANTIC         │
          │ VALIDATION       │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ SQLALCHEMY ORM   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ SQLITE DATABASE  │
          └──────────────────┘

Application  Flow

                      START
                        │
                        ▼
                ┌───────────────┐
                │    SIGNUP     │
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │     LOGIN     │
                └───────┬───────┘
                        │
                        ▼
              ┌───────────────────┐
              │ FITNESS ASSESSMENT│
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ GENERATE PLAN     │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │   GOOGLE GEMINI   │
              │   AI PROCESSING   │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ STRUCTURED 7-DAY  │
              │ WORKOUT PLAN      │
              └─────────┬─────────┘
                        │
              ┌─────────┼──────────┐
              │         │          │
              ▼         ▼          ▼
           WORKOUT   NUTRITION   RECOVERY
              │
              ▼
       DAILY COMPLETION
              │
              ▼
          FEEDBACK
              │
              ▼
       GEMINI PLAN UPDATE
              │
              ▼
        UPDATED PLAN
              │
              ▼
      PROGRESS TRACKING
              │
              ▼
          HISTORY

AI WorkFlow

User Fitness Information
          │
          ▼
   Personalized Prompt
          │
          ▼
     Google Gemini
          │
          ▼
  Structured AI Output
          │
          ▼
 Pydantic Validation
          │
          ▼
    Service Layer
          │
          ▼
 SQLite Database
          │
          ▼
 Jinja2 Result Page

 Admin Monitoring Flow

 Admin Login
     │
     ▼
Admin Dashboard
     │
     ├──────────────► Registered Users
     │
     ├──────────────► Workout Plans
     │
     ├──────────────► Feedback
     │
     ├──────────────► Progress Records
     │
     └──────────────► Workout Completion

# 9. 📁 Complete Project Folder

Feedback Workflow
Current Workout Plan
          │
          ▼
     User Feedback
          │
          ▼
Difficulty / Energy /
Workout Preferences
          │
          ▼
     Google Gemini
          │
          ▼
    Updated Plan
          │
          ▼
  Database Storage
          │
          ▼
 Updated Result Page

The main project folder is:

```text
FitBuddy_Final_Enhanced_v2/
