from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from .. import services, config
from ..models import User, WorkoutPlan
from ..schemas import UserSignup,LoginInput,AssessmentInput,FeedbackInput,ProgressInput
from ..security import hash_password,verify_password,login_user,logout_user,require_user,require_admin_user,current_user

router=APIRouter(prefix="/api",tags=["api"])
@router.get("/health")
def health():
    return {"status":"ok","gemini_api_key_configured":config.api_key_is_configured(),"gemini_model":config.get_gemini_model()}
@router.post("/auth/signup",status_code=201)
def signup(data:UserSignup,db:Session=Depends(get_db)):
    if db.query(User).filter((User.username==data.username)|(User.email==data.email)).first(): raise HTTPException(409,"Username or email already exists.")
    u=User(username=data.username,email=data.email,password_hash=hash_password(data.password),name=data.name)
    db.add(u);db.commit();db.refresh(u); return {"id":u.id,"username":u.username,"message":"Account created. Please log in."}
@router.post("/auth/login")
def login(data:LoginInput,request:Request,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.username==data.username).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Invalid username or password.")
    login_user(request,u); return {"message":"Logged in","username":u.username,"is_admin":u.is_admin}
@router.post("/auth/logout")
def logout(request): logout_user(request); return {"message":"Logged out"}
@router.get("/me")
def me(user=Depends(require_user)):
    return {"id":user.id,"username":user.username,"email":user.email,"name":user.name,"is_admin":user.is_admin}
@router.post("/assessment")
def assessment(data:AssessmentInput,user=Depends(require_user),db:Session=Depends(get_db)):
    return {"message":"Assessment saved","user_id":services.save_assessment(db,user,data).id}
@router.post("/plans",status_code=201)
def create_plan(user=Depends(require_user),db:Session=Depends(get_db)):
    return services.plan_api(services.generate(db,user))
@router.get("/plans/{plan_id}")
def read_plan(plan_id:int,user=Depends(require_user),db:Session=Depends(get_db)):
    return services.plan_api(services.owned_plan(db,user,plan_id))
@router.post("/plans/{plan_id}/feedback")
def feedback(plan_id:int,data:FeedbackInput,user=Depends(require_user),db:Session=Depends(get_db)):
    return services.plan_api(services.update(db,user,services.owned_plan(db,user,plan_id),data))
@router.get("/history")
def history(user=Depends(require_user),db:Session=Depends(get_db)):
    return [services.plan_api(p) for p in db.query(WorkoutPlan).filter(WorkoutPlan.user_id==user.id).all()]
@router.post("/progress")
def progress(data:ProgressInput,user=Depends(require_user),db:Session=Depends(get_db)):
    r=services.add_progress(db,user,data);return {"id":r.id,"recorded_at":r.recorded_at.isoformat()}
@router.get("/progress")
def get_progress(user=Depends(require_user),db:Session=Depends(get_db)):
    return [{"id":r.id,"weight_kg":r.weight_kg,"workout_completion":r.workout_completion,"energy":r.energy,"difficulty":r.difficulty,"notes":r.notes,"recorded_at":r.recorded_at.isoformat()} for r in user.progress]
@router.get("/admin/users")
def admin_users(user=Depends(require_admin_user),db:Session=Depends(get_db)):
    users=db.query(User).all()
    return [{"id":u.id,"username":u.username,"email":u.email,"name":u.name,"created_at":u.created_at.isoformat(),"plans":len(u.plans)} for u in users]
