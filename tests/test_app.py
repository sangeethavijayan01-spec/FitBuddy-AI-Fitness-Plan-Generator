from sqlalchemy import select
from app.models import User,WorkoutPlan,WorkoutDayCompletion
from app.database import SessionLocal
def signup(c,u="asha",email="asha@example.com"):
    return c.post("/signup",data={"username":u,"email":email,"name":"Asha Kumar","password":"Password123!","confirm_password":"Password123!"},follow_redirects=False)
def login(c,u="asha"):
    return c.post("/login",data={"username":u,"password":"Password123!"},follow_redirects=False)
def onboard(c):
    return c.post("/onboarding",data={"name":"Asha Kumar","age":"21","height_cm":"165","weight_kg":"58","goal":"Weight Loss","experience":"Beginner","activity_level":"Light","intensity":"Medium","location":"Home","equipment":"Bodyweight","days_per_week":"4","duration_minutes":"40","preferred_time":"Morning","dietary_preference":"Vegetarian","allergies":"","sleep_hours":"7","rest_preference":"One full rest day","exercise_preferences":"Walking","limitations":""},follow_redirects=False)
def test_health(client):
    r=client.get("/api/health");assert r.status_code==200;assert r.json()["status"]=="ok"
def test_signup_login_logout(client):
    assert signup(client).status_code==303
    assert client.get("/dashboard").status_code==200
    assert client.post("/logout",follow_redirects=False).status_code==303
    assert client.get("/dashboard").status_code==401
    assert login(client).status_code==303
def test_duplicate_signup(client):
    signup(client);client.post("/logout",follow_redirects=False)
    assert signup(client).status_code==422
def test_onboarding_and_plan(client,mock_ai):
    signup(client);r=onboard(client);assert r.status_code==303
    r=client.post("/generate-plan",follow_redirects=False);assert r.status_code==303
    pid=r.headers["location"].split("/")[-1];page=client.get(r.headers["location"])
    assert page.status_code==200 and "DAY 7" in page.text
    with SessionLocal() as db: assert db.scalar(select(User)).profile.goal=="Weight Loss"
def test_feedback_preserves_original(client,mock_ai):
    signup(client);onboard(client);r=client.post("/generate-plan",follow_redirects=False);pid=r.headers["location"].split("/")[-1]
    r=client.post("/update-plan",data={"plan_id":pid,"feedback":"More cardio","difficulty":"Challenging","energy":"Normal","preferences":["More cardio"]},follow_redirects=False)
    assert r.status_code==303
    with SessionLocal() as db:
        p=db.get(WorkoutPlan,int(pid));assert p.original_plan and p.updated_plan and p.feedback=="More cardio";assert len(p.feedback_items)==1
def test_history_private(client,mock_ai):
    signup(client);onboard(client);r=client.post("/generate-plan",follow_redirects=False);pid=r.headers["location"].split("/")[-1];client.post("/logout",follow_redirects=False)
    signup(client,"ravi","ravi@example.com");onboard(client)
    assert client.get(f"/result/{pid}").status_code==404
def test_admin_protected_and_normal_login_detects_admin(client):
    assert client.get("/admin",follow_redirects=False).status_code==303
    assert client.get("/admin/login",follow_redirects=False).status_code==303
    r=client.post("/login",data={"username":"admin","password":"adminpass"},follow_redirects=False)
    assert r.status_code==303 and r.headers["location"]=="/admin"
    assert client.get("/admin").status_code==200
    assert client.get("/nutrition").status_code==200
def test_invalid_login(client):
    signup(client);client.post("/logout",follow_redirects=False);assert client.post("/login",data={"username":"asha","password":"wrong"}).status_code==401
def test_api_signup_and_login(client):
    r=client.post("/api/auth/signup",json={"username":"apiuser","email":"api@example.com","name":"API User","password":"Password123!"});assert r.status_code==201
    r=client.post("/api/auth/login",json={"username":"apiuser","password":"Password123!"});assert r.status_code==200
def test_progress(client):
    signup(client);onboard(client)
    r=client.post("/progress",data={"weight_kg":"57.5","workout_completion":"80","energy":"High","difficulty":"Moderate","notes":"Good week"},follow_redirects=False)
    assert r.status_code==303
    assert "57.5" in client.get("/progress").text
def test_api_ownership(client,mock_ai):
    signup(client);onboard(client);r=client.post("/generate-plan",follow_redirects=False);pid=r.headers["location"].split("/")[-1];client.post("/logout",follow_redirects=False)
    signup(client,"other","other@example.com");assert client.get(f"/api/plans/{pid}").status_code==404


def test_authenticated_page_routes(client):
    signup(client)
    assert client.get("/dashboard").status_code == 200
    assert client.get("/profile").status_code == 200
    assert client.get("/progress").status_code == 200
    assert client.get("/history").status_code == 200
    assert client.get("/onboarding").status_code == 200


