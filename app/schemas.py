"""Pydantic validation models and structured Gemini output schemas."""
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError
MIN_AGE,MAX_AGE=14,90
MIN_WEIGHT,MAX_WEIGHT=20,300
DISCLAIMER="FitBuddy provides general fitness and wellness guidance and is not a substitute for professional medical advice."

class Goal(str,Enum):
    WEIGHT_LOSS="Weight Loss"; MUSCLE_GAIN="Muscle Gain"; GENERAL_FITNESS="General Fitness"; STRENGTH="Strength"; ENDURANCE="Endurance"; FLEXIBILITY="Flexibility"; MAINTENANCE="Maintenance"
class Intensity(str,Enum): LOW="Low"; MEDIUM="Medium"; HIGH="High"
class Experience(str,Enum): BEGINNER="Beginner"; INTERMEDIATE="Intermediate"; ADVANCED="Advanced"
class Activity(str,Enum): SEDENTARY="Sedentary"; LIGHT="Light"; MODERATE="Moderate"; HIGH="High"
class Location(str,Enum): HOME="Home"; GYM="Gym"; OUTDOOR="Outdoor"
class Diet(str,Enum): VEGETARIAN="Vegetarian"; NON_VEGETARIAN="Non-vegetarian"; VEGAN="Vegan"; OTHER="Other"
class UserSignup(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    username:str=Field(min_length=3,max_length=40,pattern=r"^[A-Za-z0-9_.-]+$")
    email:str=Field(min_length=5,max_length=120)
    password:str=Field(min_length=8,max_length=128)
    name:str=Field(min_length=2,max_length=60)
    @field_validator("email")
    @classmethod
    def email_ok(cls,v):
        if "@" not in v or "." not in v.rsplit("@",1)[-1]: raise ValueError("Enter a valid email address.")
        return v.lower()
class LoginInput(BaseModel): username:str; password:str
class AssessmentInput(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True)
    name:str=Field(min_length=2,max_length=60); age:int=Field(ge=MIN_AGE,le=MAX_AGE); height_cm:float=Field(ge=100,le=250); weight_kg:float=Field(ge=MIN_WEIGHT,le=MAX_WEIGHT)
    goal:Goal; experience:Experience; activity_level:Activity; intensity:Intensity; location:Location; equipment:str=Field(min_length=1,max_length=500)
    days_per_week:int=Field(ge=1,le=7); duration_minutes:int=Field(ge=15,le=180); preferred_time:str=Field(min_length=2,max_length=30)
    dietary_preference:Diet; allergies:str=Field(default="",max_length=500); sleep_hours:float=Field(ge=0,le=24); rest_preference:str=Field(min_length=2,max_length=100)
    exercise_preferences:str=Field(default="",max_length=500); limitations:str=Field(default="",max_length=500)
    @field_validator("name")
    @classmethod
    def name_ok(cls,v):
        if not any(c.isalpha() for c in v): raise ValueError("Name must contain letters.")
        return v
class FeedbackInput(BaseModel):
    feedback:str=Field(min_length=3,max_length=500); difficulty:str|None=None; energy:str|None=None; preferences:list[str]=Field(default_factory=list)
class ProgressInput(BaseModel):
    weight_kg:float|None=Field(default=None,ge=20,le=300); workout_completion:int|None=Field(default=None,ge=0,le=100)
    energy:str|None=None; difficulty:str|None=None; notes:str=Field(default="",max_length=500)

class Exercise(BaseModel):
    name:str; sets:int=Field(ge=1,le=10); reps_or_duration:str; rest:str="30-90 sec"; notes:str=""
class MealSuggestion(BaseModel):
    meal:str; food:str; portion:str; calories:int=Field(ge=0,le=2000); protein_g:float=Field(ge=0,le=150); fiber_g:float=Field(ge=0,le=50)
class DayPlan(BaseModel):
    day:int=Field(ge=1,le=7); focus:str; is_rest_day:bool; warm_up:str; exercises:list[Exercise]; cooldown:str; recovery:str
    meals:list[MealSuggestion]=Field(default_factory=list)
class WorkoutPlanData(BaseModel):
    summary:str; weekly_strategy:str=""; days:list[DayPlan]; nutrition_tip:str; hydration_tip:str=""; sleep_tip:str=""

def friendly_errors(exc:ValidationError):
    out={}
    for e in exc.errors():
        f=str((e.get("loc") or ["form"])[0]); t=e.get("type","")
        if t=="missing": msg=f"{f.replace('_',' ').capitalize()} is required."
        elif t in ("int_parsing","int_type"): msg=f"{f.replace('_',' ').capitalize()} must be a whole number."
        elif t in ("float_parsing","float_type"): msg=f"{f.replace('_',' ').capitalize()} must be a valid number."
        elif t=="greater_than_equal": msg=f"{f.replace('_',' ').capitalize()} is below the allowed minimum."
        elif t=="less_than_equal": msg=f"{f.replace('_',' ').capitalize()} is above the allowed maximum."
        elif t=="string_too_short": msg=f"{f.replace('_',' ').capitalize()} is too short."
        elif t=="string_too_long": msg=f"{f.replace('_',' ').capitalize()} is too long."
        elif t in ("enum","literal_error"): msg=f"Please choose a valid {f.replace('_',' ')}."
        else: msg=e.get("msg","Invalid value.")
        out.setdefault(f,msg)
    return out
