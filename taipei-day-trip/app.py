from fastapi import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api import router

app=FastAPI()
app.include_router(router)

# **提供靜態檔案（CSS、JS、圖片）**
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request):
	return templates.TemplateResponse("attraction.html", {"request":request})
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
    return templates.TemplateResponse("booking.html", {"request": request})
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
    return templates.TemplateResponse("thankyou.html", {"request": request})