def test_fallback_is_personalized(monkeypatch):
    from app import ai_service
    from app.schemas import AssessmentInput
    monkeypatch.setattr(ai_service, "_generate", lambda prompt: (_ for _ in ()).throw(ai_service.AIRequestError("temporary 503")))
    a = AssessmentInput(name="Asha Kumar", age=21, height_cm=165, weight_kg=58, goal="Weight Loss", experience="Beginner", activity_level="Light", intensity="Medium", location="Home", equipment="Bodyweight", days_per_week=4, duration_minutes=40, preferred_time="Morning", dietary_preference="Vegetarian", sleep_hours=7, rest_preference="One full rest day", exercise_preferences="Walking", limitations="")
    b = AssessmentInput(name="Ravi Kumar", age=30, height_cm=180, weight_kg=82, goal="Muscle Gain", experience="Advanced", activity_level="High", intensity="High", location="Gym", equipment="Dumbbells and machines", days_per_week=6, duration_minutes=60, preferred_time="Evening", dietary_preference="Non-vegetarian", sleep_hours=8, rest_preference="One rest day", exercise_preferences="Strength", limitations="")
    pa = ai_service.generate_workout_plan(a)
    pb = ai_service.generate_workout_plan(b)
    assert pa.summary != pb.summary
    assert pa.days != pb.days
    assert "Weight Loss" in pa.summary
    assert "Muscle Gain" in pb.summary


def test_normal_user_cannot_see_admin_navigation(client):
    signup(client)
    assert "Admin" not in client.get("/profile").text
    assert "Admin" not in client.get("/progress").text

def test_admin_can_use_food_guide_and_admin_only_navigation(client):
    r=client.post("/login",data={"username":"admin","password":"adminpass"},follow_redirects=False)
    assert r.status_code==303 and r.headers["location"]=="/admin"
    admin_page=client.get("/admin"); assert admin_page.status_code==200 and 'class="active" href="/admin"' in admin_page.text
    food=client.get("/nutrition"); assert food.status_code==200 and "Drinks" in food.text and "Coconut water" in food.text

def test_food_guide_requires_authentication(client):
    assert client.get("/nutrition").status_code==401

def test_public_auth_pages_hide_food_and_admin_links(client):
    assert "Food guide" not in client.get("/login").text
    assert "Food guide" not in client.get("/signup").text
    assert "Coach / Admin login" not in client.get("/login").text
    assert "Food guide" not in client.get("/signup").text

def test_day_checklist_auto_progress(client,mock_ai):
    signup(client); onboard(client); r=client.post("/generate-plan",follow_redirects=False); pid=int(r.headers["location"].split("/")[-1])
    page=client.get(r.headers["location"]); assert "Mark each day complete" in page.text and "Day 7" in page.text
    r=client.post(f"/plan/{pid}/day/1/toggle",data={"completed":"true"}); assert r.status_code==200; assert r.json()["percent"]==14
    r=client.post(f"/plan/{pid}/day/2/toggle",data={"completed":"true"}); assert r.json()["completed_count"]==2
    with SessionLocal() as db: assert db.query(WorkoutDayCompletion).count()==2
    assert "29%" in client.get(f"/result/{pid}").text

def test_day_completion_private(client,mock_ai):
    signup(client); onboard(client); r=client.post("/generate-plan",follow_redirects=False); pid=int(r.headers["location"].split("/")[-1]); client.post("/logout",follow_redirects=False)
    signup(client,"other","other@example.com"); assert client.post(f"/plan/{pid}/day/1/toggle",data={"completed":"true"}).status_code==404

def test_food_guide(client):
    signup(client)
    r=client.get("/nutrition"); assert r.status_code==200; assert "Banana" in r.text and "Chicken breast" in r.text and "Coconut water" in r.text and "fibre" in r.text

def test_progress_admin_monitoring(client):
    signup(client); onboard(client); client.post("/progress",data={"weight_kg":"57.5","workout_completion":"80","energy":"High","difficulty":"Moderate","notes":"Good week"})
    client.post("/logout",follow_redirects=False); client.post("/admin/login",data={"username":"admin","password":"adminpass"},follow_redirects=False)
    page=client.get("/admin"); assert page.status_code==200; assert "57.5" in page.text and "80%" in page.text and "Total users" in page.text

def test_fallback_has_food_habits(monkeypatch):
    from app import ai_service
    from app.schemas import AssessmentInput
    monkeypatch.setattr(ai_service, "_generate", lambda prompt: (_ for _ in ()).throw(ai_service.AIRequestError("temporary 503")))
    a=AssessmentInput(name="Asha Kumar",age=21,height_cm=165,weight_kg=58,goal="Weight Loss",experience="Beginner",activity_level="Light",intensity="Medium",location="Home",equipment="Bodyweight",days_per_week=4,duration_minutes=40,preferred_time="Morning",dietary_preference="Vegetarian",sleep_hours=7,rest_preference="One full rest day",exercise_preferences="Walking",limitations="")
    plan=ai_service.generate_workout_plan(a); assert len(plan.days)==7 and all(len(d.meals)==4 for d in plan.days); assert plan.days[0].meals[0].calories > 0
