import logging
from fastapi import APIRouter,Depends,Form,Request,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from .. import services, config
from ..errors import FitBuddyError
from ..models import User,WorkoutPlan
from ..schemas import UserSignup,LoginInput,AssessmentInput,FeedbackInput,ProgressInput,Goal,Intensity,Experience,Activity,Location,Diet,friendly_errors
from ..security import current_user,require_user,hash_password,verify_password,login_user,logout_user,login_admin,admin_authenticated,admin_env_login
from ..templating import render
router=APIRouter()
GOALS=[g.value for g in Goal]; INTENSITIES=[g.value for g in Intensity]; EXPERIENCES=[g.value for g in Experience]; ACTIVITIES=[g.value for g in Activity]; LOCATIONS=[g.value for g in Location]; DIETS=[g.value for g in Diet]

def ctx(user=None, **kw):
    return {"user":user,"goals":GOALS,"intensities":INTENSITIES,"experiences":EXPERIENCES,"activities":ACTIVITIES,"locations":LOCATIONS,"diets":DIETS,"admin_authenticated":False,"errors":{},"values":{},**kw}

@router.get("/",response_class=HTMLResponse)
def home(request:Request,user=Depends(current_user)):
    return render(request,"landing.html",ctx(user,admin_authenticated=admin_authenticated(request),active_path=request.url.path))

@router.get("/signup",response_class=HTMLResponse)
def signup_page(request:Request): return render(request,"signup.html",ctx(active_path=request.url.path))
@router.post("/signup",response_class=HTMLResponse)
def signup(request:Request,username:str=Form(""),email:str=Form(""),name:str=Form(""),password:str=Form(""),confirm_password:str=Form(""),db:Session=Depends(get_db)):
    try:
        if password!=confirm_password: raise ValueError("Passwords do not match.")
        data=UserSignup(username=username,email=email,name=name,password=password)
        if db.query(User).filter((User.username==data.username)|(User.email==data.email)).first(): raise ValueError("Username or email already exists.")
        u=User(username=data.username,email=data.email,name=data.name,password_hash=hash_password(data.password));db.add(u);db.commit();db.refresh(u)
        login_user(request,u);return RedirectResponse("/onboarding",303)
    except (ValidationError,ValueError) as e:
        errors=friendly_errors(e) if isinstance(e,ValidationError) else {"form":str(e)}
        return render(request,"signup.html",ctx(errors=errors,values={"username":username,"email":email,"name":name},active_path=request.url.path),422)

@router.get("/login",response_class=HTMLResponse)
def login_page(request:Request): return render(request,"login.html",ctx(active_path=request.url.path))
@router.post("/login")
def login(request:Request,username:str=Form(""),password:str=Form(""),db:Session=Depends(get_db)):
    # The normal login form is also the single entry point for the configured admin account.
    if admin_env_login(username, password):
        login_admin(request, username, password)
        return RedirectResponse("/admin", 303)
    u=db.query(User).filter(User.username==username).first()
    if u and verify_password(password,u.password_hash):
        login_user(request,u)
        return RedirectResponse("/dashboard",303)
    return render(request,"login.html",ctx(error="Invalid username or password.",values={"username":username},active_path=request.url.path),401)
@router.post("/logout")
def logout(request:Request): logout_user(request);return RedirectResponse("/",303)

@router.get("/admin/login",response_class=HTMLResponse)
def admin_login_page(request:Request):
    # Kept as a compatibility route; admin authentication happens through /login.
    return RedirectResponse("/login",303)

@router.post("/admin/login")
def admin_login_compat(request:Request,username:str=Form(""),password:str=Form("")):
    if login_admin(request,username,password): return RedirectResponse("/admin",303)
    return RedirectResponse("/login?admin=1",303)

@router.get("/onboarding",response_class=HTMLResponse)
def onboarding(request:Request,user=Depends(require_user)): return render(request,"onboarding.html",ctx(user,admin_authenticated=admin_authenticated(request),active_path=request.url.path,values={}))
@router.post("/onboarding",response_class=HTMLResponse)
def save_onboarding(request:Request,user=Depends(require_user),db:Session=Depends(get_db),name:str=Form(""),age:str=Form(""),height_cm:str=Form(""),weight_kg:str=Form(""),goal:str=Form(""),experience:str=Form(""),activity_level:str=Form(""),intensity:str=Form(""),location:str=Form(""),equipment:str=Form(""),days_per_week:str=Form(""),duration_minutes:str=Form(""),preferred_time:str=Form(""),dietary_preference:str=Form(""),allergies:str=Form(""),sleep_hours:str=Form(""),rest_preference:str=Form(""),exercise_preferences:str=Form(""),limitations:str=Form("")):
    raw=locals(); [raw.pop(k,None) for k in ("request","user","db")]
    try:
        data=AssessmentInput(**raw);services.save_assessment(db,user,data);return RedirectResponse("/dashboard",303)
    except ValidationError as e:
        return render(request,"onboarding.html",ctx(user,errors=friendly_errors(e),values=raw,active_path=request.url.path),422)

