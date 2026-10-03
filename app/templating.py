from datetime import datetime
from fastapi import Request
from fastapi.templating import Jinja2Templates
from .config import BASE_DIR
from .schemas import DISCLAIMER
templates=Jinja2Templates(directory=str(BASE_DIR/"templates"))
def fmt_dt(v):
    return v.strftime("%d %b %Y, %H:%M") if isinstance(v,datetime) else "—"
templates.env.filters["fmt_dt"]=fmt_dt
templates.env.globals["disclaimer"]=DISCLAIMER
def render(request,name,context=None,status_code=200,headers=None):
    return templates.TemplateResponse(request,name,context or {},status_code=status_code,headers=headers)
