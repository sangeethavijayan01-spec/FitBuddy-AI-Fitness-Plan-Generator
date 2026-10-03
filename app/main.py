import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from . import config
from .config import BASE_DIR
from .database import init_db
from .errors import FitBuddyError
from .routes import pages,api
from .templating import render
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
@asynccontextmanager
async def lifespan(app):
    init_db()
    yield
app=FastAPI(title="FitBuddy – AI Fitness Plan Generator",version="2.0.0",description="Personalized fitness planning with Gemini.")
app.add_middleware(SessionMiddleware,secret_key=config.get_secret_key(),session_cookie="fitbuddy_session",max_age=60*60*24*7,same_site="lax")
app.mount("/static",StaticFiles(directory=str(BASE_DIR/"static")),name="static")
app.include_router(pages.router);app.include_router(api.router)
def json_path(request): return request.url.path.startswith("/api")
@app.exception_handler(FitBuddyError)
async def fit_error(request,exc):
    if json_path(request): return JSONResponse({"detail":exc.user_message},status_code=exc.status_code)
    return render(request,"error.html",{"status_code":exc.status_code,"title":"Something went wrong","message":exc.user_message},exc.status_code)
@app.exception_handler(StarletteHTTPException)
async def http_error(request,exc):
    if json_path(request): return JSONResponse({"detail":exc.detail},status_code=exc.status_code,headers=exc.headers)
    return render(request,"error.html",{"status_code":exc.status_code,"title":"Request error","message":str(exc.detail)},exc.status_code,exc.headers)
@app.exception_handler(RequestValidationError)
async def validation(request,exc):
    if json_path(request): return JSONResponse({"detail":[{"field":".".join(map(str,e["loc"])),"message":e["msg"]} for e in exc.errors()]},422)
    return render(request,"error.html",{"status_code":422,"title":"Invalid request","message":"Please check the information you entered."},422)
@app.exception_handler(Exception)
async def unexpected(request,exc):
    logging.getLogger("fitbuddy").exception("Unhandled error")
    if json_path(request): return JSONResponse({"detail":"An unexpected error occurred. Please try again."},500)
    return render(request,"error.html",{"status_code":500,"title":"Unexpected error","message":"An unexpected error occurred. Please try again."},500)
