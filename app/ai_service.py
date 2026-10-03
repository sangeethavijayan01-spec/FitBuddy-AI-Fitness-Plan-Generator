"""Gemini integration with structured output, validation, retries and safe fallback."""

import json
import logging

from . import config
from .errors import AIConfigError, AIRequestError, AIResponseError
from .schemas import WorkoutPlanData, AssessmentInput, MealSuggestion


logger = logging.getLogger("fitbuddy.ai")

_ACTIVE_PROFILE: AssessmentInput | None = None


# ============================================================
# PROFILE HELPER
# ============================================================

def _profile_text(p: AssessmentInput) -> str:
    """Convert the assessment profile into readable JSON text."""

    return json.dumps(
        p.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# PLAN VALIDATION
# ============================================================

def _validate(plan: WorkoutPlanData) -> WorkoutPlanData:
    """Validate that the AI returned a complete 7-day plan."""

    if len(plan.days) != 7:
        raise AIResponseError(
            "The AI returned an invalid 7-day schedule."
        )

    if [day.day for day in plan.days] != list(range(1, 8)):
        raise AIResponseError(
            "The AI returned invalid day numbering."
        )

    if not plan.summary.strip():
        raise AIResponseError(
            "The AI returned an incomplete plan."
        )

    if not plan.nutrition_tip.strip():
        raise AIResponseError(
            "The AI returned an incomplete nutrition tip."
        )

    return plan


# ============================================================
# FOOD LIBRARY
# ============================================================

FOOD_LIBRARY = {
    "Vegetarian": [
        (
            "Breakfast",
            "Oats with banana + curd",
            "1 bowl",
            320,
            12,
            7,
        ),
        (
            "Lunch",
            "Rice + dal + mixed vegetables",
            "1 plate",
            520,
            18,
            9,
        ),
        (
            "Snack",
            "Guava + roasted peanuts",
            "1 guava + 20 g",
            190,
            7,
            6,
        ),
        (
            "Dinner",
            "2 chapatis + paneer + salad",
            "2 chapatis + 100 g",
            460,
            24,
            8,
        ),
    ],
    "Vegan": [
        (
            "Breakfast",
            "Oats + banana + peanut butter",
            "1 bowl",
            360,
            11,
            8,
        ),
        (
            "Lunch",
            "Rice + lentil dal + vegetables",
            "1 plate",
            500,
            18,
            10,
        ),
        (
            "Snack",
            "Orange + roasted chickpeas",
            "1 orange + 40 g",
            210,
            9,
            8,
        ),
        (
            "Dinner",
            "Chapati + tofu + vegetable salad",
            "2 chapatis + 120 g",
            430,
            23,
            9,
        ),
    ],
    "Non-vegetarian": [
        (
            "Breakfast",
            "2 eggs + oats + banana",
            "2 eggs + 1 bowl",
            390,
            22,
            6,
        ),
        (
            "Lunch",
            "Rice + chicken + vegetables",
            "1 plate + 120 g",
            560,
            38,
            7,
        ),
        (
            "Snack",
            "Apple + curd",
            "1 apple + 150 g",
            180,
            7,
            5,
        ),
        (
            "Dinner",
            "Chapati + fish + salad",
            "2 chapatis + 120 g",
            470,
            34,
            7,
        ),
    ],
    "Other": [
        (
            "Breakfast",
            "Oats + fruit + a protein source",
            "1 bowl",
            350,
            15,
            7,
        ),
        (
            "Lunch",
            "Rice + dal + vegetables",
            "1 plate",
            520,
            18,
            9,
        ),
        (
            "Snack",
            "Seasonal fruit + nuts",
            "1 serving",
            200,
            6,
            5,
        ),
        (
            "Dinner",
            "Chapati + protein source + salad",
            "2 chapatis + 1 serving",
            450,
            22,
            8,
        ),
    ],
}


def _food_habits(
    p: AssessmentInput,
    day: int,
):
    """Return four food suggestions for the selected dietary preference."""

    dietary_preference = p.dietary_preference.value

    # Use Other if an unexpected dietary value appears.
    items = FOOD_LIBRARY.get(
        dietary_preference,
        FOOD_LIBRARY["Other"],
    )

    # Rotate the familiar foods slightly across the week.
    rotation = (day - 1) % len(items)
    rotated = items[rotation:] + items[:rotation]

    return [
        {
            "meal": meal,
            "food": food,
            "portion": portion,
            "calories": calories,
            "protein_g": protein,
            "fiber_g": fiber,
        }
        for meal, food, portion, calories, protein, fiber in rotated
    ]


def _add_food_habits(
    plan: WorkoutPlanData,
    p: AssessmentInput,
) -> WorkoutPlanData:
    """Ensure every day has food suggestions."""

    for day in plan.days:
        if not day.meals:
            day.meals = [
                MealSuggestion(**item)
                for item in _food_habits(p, day.day)
            ]

    return plan


# ============================================================
# SAFE FALLBACK PLAN
# ============================================================

def _fallback(
    p: AssessmentInput,
    reason: str = "",
) -> WorkoutPlanData:
    """
    Build a deterministic fallback plan that still uses
    the user's assessment.

    Gemini can temporarily be unavailable, for example HTTP 503.
    The fallback must never collapse every user into the same
    generic workout.
    """

    goal = p.goal.value
    experience = p.experience.value
    location = p.location.value
    intensity = p.intensity.value
    equipment = p.equipment.strip()
    preference = p.exercise_preferences.strip()
    limitation = p.limitations.strip()

    # --------------------------------------------------------
    # Select focus based on the user's goal
    # --------------------------------------------------------

    if goal == "Weight Loss":
        focus_pool = [
            "Full Body Conditioning",
            "Lower Body + Cardio",
            "Upper Body + Cardio",
            "Core + Conditioning",
        ]

    elif goal == "Muscle Gain":
        focus_pool = [
            "Full Body Strength",
            "Lower Body Hypertrophy",
            "Upper Body Hypertrophy",
            "Full Body Strength",
        ]

    elif goal == "Strength":
        focus_pool = [
            "Strength Foundation",
            "Lower Body Strength",
            "Upper Body Strength",
            "Full Body Strength",
        ]

    elif goal == "Endurance":
        focus_pool = [
            "Cardio Endurance",
            "Lower Body + Endurance",
            "Interval Conditioning",
            "Steady-State Endurance",
        ]

    elif goal == "Flexibility":
        focus_pool = [
            "Mobility + Flexibility",
            "Lower Body Mobility",
            "Upper Body Mobility",
            "Full Body Mobility",
        ]

    else:
        focus_pool = [
            "Full Body Fitness",
            "Lower Body + Cardio",
            "Upper Body + Core",
            "Full Body Fitness",
        ]

    # --------------------------------------------------------
    # Select exercises based on location/equipment
    # --------------------------------------------------------

    if (
        location == "Gym"
        or any(
            word in equipment.lower()
            for word in (
                "dumbbell",
                "barbell",
                "machine",
                "cable",
                "kettlebell",
            )
        )
    ):
        strength_exercises = [
            ("Goblet Squat", "8-12 reps"),
            ("Dumbbell Row", "8-12 reps"),
            ("Dumbbell Chest Press", "8-12 reps"),
            ("Romanian Deadlift", "8-10 reps"),
        ]

    elif location == "Outdoor":
        strength_exercises = [
            ("Bodyweight Squat", "10-15 reps"),
            ("Incline Push-up", "8-12 reps"),
            ("Walking Lunge", "8-12 reps each side"),
            (
                "Brisk Walk",
                f"{max(10, min(p.duration_minutes // 2, 30))} minutes",
            ),
        ]

    else:
        strength_exercises = [
            ("Bodyweight Squat", "10-15 reps"),
            ("Incline Push-up", "8-12 reps"),
            ("Glute Bridge", "10-15 reps"),
            ("Reverse Lunge", "8-12 reps each side"),
        ]

    # --------------------------------------------------------
    # Select cardio preference
    # --------------------------------------------------------

    if "walk" in preference.lower():
        cardio = "Brisk Walk"

    elif (
        "cycle" in preference.lower()
        or "bike" in preference.lower()
    ):
        cardio = "Cycling"

    else:
        cardio = (
            "Brisk Walk"
            if location != "Gym"
            else "Cardio Machine"
        )

    # --------------------------------------------------------
    # Determine number of sets
    # --------------------------------------------------------

    if experience == "Beginner":
        sets = 2

    elif experience == "Advanced":
        sets = 4

    else:
        sets = 3

    if intensity == "Low":
        sets = max(2, sets - 1)

    elif intensity == "High":
        sets = min(4, sets + 1)

    # --------------------------------------------------------
    # Determine active training days
    # --------------------------------------------------------

    requested_training_days = max(
        1,
        min(p.days_per_week, 7),
    )

    rest_days = 7 - requested_training_days

    active_days = []
    remaining = rest_days

    for day in range(1, 8):

        if (
            remaining
            and day in {2, 4, 6, 7}
            and len(active_days) >= 1
        ):
            remaining -= 1

        else:
            active_days.append(day)

    while len(active_days) > requested_training_days:
        active_days.pop()

    while len(active_days) < requested_training_days:
        for day in range(1, 8):

            if day not in active_days:
                active_days.append(day)

                if len(active_days) == requested_training_days:
                    break

    active_days = sorted(active_days)

    # --------------------------------------------------------
    # Build the seven-day schedule
    # --------------------------------------------------------

    days = []

    for day in range(1, 8):

        # ----------------------------------------------------
        # Rest day
        # ----------------------------------------------------

        if day not in active_days:

            days.append(
                {
                    "day": day,
                    "focus": "Recovery / Rest",
                    "is_rest_day": True,
                    "warm_up": (
                        "Gentle walking and mobility "
                        "for 5 minutes."
                    ),
                    "exercises": [],
                    "cooldown": (
                        "Easy breathing and gentle stretching "
                        "for 5 minutes."
                    ),
                    "recovery": (
                        f"Respect your rest preference "
                        f"({p.rest_preference}), hydrate, "
                        "and prioritize recovery."
                    ),
                    "meals": _food_habits(p, day),
                }
            )

            continue

        # ----------------------------------------------------
        # Active workout day
        # ----------------------------------------------------

        completed_active_days = len(
            [
                d
                for d in days
                if not d["is_rest_day"]
            ]
        )

        focus = focus_pool[
            completed_active_days % len(focus_pool)
        ]

        exercise_items = []

        offset = (day - 1) % len(strength_exercises)

        for j in range(3):

            name, reps = strength_exercises[
                (offset + j) % len(strength_exercises)
            ]

            exercise_items.append(
                {
                    "name": name,
                    "sets": sets,
                    "reps_or_duration": reps,
                    "rest": "45-90 sec",
                    "notes": (
                        f"{experience} level, "
                        f"{intensity.lower()} intensity; "
                        f"use {equipment} as available."
                    ),
                }
            )

        exercise_items.append(
            {
                "name": cardio,
                "sets": 1,
                "reps_or_duration": (
                    f"{max(10, min(p.duration_minutes // 3, 25))} "
                    "minutes"
                ),
                "rest": "As needed",
                "notes": (
                    f"Supports your {goal.lower()} goal."
                ),
            }
        )

        days.append(
            {
                "day": day,
                "focus": focus,
                "is_rest_day": False,
                "warm_up": (
                    "5-8 minutes of easy movement "
                    f"appropriate for {location.lower()} training."
                ),
                "exercises": exercise_items,
                "cooldown": (
                    "5 minutes of easy movement followed "
                    "by comfortable stretching."
                ),
                "recovery": (
                    f"Keep the session within about "
                    f"{p.duration_minutes} minutes and adjust "
                    f"effort to your {intensity.lower()} "
                    "intensity target. "
                    + (
                        f"Respect the stated limitation: "
                        f"{limitation}"
                        if limitation
                        else
                        "Stop an exercise if it causes pain "
                        "or unusual symptoms."
                    )
                ),
                "meals": _food_habits(p, day),
            }
        )

    # --------------------------------------------------------
    # Nutrition guidance
    # --------------------------------------------------------

    diet_note = {
        "Vegetarian": (
            "Include protein-rich vegetarian foods such as "
            "lentils, beans, dairy or suitable alternatives."
        ),
        "Vegan": (
            "Include varied plant protein sources such as "
            "lentils, beans, tofu and other fortified foods."
        ),
        "Non-vegetarian": (
            "Include a variety of protein sources alongside "
            "vegetables or fruit and whole-food carbohydrates."
        ),
        "Other": (
            "Choose balanced meals with a suitable protein "
            "source, vegetables or fruit, and whole-food "
            "carbohydrates."
        ),
    }.get(
        p.dietary_preference.value,
        "Choose balanced meals with suitable protein, "
        "vegetables or fruit, and whole-food carbohydrates.",
    )

    # --------------------------------------------------------
    # Return validated fallback plan
    # --------------------------------------------------------

    return WorkoutPlanData(
        summary=(
            f"Personalized {goal} starter plan for {p.name}: "
            f"{requested_training_days} training day(s) per week, "
            f"{p.duration_minutes} minutes per session, "
            f"{intensity.lower()} intensity."
        ),
        weekly_strategy=(
            f"Designed for a {experience.lower()} exerciser "
            f"training at {location.lower()} with {equipment}. "
            f"The schedule reflects the requested "
            f"{requested_training_days} training day(s) and "
            f"{p.rest_preference.lower()}."
        ),
        days=days,
        nutrition_tip=(
            diet_note
            + (
                f" Consider the stated restriction/allergy "
                f"information: {p.allergies}."
                if p.allergies
                else ""
            )
        ),
        hydration_tip=(
            "Drink fluids regularly through the day and "
            "around exercise, with extra attention in hot "
            "conditions."
        ),
        sleep_tip=(
            "Aim for a consistent sleep routine; your "
            f"assessment reports about {p.sleep_hours:g} "
            "hour(s) of sleep. Prioritize recovery when "
            "energy is low."
        ),
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

def _client():
    """Create and return the Google Gemini client."""

    try:
        from google import genai
        from google.genai import types

    except ImportError as exc:
        raise AIConfigError(
            "The Google GenAI SDK is not installed. "
            "Run: python -m pip install -r requirements.txt"
        ) from exc

    if not config.api_key_is_configured():
        raise AIConfigError(
            "Gemini API is not configured. "
            "Add GEMINI_API_KEY to .env."
        )

    return genai.Client(
        api_key=config.get_gemini_api_key(),
        http_options=types.HttpOptions(
            timeout=int(
                config.get_gemini_timeout_seconds() * 1000
            )
        ),
    )


def _generate(prompt: str):
    """Send a structured request to Gemini."""

    try:
        from google.genai import types, errors as genai_errors

    except ImportError as exc:
        raise AIConfigError(
            "The Google GenAI SDK is not installed. "
            "Run: python -m pip install -r requirements.txt"
        ) from exc

    client = _client()
    model = config.get_gemini_model()

    try:

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are FitBuddy, a fitness and wellness "
                    "planning assistant. Do not diagnose medical "
                    "conditions. Respect limitations. Create "
                    "practical, conservative plans. Return only "
                    "schema-compliant JSON."
                ),
                response_mime_type="application/json",
                response_schema=WorkoutPlanData,
            ),
        )

        # ----------------------------------------------------
        # Preferred structured response
        # ----------------------------------------------------

        parsed = getattr(
            response,
            "parsed",
            None,
        )

        if isinstance(parsed, WorkoutPlanData):

            if _ACTIVE_PROFILE is None:
                raise AIResponseError(
                    "The active assessment profile is missing."
                )

            return _add_food_habits(
                _validate(parsed),
                _ACTIVE_PROFILE,
            )

        # ----------------------------------------------------
        # Text JSON response fallback
        # ----------------------------------------------------

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            raise AIResponseError(
                "Gemini returned an empty response."
            )

        if _ACTIVE_PROFILE is None:
            raise AIResponseError(
                "The active assessment profile is missing."
            )

        parsed_plan = WorkoutPlanData.model_validate_json(
            text
        )

        return _add_food_habits(
            _validate(parsed_plan),
            _ACTIVE_PROFILE,
        )

    except genai_errors.APIError as exc:

        logger.error(
            "Gemini API error: %s",
            exc,
        )

        code = getattr(
            exc,
            "code",
            None,
        )

        if code in (401, 403):
            raise AIRequestError(
                "Gemini rejected the API key. "
                "Check GEMINI_API_KEY."
            ) from exc

        if code == 404:
            raise AIRequestError(
                f"The Gemini model '{model}' was not found. "
                "Change GEMINI_MODEL."
            ) from exc

        if code == 429:
            raise AIRequestError(
                "Gemini rate limit or quota was reached. "
                "Please try again later."
            ) from exc

        raise AIRequestError(
            "The Gemini service is temporarily unavailable. "
            "Please try again."
        ) from exc

    except AIResponseError:
        raise

    except Exception as exc:

        logger.exception(
            "Gemini generation failed"
        )

        raise AIRequestError(
            "Could not reach Gemini. "
            "A safe fallback can be used by the web workflow."
        ) from exc


