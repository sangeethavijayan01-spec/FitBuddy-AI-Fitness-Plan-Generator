import os,tempfile
from pathlib import Path
td=tempfile.mkdtemp()
os.environ["DATABASE_URL"]=f"sqlite:///{(Path(td) / 'test.db').as_posix()}"
os.environ["GEMINI_API_KEY"]="test-key";os.environ["GEMINI_MODEL"]="test-model";os.environ["SECRET_KEY"]="test-secret";os.environ["ADMIN_PASSWORD"]="adminpass";os.environ["ADMIN_USERNAME"]="admin"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base,engine,SessionLocal
from app import ai_service
from app.schemas import WorkoutPlanData
@pytest.fixture(autouse=True)
def db():
    Base.metadata.drop_all(bind=engine);Base.metadata.create_all(bind=engine);yield
@pytest.fixture
def client():
    with TestClient(app) as c: yield c
def plan():
    return WorkoutPlanData.model_validate({"summary":"Test plan","weekly_strategy":"Build gradually","days":[{"day":i,"focus":"Rest" if i==7 else f"Focus {i}","is_rest_day":i==7,"warm_up":"5 min","exercises":[] if i==7 else [{"name":"Squat","sets":3,"reps_or_duration":"10 reps","rest":"60 sec","notes":"Control"}],"cooldown":"5 min","recovery":"Hydrate"} for i in range(1,8)],"nutrition_tip":"Balanced meals","hydration_tip":"Drink water","sleep_tip":"Sleep well"})
@pytest.fixture
def mock_ai(monkeypatch):
    monkeypatch.setattr(ai_service,"generate_workout_plan",lambda p:plan())
    monkeypatch.setattr(ai_service,"update_workout_plan",lambda p,c,f:plan())
