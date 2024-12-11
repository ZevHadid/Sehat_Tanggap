from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates

from routes import dashboard, chatbot, login, logout, medicine_management, patients, pmr_schedules, profile
from exceptions import unauthorized_exception_handler

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.include_router(dashboard.router)
app.include_router(chatbot.router)
app.include_router(medicine_management.router)
app.include_router(patients.router)
app.include_router(pmr_schedules.router)
app.include_router(profile.router)

app.include_router(login.router)
app.include_router(logout.router)

app.add_exception_handler(HTTPException, unauthorized_exception_handler)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
