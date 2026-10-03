"""Authentication and authorization helpers for user and admin sessions."""
import base64, hashlib, hmac, os, secrets
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .config import get_admin_password, get_admin_username
from .database import get_db
from .models import User

def hash_password(password:str)->str:
    salt=os.urandom(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1)
    return "scrypt$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()

def verify_password(password:str, encoded:str)->bool:
    try:
        _,s,d=encoded.split("$",2)
        salt=base64.urlsafe_b64decode(s.encode()); expected=base64.urlsafe_b64decode(d.encode())
        actual=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1)
        return hmac.compare_digest(actual,expected)
    except Exception:
        return False

def login_user(request:Request,user:User):
    request.session.pop("admin_authenticated", None)
    request.session.pop("admin_username", None)
    request.session["user_id"]=user.id
    request.session["is_admin"]=bool(user.is_admin)

def logout_user(request:Request):
    request.session.clear()

def current_user(request:Request,db:Session=Depends(get_db)):
    uid=request.session.get("user_id")
    if not uid: return None
    return db.get(User,int(uid))

def require_user(user=Depends(current_user)):
    if not user: raise HTTPException(401,"Please log in to continue.")
    return user

def require_admin_user(request:Request,user=Depends(current_user)):
    if admin_authenticated(request):
        return user or True
    if user and user.is_admin:
        return user
    raise HTTPException(403,"Admin access is required.")

def admin_env_login(username,password):
    configured=get_admin_password()
    return bool(configured) and secrets.compare_digest(username,get_admin_username()) and secrets.compare_digest(password,configured)

def login_admin(request:Request, username:str, password:str)->bool:
    if not admin_env_login(username,password):
        return False
    request.session.pop("user_id", None)
    request.session.pop("is_admin", None)
    request.session["admin_authenticated"] = True
    request.session["admin_username"] = username
    return True

def admin_authenticated(request:Request)->bool:
    return bool(request.session.get("admin_authenticated"))

def require_admin_session(request:Request):
    if not admin_authenticated(request):
        raise HTTPException(401,"Admin login is required.")
    return True

from fastapi.security import HTTPBasic, HTTPBasicCredentials
basic=HTTPBasic(auto_error=False)
def require_admin_basic(credentials:HTTPBasicCredentials|None=Depends(basic)):
    if not credentials or not admin_env_login(credentials.username,credentials.password):
        raise HTTPException(401,"Admin credentials are required.",headers={"WWW-Authenticate":"Basic"})
