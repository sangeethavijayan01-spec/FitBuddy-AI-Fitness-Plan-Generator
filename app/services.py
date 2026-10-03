"""Business logic and ownership-safe database operations."""
import json, logging
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from . import ai_service
from .errors import DatabaseOperationError, PlanNotFoundError
from .models import User,Profile,FitnessAssessment,WorkoutPlan,PlanFeedback,ProgressRecord,WorkoutDayCompletion,utcnow
from .schemas import AssessmentInput,FeedbackInput,ProgressInput
logger=logging.getLogger("fitbuddy.services")

def dump(x): return json.dumps(x.model_dump(mode="json"),ensure_ascii=False)
def load(raw):
    try:return json.loads(raw)
    except Exception as e: raise DatabaseOperationError("Saved plan data could not be read.") from e

def profile_input(user):
    p=user.profile; a=user.assessment
    if not p or not a: raise DatabaseOperationError("Complete your fitness assessment first.")
    return AssessmentInput(name=user.name,age=p.age or 30,height_cm=p.height_cm or 170,weight_kg=p.weight_kg or 60,goal=p.goal,experience=a.experience,activity_level=a.activity_level,intensity=p.intensity,location=p.location,equipment=p.equipment or "Bodyweight",days_per_week=p.days_per_week or 3,duration_minutes=p.duration_minutes or 30,preferred_time=a.preferred_time or "Flexible",dietary_preference=p.dietary_preference,allergies=p.allergies or "",sleep_hours=p.sleep_hours or 7,rest_preference=p.rest_preference or "Flexible",exercise_preferences=p.exercise_preferences or "",limitations=p.limitations or "")

def save_assessment(db,user,data):
    user.name=data.name
    p=user.profile or Profile(user_id=user.id); user.profile=p
    for k in ["age","height_cm","weight_kg","goal","activity_level","intensity","location","equipment","days_per_week","duration_minutes","dietary_preference","allergies","sleep_hours","rest_preference","exercise_preferences","limitations"]:
        value=getattr(data,k); setattr(p,k,value.value if hasattr(value,"value") else value)
    a=user.assessment or FitnessAssessment(user_id=user.id); user.assessment=a
    a.experience=data.experience.value; a.activity_level=data.activity_level.value; a.preferred_time=data.preferred_time
    a.recovery_preference=data.rest_preference; a.exercise_preferences=data.exercise_preferences; a.limitations=data.limitations
    db.add_all([p,a]); db.commit(); db.refresh(user); return user

def owned_plan(db,user,plan_id):
    plan=db.scalar(select(WorkoutPlan).options(joinedload(WorkoutPlan.user)).where(WorkoutPlan.id==plan_id,WorkoutPlan.user_id==user.id))
    if not plan: raise PlanNotFoundError("That workout plan was not found in your account.")
    return plan

def generate(db,user):
    data=profile_input(user); plan_data=ai_service.generate_workout_plan(data)
    plan=WorkoutPlan(user_id=user.id,goal=data.goal.value,intensity=data.intensity.value,original_plan=dump(plan_data))
    db.add(plan); db.commit(); db.refresh(plan); return plan

def update(db,user,plan,feedback):
    data=profile_input(user); current=load(plan.updated_plan or plan.original_plan)
    new=ai_service.update_workout_plan(data,current,feedback.feedback)
    plan.updated_plan=dump(new); plan.feedback=feedback.feedback; plan.updated_at=utcnow()
    db.add(PlanFeedback(plan_id=plan.id,feedback=feedback.feedback,difficulty=feedback.difficulty,energy=feedback.energy,preferences=json.dumps(feedback.preferences)))
    db.commit(); db.refresh(plan); return plan

def add_progress(db,user,data):
    rec=ProgressRecord(user_id=user.id,**data.model_dump()); db.add(rec); db.commit(); db.refresh(rec); return rec

def progress_summary(user):
    rows=sorted(list(user.progress or []), key=lambda x:x.recorded_at)
    weights=[r.weight_kg for r in rows if r.weight_kg is not None]
    completions=[r.workout_completion for r in rows if r.workout_completion is not None]
    return {
        "records": len(rows),
        "latest": rows[-1] if rows else None,
        "first_weight": weights[0] if weights else None,
        "latest_weight": weights[-1] if weights else None,
        "weight_change": (weights[-1]-weights[0]) if len(weights)>=2 else None,
        "avg_completion": round(sum(completions)/len(completions),1) if completions else None,
        "completion_count": len(completions),
    }

def admin_snapshot(db):
    users=db.scalars(select(User).order_by(User.created_at.desc())).all()
    plans=db.scalars(select(WorkoutPlan).options(joinedload(WorkoutPlan.user)).order_by(WorkoutPlan.created_at.desc())).all()
    feedback_count=db.scalar(select(func.count(PlanFeedback.id))) or 0
    progress_count=db.scalar(select(func.count(ProgressRecord.id))) or 0
    rows=[]
    for u in users:
        rows.append({"user":u,"summary":progress_summary(u),"plans_count":len(u.plans),"feedback_count":sum(len(p.feedback_items) for p in u.plans),"latest_plan":(u.plans[0] if u.plans else None)})
    return {"users":users,"plans":plans,"rows":rows,"completion_by_plan":{p.id:completion_summary(p) for p in plans},"stats":{"users":len(users),"plans":len(plans),"updated_plans":sum(1 for p in plans if p.is_updated),"feedback":feedback_count,"progress_records":progress_count}}



def completion_summary(plan):
    completed = {row.day for row in (plan.completions or []) if row.completed}
    return {"completed_days": sorted(completed), "completed_count": len(completed), "total_days": 7, "percent": round(len(completed) / 7 * 100)}

def set_day_completion(db, user, plan, day, completed):
    if day < 1 or day > 7:
        raise ValueError("Day must be between 1 and 7.")
    row = next((x for x in plan.completions if x.day == day), None)
    if row is None:
        row = WorkoutDayCompletion(plan_id=plan.id, day=day)
        db.add(row)
    row.completed = bool(completed)
    row.completed_at = utcnow() if completed else None
    db.commit(); db.refresh(plan)
    return completion_summary(plan)

def plan_api(plan):
    return {"id":plan.id,"goal":plan.goal,"intensity":plan.intensity,"created_at":plan.created_at.isoformat(),"updated_at":plan.updated_at.isoformat() if plan.updated_at else None,"feedback":plan.feedback,"original_plan":load(plan.original_plan),"updated_plan":load(plan.updated_plan) if plan.updated_plan else None,"completion":completion_summary(plan)}