# ============================================================
# GENERATE INITIAL WORKOUT PLAN
# ============================================================

def generate_workout_plan(
    profile: AssessmentInput,
):
    """Generate a new personalized 7-day workout plan."""

    global _ACTIVE_PROFILE

    _ACTIVE_PROFILE = profile

    prompt = f"""
Create a personalized 7-day fitness plan from this
structured profile:

{_profile_text(profile)}

Requirements:

- include overall goal
- include weekly strategy
- exactly Day 1-Day 7
- warm-up
- exercises with sets/reps or duration/rest
- cooldown
- recovery notes
- appropriate rest days
- nutrition guidance
- hydration guidance
- sleep guidance

For EVERY day include 4 practical food habit entries:

1. Breakfast
2. Lunch
3. Snack
4. Dinner

Each food entry must include:

- familiar food
- portion
- approximate calories
- protein grams
- fiber grams

Respect:

- dietary preference
- allergies
- restrictions
- days_per_week
- limitations

Keep food advice general and conservative.

Do not provide medical treatment.
"""

    try:

        return _generate(prompt)

    except (
        AIConfigError,
        AIRequestError,
        AIResponseError,
    ) as exc:

        logger.warning(
            "Using safe fallback plan: %s",
            exc,
        )

        return _fallback(
            profile,
            str(exc),
        )