@router.get("/dashboard",response_class=HTMLResponse)
def dashboard(request:Request,user=Depends(require_user),db:Session=Depends(get_db)):
    plans=db.scalars(select(WorkoutPlan).where(WorkoutPlan.user_id==user.id).order_by(WorkoutPlan.created_at.desc()).limit(5)).all()
    return render(request,"dashboard.html",ctx(user,plans=plans,progress=services.progress_summary(user),admin_authenticated=admin_authenticated(request),active_path=request.url.path))
@router.post("/generate-plan")
def generate_plan(user=Depends(require_user),db:Session=Depends(get_db)): return RedirectResponse(f"/result/{services.generate(db,user).id}",303)
@router.get("/result/{plan_id}",response_class=HTMLResponse)
def result(request:Request,plan_id:int,user=Depends(require_user),db:Session=Depends(get_db),updated:int=0):
    p=services.owned_plan(db,user,plan_id);return render(request,"result.html",ctx(user,plan=p,data=services.load(p.updated_plan or p.original_plan),original=services.load(p.original_plan) if p.updated_plan else None,updated=bool(updated),completion=services.completion_summary(p),admin_authenticated=admin_authenticated(request),active_path=request.url.path))
@router.get("/feedback/{plan_id}",response_class=HTMLResponse)
def feedback_page(request:Request,plan_id:int,user=Depends(require_user),db:Session=Depends(get_db)):
    p=services.owned_plan(db,user,plan_id);return render(request,"feedback.html",ctx(user,plan=p,admin_authenticated=admin_authenticated(request),active_path=request.url.path))
@router.post("/update-plan")
def update_plan(request:Request,plan_id:int=Form(...),feedback:str=Form(""),difficulty:str=Form(""),energy:str=Form(""),preferences:list[str]=Form(default=[]),user=Depends(require_user),db:Session=Depends(get_db)):
    p=services.owned_plan(db,user,plan_id)
    try: data=FeedbackInput(feedback=feedback,difficulty=difficulty or None,energy=energy or None,preferences=preferences)
    except ValidationError as e:return render(request,"feedback.html",ctx(user,plan=p,errors=friendly_errors(e),values={"feedback":feedback}),422)
    services.update(db,user,p,data);return RedirectResponse(f"/result/{p.id}?updated=1",303)

@router.post("/plan/{plan_id}/day/{day}/toggle")
def toggle_day(plan_id:int,day:int,completed:bool=Form(...),user=Depends(require_user),db:Session=Depends(get_db)):
    plan=services.owned_plan(db,user,plan_id)
    return services.set_day_completion(db,user,plan,day,completed)

@router.get("/history",response_class=HTMLResponse)
def history(request:Request,user=Depends(require_user),db:Session=Depends(get_db)):
    plans=db.scalars(select(WorkoutPlan).where(WorkoutPlan.user_id==user.id).order_by(WorkoutPlan.created_at.desc())).all();return render(request,"history.html",ctx(user,plans=plans,admin_authenticated=admin_authenticated(request),active_path=request.url.path))
@router.get("/profile",response_class=HTMLResponse)
def profile(request:Request,user=Depends(require_user)): return render(request,"profile.html",ctx(user,progress=services.progress_summary(user),admin_authenticated=admin_authenticated(request),active_path=request.url.path))
@router.get("/progress",response_class=HTMLResponse)
def progress_page(request:Request,user=Depends(require_user)): return render(request,"progress.html",ctx(user,progress=services.progress_summary(user),admin_authenticated=admin_authenticated(request),active_path=request.url.path))
@router.post("/progress")
def add_progress(weight_kg:str=Form(""),workout_completion:str=Form(""),energy:str=Form(""),difficulty:str=Form(""),notes:str=Form(""),user=Depends(require_user),db:Session=Depends(get_db)):
    d=ProgressInput(weight_kg=float(weight_kg) if weight_kg else None,workout_completion=int(workout_completion) if workout_completion else None,energy=energy or None,difficulty=difficulty or None,notes=notes)
    services.add_progress(db,user,d);return RedirectResponse("/progress",303)

@router.get("/nutrition",response_class=HTMLResponse)
def nutrition_page(request:Request,user=Depends(current_user)):
    if not user and not admin_authenticated(request):
        raise HTTPException(401,"Please log in to view the food guide.")
    return render(request,"nutrition.html",ctx(user,admin_authenticated=admin_authenticated(request),active_path=request.url.path))

@router.get("/admin",response_class=HTMLResponse)
def admin(request:Request,db:Session=Depends(get_db)):
    if not admin_authenticated(request):
        return RedirectResponse("/login",303)
    snap=services.admin_snapshot(db)
    return render(request,"admin.html",ctx(None,admin_authenticated=True,admin_username=request.session.get("admin_username","admin"),active_path=request.url.path,**snap))