# ============================================================
# FEEDBACK-AWARE FALLBACK
# ============================================================

def _feedback_fallback(
    profile: AssessmentInput,
    current,
    feedback: str,
) -> WorkoutPlanData:
    """
    Apply the user's feedback even when Gemini is temporarily
    unavailable.

    This is important because Gemini may return HTTP 503 during
    periods of high demand.

    Instead of creating a completely new generic plan, this
    function modifies the CURRENT plan using the actual feedback.
    """

    # --------------------------------------------------------
    # Convert current stored plan into WorkoutPlanData
    # --------------------------------------------------------

    try:

        if isinstance(current, WorkoutPlanData):
            plan = current

        elif isinstance(current, str):
            plan = WorkoutPlanData.model_validate_json(
                current
            )

        else:
            plan = WorkoutPlanData.model_validate(
                current
            )

    except Exception:

        plan = _fallback(
            profile,
            "invalid current plan",
        )

    # --------------------------------------------------------
    # Normalize feedback
    # --------------------------------------------------------

    text = (
        feedback or ""
    ).strip().lower()

    # --------------------------------------------------------
    # Detect common feedback requests
    # --------------------------------------------------------

    wants_cardio = "cardio" in text

    wants_strength = "strength" in text

    wants_rest = (
        "more rest" in text
        or "rest day" in text
        or "rest days" in text
    )

    wants_shorter = (
        "shorter" in text
        or "less time" in text
        or "reduce session" in text
        or "reduce workout" in text
    )

    wants_longer = (
        "longer" in text
        or "more time" in text
        or "increase session" in text
        or "increase workout" in text
    )

    wants_home = (
        "home" in text
        or "no equipment" in text
        or "without equipment" in text
    )

    wants_gym = "gym" in text

    wants_stretch = (
        "stretch" in text
        or "flexib" in text
        or "mobility" in text
    )

    too_easy = "too easy" in text

    too_hard = (
        "too difficult" in text
        or "too hard" in text
    )

    low_energy = (
        "low energy" in text
        or "tired" in text
        or "fatigue" in text
    )

    # --------------------------------------------------------
    # Make feedback visible in the plan summary
    # --------------------------------------------------------

    plan.summary = (
        f"Updated from feedback: "
        f"{feedback.strip()} | "
        f"{plan.summary}"
    )

    # --------------------------------------------------------
    # ADD MORE REST
    # --------------------------------------------------------

    active_days = [
        day
        for day in plan.days
        if not day.is_rest_day
    ]

    if wants_rest and active_days:

        day = active_days[-1]

        day.is_rest_day = True

        day.focus = (
            "Recovery / Rest (feedback adjustment)"
        )

        day.exercises = []

        day.warm_up = (
            "Gentle walking and mobility "
            "for 5 minutes."
        )

        day.cooldown = (
            "Easy breathing and comfortable "
            "stretching for 5 minutes."
        )

        day.recovery = (
            "Added a recovery day because your "
            "feedback requested more rest."
        )

    # --------------------------------------------------------
    # APPLY FEEDBACK TO ACTIVE DAYS
    # --------------------------------------------------------

    for day in plan.days:

        # ----------------------------------------------------
        # Rest days
        # ----------------------------------------------------

        if day.is_rest_day:

            if wants_stretch:

                day.recovery = (
                    "Recovery day with extra gentle "
                    "mobility and stretching, as requested."
                )

            continue

        # ----------------------------------------------------
        # HOME / NO EQUIPMENT
        # ----------------------------------------------------

        if wants_home:

            replacements = {
                "Dumbbell Row": "Backpack Row",
                "Dumbbell Chest Press": "Incline Push-up",
                "Goblet Squat": "Bodyweight Squat",
                "Romanian Deadlift": "Hip Hinge",
                "Cardio Machine": "Brisk Walk",
            }

            for exercise in day.exercises:

                exercise.name = replacements.get(
                    exercise.name,
                    exercise.name,
                )

                exercise.notes = (
                    exercise.notes or ""
                ) + (
                    " Adjusted for home/no-equipment "
                    "training."
                )

        # ----------------------------------------------------
        # GYM
        # ----------------------------------------------------

        elif wants_gym:

            for exercise in day.exercises:

                if exercise.name in {
                    "Bodyweight Squat",
                    "Squat",
                }:
                    exercise.name = "Goblet Squat"

                elif exercise.name in {
                    "Incline Push-up",
                    "Push-up",
                }:
                    exercise.name = (
                        "Dumbbell Chest Press"
                    )

                elif exercise.name == "Glute Bridge":
                    exercise.name = (
                        "Romanian Deadlift"
                    )

        # ----------------------------------------------------
        # MORE CARDIO
        # ----------------------------------------------------

        if wants_cardio:

            already_has_cardio = any(
                (
                    "cardio" in exercise.name.lower()
                    or "walk" in exercise.name.lower()
                    or "cycle" in exercise.name.lower()
                    or "running" in exercise.name.lower()
                    or "jog" in exercise.name.lower()
                )
                for exercise in day.exercises
            )

            if not already_has_cardio:

                day.exercises.append(
                    {
                        "name": "Brisk Walk / Cardio",
                        "sets": 1,
                        "reps_or_duration": (
                            "15-20 minutes"
                        ),
                        "rest": "As needed",
                        "notes": (
                            "Additional cardio added "
                            "from your feedback."
                        ),
                    }
                )

                day.focus = (
                    f"{day.focus} + Cardio"
                )

        # ----------------------------------------------------
        # MORE STRENGTH
        # ----------------------------------------------------

        if wants_strength:

            day.exercises.append(
                {
                    "name": "Strength Finisher",
                    "sets": 2,
                    "reps_or_duration": (
                        "8-12 reps"
                    ),
                    "rest": "60 sec",
                    "notes": (
                        "Additional strength work "
                        "added from your feedback."
                    ),
                }
            )

            day.focus = (
                f"{day.focus} + Strength"
            )

        # ----------------------------------------------------
        # SHORTER SESSIONS / LOW ENERGY
        # ----------------------------------------------------

        if wants_shorter or low_energy:

            for exercise in day.exercises:

                exercise.sets = max(
                    1,
                    min(exercise.sets, 2),
                )

                exercise.reps_or_duration = (
                    exercise.reps_or_duration
                    .replace(
                        "15-20 minutes",
                        "10-12 minutes",
                    )
                    .replace(
                        "20 minutes",
                        "12 minutes",
                    )
                    .replace(
                        "15 minutes",
                        "10 minutes",
                    )
                )

            day.recovery = (
                day.recovery or ""
            ) + (
                " Session load reduced "
                "based on your feedback."
            )

        # ----------------------------------------------------
        # LONGER SESSIONS
        # ----------------------------------------------------

        elif wants_longer:

            for exercise in day.exercises:

                exercise.sets = min(
                    4,
                    exercise.sets + 1,
                )

            day.recovery = (
                day.recovery or ""
            ) + (
                " Session volume increased "
                "based on your feedback."
            )

        # ----------------------------------------------------
        # TOO EASY
        # ----------------------------------------------------

        if too_easy:

            for exercise in day.exercises:

                exercise.sets = min(
                    4,
                    exercise.sets + 1,
                )

            day.recovery = (
                day.recovery or ""
            ) + (
                " Intensity increased because "
                "the previous plan felt too easy."
            )

        # ----------------------------------------------------
        # TOO HARD
        # ----------------------------------------------------

        elif too_hard:

            for exercise in day.exercises:

                exercise.sets = max(
                    1,
                    exercise.sets - 1,
                )

            day.recovery = (
                day.recovery or ""
            ) + (
                " Intensity reduced because "
                "the previous plan felt too difficult."
            )

        # ----------------------------------------------------
        # STRETCHING / MOBILITY
        # ----------------------------------------------------

        if wants_stretch:

            day.warm_up = (
                day.warm_up or ""
            ) + (
                " Add 5 minutes of "
                "mobility/stretching."
            )

            day.cooldown = (
                day.cooldown or ""
            ) + (
                " Add extra comfortable stretching."
            )

    # --------------------------------------------------------
    # Validate the final modified plan
    # --------------------------------------------------------

    return _add_food_habits(
        _validate(plan),
        profile,
    )


# ============================================================
# UPDATE WORKOUT PLAN USING FEEDBACK
# ============================================================

def update_workout_plan(
    profile: AssessmentInput,
    current,
    feedback: str,
):
    """
    Update an existing workout plan using user feedback.

    Gemini is used first.

    If Gemini is temporarily unavailable, the feedback-aware
    fallback function modifies the existing plan.
    """

    # --------------------------------------------------------
    # Clean feedback
    # --------------------------------------------------------

    feedback = (
        feedback or ""
    ).strip()

    if not feedback:

        raise AIResponseError(
            "Feedback cannot be empty."
        )

    # --------------------------------------------------------
    # Build Gemini feedback prompt
    # --------------------------------------------------------

    prompt = f"""
Revise this FitBuddy personalized workout plan using the
user profile, current plan, and the user's feedback.

PROFILE:

{_profile_text(profile)}

CURRENT PLAN:

{json.dumps(
    current,
    ensure_ascii=False,
    indent=2,
)}

USER FEEDBACK:

{feedback}

REQUIREMENTS:

1. Preserve the user's original fitness profile and safety constraints.

2. Incorporate the user's feedback into the workout plan.

3. Do not ignore the feedback.

4. Keep the plan personalized to the user's goal, age, weight,
   fitness level, intensity, equipment, and preferences.

5. Maintain exactly 7 days.

6. Each day must contain:
   - day number
   - focus
   - warm-up
   - exercises
   - cooldown
   - recovery guidance
   - rest-day information

7. Each exercise must contain:
   - name
   - sets
   - reps_or_duration
   - rest
   - notes

8. If the user requests more cardio, add appropriate cardio.

9. If the user requests more strength training, add appropriate
   strength exercises.

10. If the user requests more rest, add or convert an appropriate
    day into a recovery/rest day.

11. If the user requests shorter workouts, reduce the workout volume
    or duration.

12. If the user requests longer workouts, increase the workout volume
    carefully.

13. If the user requests home or no-equipment workouts, replace
    equipment-dependent exercises with suitable alternatives.

14. If the user requests stretching, flexibility, or mobility,
    include additional appropriate mobility/stretching work.

15. If the user says the previous plan was too easy, increase the
    intensity gradually.

16. If the user says the previous plan was too difficult, reduce
    the intensity appropriately.

17. Keep warm-up and cooldown guidance practical.

18. Do not remove the user's requested changes unless they conflict
    with safety constraints.

19. Return ONLY valid JSON.

20. Do not include Markdown fences.

21. Use this exact JSON structure:

{{
  "summary": "short summary of the updated plan",
  "weekly_strategy": "short weekly strategy",
  "days": [
    {{
      "day": 1,
      "focus": "workout focus",
      "is_rest_day": false,
      "warm_up": "warm-up instructions",
      "exercises": [
        {{
          "name": "exercise name",
          "sets": 3,
          "reps_or_duration": "10-12 reps",
          "rest": "60 seconds",
          "notes": "exercise guidance"
        }}
      ],
      "cooldown": "cooldown instructions",
      "recovery": "recovery guidance",
      "meals": []
    }}
  ],
  "nutrition_tip": "nutrition guidance",
  "hydration_tip": "hydration guidance",
  "sleep_tip": "sleep guidance"
}}

The response MUST contain exactly 7 day objects.
"""

    # --------------------------------------------------------
    # Try Gemini first
    # --------------------------------------------------------

    try:

        raw = _generate(prompt)

        # ----------------------------------------------------
        # Parse Gemini JSON response
        # ----------------------------------------------------

        try:

            if isinstance(raw, WorkoutPlanData):
                updated_plan = raw

            else:
                data = json.loads(raw)
                updated_plan = WorkoutPlanData.model_validate(
                    data
                )

        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:

            # Gemini can occasionally return Markdown fences.
            cleaned = str(raw).strip()

            if cleaned.startswith("```"):

                cleaned = cleaned.replace(
                    "```json",
                    "",
                    1,
                )

                cleaned = cleaned.replace(
                    "```JSON",
                    "",
                    1,
                )

                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]

                cleaned = cleaned.strip()

            try:

                data = json.loads(cleaned)

                updated_plan = (
                    WorkoutPlanData.model_validate(
                        data
                    )
                )

            except Exception as inner_exc:

                raise AIResponseError(
                    "Gemini returned invalid JSON."
                ) from inner_exc

        # ----------------------------------------------------
        # Validate Gemini's updated plan
        # ----------------------------------------------------

        updated_plan = _validate(
            updated_plan
        )

        # ----------------------------------------------------
        # Ensure food guidance exists
        # ----------------------------------------------------

        updated_plan = _add_food_habits(
            updated_plan,
            profile,
        )

        return updated_plan

    # --------------------------------------------------------
    # Gemini errors
    # --------------------------------------------------------

    except (
        AIConfigError,
        AIRequestError,
        AIResponseError,
    ) as exc:

        logger.warning(
            "Using feedback-aware fallback updated plan: %s",
            exc,
        )

        # IMPORTANT:
        #
        # Do NOT call _fallback() here.
        #
        # _fallback() creates a new plan and can ignore the
        # user's actual feedback.
        #
        # _feedback_fallback() modifies the CURRENT plan.

        return _feedback_fallback(
            profile,
            current,
            feedback,
        )